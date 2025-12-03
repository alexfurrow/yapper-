"""
Conversation management routes for Yap chat functionality.
Handles all OpenAI calls, message formatting, and business logic.
"""

from flask import Blueprint, request, jsonify, Response, g
import json
import logging
from backend.services.context_retrieval import search_by_text
from backend.routes.entries import supabase_auth_required
from backend.services.initial_processing import process_text
from backend.services.embedding import generate_embedding
from datetime import datetime
from openai import OpenAI
import os

logger = logging.getLogger(__name__)

# Create blueprint
converse_bp = Blueprint('converse', __name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

# Yap system prompt template
YAP_SYSTEM_PROMPT = """You are a warm, insightful journaling companion. Today is {TODAY}. 

Your role is to help users explore their thoughts, feelings, and experiences through guided conversation. 

## Response Style
- Be conversational and natural, like talking to a friend
- Keep responses concise and focused
- Use simple, clear language
- Avoid excessive formatting, headers, or bullet points
- Write in a flowing, natural style

## Conversation Approach
- Ask thoughtful, open-ended questions that encourage reflection
- Be genuinely curious about their experiences and perspectives  
- Help them process emotions and find meaning in their experiences
- Be supportive and non-judgmental
- Keep conversations flowing naturally

Remember: You're having a real conversation. Be helpful, insightful, and conversational without over-formatting your responses."""

def get_today_string():
    """Get today's date as a string for the system prompt."""
    from datetime import datetime
    return datetime.now().strftime("%B %d, %Y")

def build_conversation_messages(yap_messages, user_input, context=""):
    """
    Build the messages array for OpenAI API call.
    Converts frontend message format to OpenAI format.
    """
    messages = []
    
    # Add system prompt with today's date
    system_prompt = YAP_SYSTEM_PROMPT.format(TODAY=get_today_string())
    
    # If we have context, add it to the system prompt
    if context:
        if context.startswith("ERROR:"):
            # Search failed - tell AI to inform user
            system_prompt += f"\n\n{context}\n\nYou must inform the user about this error."
        else:
            system_prompt += f"\n\n## User's Journal History\n{context}\n\nUse this context to provide more personalized and relevant responses. Reference specific entries when appropriate."
    
    messages.append({"role": "system", "content": system_prompt})
    
    # Convert yap_messages to OpenAI format
    for msg in yap_messages:
        if msg.get('type') == 'user':
            messages.append({"role": "user", "content": msg.get('content', '')})
        elif msg.get('type') == 'ai':
            messages.append({"role": "assistant", "content": msg.get('content', '')})
    
    # Add the new user input
    messages.append({"role": "user", "content": user_input})
    
    return messages

def get_user_context(user_id, user_supabase, limit=15):
    """
    Get relevant context from user's journal entries for the conversation.
    """
    try:
        # Get recent entries for context
        response = user_supabase.table('entries').select('content,created_at,user_entry_id').eq('user_id', user_id).order('created_at', desc=True).limit(100).execute()
        entries = response.data if response.data else []
        
        if not entries:
            return ""
        
        # Build context from recent entries with better formatting
        context_parts = []
        for entry in entries[:limit]:  # Use specified limit
            content = entry.get('content', '').strip()
            if content:
                # Truncate very long entries to keep context manageable
                if len(content) > 500:
                    content = content[:500] + "..."
                context_parts.append(f"Entry {entry.get('user_entry_id', 'N/A')}: {content}")
        
        return "\n\n".join(context_parts)
    except Exception as e:
        logger.error(f"Error getting user context: {e}")
        return ""

@converse_bp.route('/converse/stream', methods=['POST'])
@supabase_auth_required
def converse_stream():
    """
    Handle streaming conversation with AI.
    Frontend sends: { messages: [...], user_input: "..." }
    Backend handles: OpenAI calls, context, streaming response
    """
    logger.info("=" * 50)
    logger.info("CONVERSE_STREAM ROUTE HIT!")
    logger.info("=" * 50)
    try:
        data = request.get_json()
        
        if not data or 'messages' not in data or 'user_input' not in data:
            logger.error("Missing required fields in request")
            return jsonify({'error': 'Messages and user_input are required'}), 400
        
        yap_messages = data.get('messages', [])
        user_input = data.get('user_input', '').strip()
        
        if not user_input:
            return jsonify({'error': 'User input cannot be empty'}), 400
        
        logger.info(f"Converse request: {len(yap_messages)} previous messages, user input: {user_input[:50]}...")
        logger.info(f"[converse_stream] Starting search for user_id={g.current_user.id}, query={user_input[:50]}")
        
        # Use RAG pipeline to find relevant entries
        from backend.services.context_retrieval import search_by_text
        logger.info(f"[converse_stream] Calling search_by_text...")
        relevant_entries = search_by_text(user_input, limit=3, user_id=g.current_user.id, user_client=g.user_supabase)
        logger.info(f"[converse_stream] search_by_text returned {len(relevant_entries)} entries")
        
        # Build context from relevant entries
        context_parts = []
        sources = []
        search_failed = False
        
        if not relevant_entries:
            # Check if user has entries WITH VECTORS (not just any entries)
            try:
                response = g.user_supabase.table('entries').select('user_and_entry_id').eq('user_id', g.current_user.id).not_.is_('vectors', 'null').limit(1).execute()
                has_vectorized_entries = response.data and len(response.data) > 0
                
                if has_vectorized_entries:
                    # User has vectorized entries but search returned nothing - this is an error
                    logger.warning("HNSW search returned no results but user has vectorized entries - search may have failed")
                    search_failed = True
            except Exception as e:
                logger.error(f"Error checking for user vectorized entries: {e}")
                search_failed = True
        else:
            for entry in relevant_entries:
                content = entry.get('content', '').strip()
                if content:
                    # Truncate very long entries
                    if len(content) > 300:
                        content = content[:300] + "..."
                    context_parts.append(f"Entry {entry.get('user_entry_id', 'N/A')}: {content}")
                    # Add to sources for frontend
                    sources.append({
                        'entry_id': entry.get('entry_id'),
                        'user_entry_id': entry.get('user_entry_id'),
                        'content': content,
                        'similarity': entry.get('similarity', 0)
                    })
        
        context = "\n\n".join(context_parts)
        
        # If search failed, add error message to context
        if search_failed:
            context = "ERROR: There was an error with retrieving your history. Please inform the user: 'There was an error with retrieving your history.'"
        
        # Build conversation messages for OpenAI with context
        messages = build_conversation_messages(yap_messages, user_input, context)
        
        def generate_stream():
            try:
                # Use GPT-4o for streaming
                stream = client.chat.completions.create(
                    model="gpt-4o",
                    messages=messages,
                    temperature=0.7,
                    stream=True
                )
                
                for chunk in stream:
                    if chunk.choices[0].delta.content is not None:
                        content = chunk.choices[0].delta.content
                        yield f"data: {json.dumps({'type': 'content', 'data': content})}\n\n"
                
                # Send sources after content is done
                if sources:
                    yield f"data: {json.dumps({'type': 'sources', 'data': sources})}\n\n"
                
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
                
            except Exception as e:
                logger.exception("Error in streaming conversation")
                yield f"data: {json.dumps({'type': 'error', 'data': str(e)})}\n\n"
        
        # Create streaming response with CORS headers
        # Use text/event-stream for proper SSE support
        response = Response(generate_stream(), mimetype='text/event-stream')
        
        # Set CORS headers explicitly for streaming response
        # The after_request handler should handle this, but we set it here as backup
        origin = request.headers.get('Origin')
        if origin:
            # Build allowed origins list (matching app.py logic)
            allowed_origins = [
                "http://localhost:3000",
                "http://localhost:3001",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:3001",
                "https://yapper-beta.vercel.app",
                "https://yapper.vercel.app"
            ]
            # Also check environment variable
            frontend_urls = os.environ.get('FRONTEND_URL', '')
            if frontend_urls:
                urls = [url.strip() for url in frontend_urls.replace(',', ' ').split() if url.strip()]
                allowed_origins.extend(urls)
            
            # Check if origin is in allowed list
            if origin in allowed_origins:
                response.headers['Access-Control-Allow-Origin'] = origin
        
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, Accept, Origin'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Expose-Headers'] = 'Content-Type'
        
        return response
        
    except Exception as e:
        logger.exception("Error in converse_stream")
        return jsonify({'error': 'Internal server error'}), 500

@converse_bp.route('/converse/save', methods=['POST'])
@supabase_auth_required
def save_conversation():
    """
    Save a complete conversation as a journal entry.
    Frontend sends: { conversation: "formatted conversation text" }
    Backend handles: Database save, validation
    """
    try:
        data = request.get_json()
        
        if not data or 'conversation' not in data:
            return jsonify({'error': 'Conversation text is required'}), 400
        
        conversation_text = data.get('conversation', '').strip()
        
        if not conversation_text:
            return jsonify({'error': 'Conversation cannot be empty'}), 400
        
        # Get the next user entry ID
        user_entries_response = g.user_supabase.table('entries').select('user_entry_id').eq('user_id', g.current_user.id).execute()
        user_entry_count = len(user_entries_response.data) if user_entries_response.data else 0
        next_user_entry_id = user_entry_count + 1
        
        # Save to database (same structure as entries.py)
        entry_data = {
            'user_id': g.current_user.id,
            'user_entry_id': next_user_entry_id,
            'user_and_entry_id': f"{g.current_user.id}_{next_user_entry_id}",
            'content': conversation_text,
            'processed': None,  # Will be processed in background
            'vectors': None     # Will be generated in background
        }
        
        response = g.user_supabase.table('entries').insert(entry_data).execute()
        
        if response.data:
            new_entry = response.data[0]
            entry_id = new_entry.get('user_and_entry_id')  # Primary key is 'user_and_entry_id'
            
            if entry_id:
                # Process and embed in background (same flow as entries.py)
                def process_entry_background(entry_id_value, content_to_process):
                    try:
                        from supabase import create_client
                        from backend.services.initial_processing import process_text
                        from backend.services.embedding import generate_embedding
                        from backend.services.hnsw_index import add_entry_to_index
                        
                        logger.info(f"Starting background processing for conversation entry {entry_id_value}")
                        
                        bg_supabase = create_client(
                            os.environ.get('SUPABASE_URL'),
                            os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
                        )
                        
                        # Step 1: Process content through OpenAI
                        logger.info(f"Step 1: Processing content for entry {entry_id_value}")
                        processed_content = process_text(content_to_process)
                        
                        if not processed_content:
                            logger.warning(f"Processing failed for entry {entry_id_value}, skipping vectorization")
                            return
                        
                        # Step 2: Generate embedding from processed content
                        logger.info(f"Step 2: Generating embedding for entry {entry_id_value}")
                        embedding = generate_embedding(processed_content)
                        
                        if not embedding:
                            logger.warning(f"Embedding generation failed for entry {entry_id_value}")
                            # Still save processed content even if embedding fails
                            bg_supabase.table('entries').update({
                                'processed': processed_content
                            }).eq('user_and_entry_id', entry_id_value).execute()
                            return
                        
                        # Step 3: Update entry with processed content and embedding
                        logger.info(f"Step 3: Updating entry {entry_id_value} with processed content and embedding")
                        bg_supabase.table('entries').update({
                            'processed': processed_content,
                            'vectors': embedding
                        }).eq('user_and_entry_id', entry_id_value).execute()
                        
                        logger.info(f"Conversation entry processed and embedded: {entry_id_value}")
                        
                        # Step 4: Add entry to HNSW index
                        logger.info(f"Step 4: Adding entry {entry_id_value} to HNSW index")
                        try:
                            add_entry_to_index(entry_id_value, embedding)
                            logger.info(f"Conversation entry added to HNSW index: {entry_id_value}")
                        except Exception as e:
                            logger.warning(f"Failed to add conversation entry to HNSW index: {str(e)}")
                    except Exception as e:
                        logger.exception(f"Error processing conversation entry in background: {entry_id_value}")
                
                # Start background processing
                import threading
                thread = threading.Thread(target=process_entry_background, args=(entry_id, conversation_text))
                thread.daemon = True
                thread.start()
            
            logger.info(f"Saved conversation as entry {entry_id}")
            return jsonify({
                'success': True,
                'user_and_entry_id': user_and_entry_id,
                'message': 'Conversation saved successfully'
            })
        else:
            return jsonify({'error': 'Failed to save conversation'}), 500
            
    except Exception as e:
        logger.exception("Error saving conversation")
        return jsonify({'error': 'Failed to save conversation'}), 500

@converse_bp.route('/converse/intro', methods=['GET'])
@supabase_auth_required
def get_conversation_intro():
    """
    Get an AI-generated opening message and topics based on user's journal history.
    Backend handles: Context analysis, AI generation, topic extraction
    """
    try:
        # Get user's recent entries for context (reduced from 100 to 20 for faster response)
        response = g.user_supabase.table('entries').select('content,created_at,user_entry_id').eq('user_id', g.current_user.id).order('created_at', desc=True).limit(20).execute()
        entries = response.data if response.data else []
        
        if not entries:
            return jsonify({
                'opening': "What's on your mind?",
                'topics': []
            })
        
        # Build context from recent entries (reduced from 10 to 5 for faster processing)
        context_parts = []
        for entry in entries[:5]:
            content = entry.get('content', '').strip()
            if content:
                # Truncate entries to keep context manageable
                if len(content) > 300:
                    content = content[:300] + "..."
                context_parts.append(f"Entry {entry.get('user_entry_id', 'N/A')}: {content}")
        
        context = "\n\n".join(context_parts)
        
        system_prompt = (
            "You are a warm journaling companion. Given the user's recent journal text, "
            "identify 3 to 7 concise subjects that are especially interesting, emotionally salient, or important. "
            "Rank them in descending order of salience. "
            "Then propose a single, inviting question (ONE sentence only) to start today's conversation. "
            "The opening should be a single question that invites reflection, like 'What's on your mind?' or 'What stood out about today?'. "
            "Keep it to one sentence - no follow-up statements or explanations. "
            "Respond strictly as JSON with keys 'topics' (array of strings) and 'opening' (string)."
        )
        
        user_prompt = f"User's recent entries (most recent first):\n\n{context}\n\nReturn JSON only."
        
        # Generate with AI (use gpt-4o-mini for faster, cheaper intro generation)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=200  # Limit response length for faster generation
        )
        
        content = resp.choices[0].message.content if resp.choices else '{}'
        
        try:
            data = json.loads(content)
        except Exception:
            # Fallback if JSON parsing fails
            data = {'opening': "What stood out about today?", 'topics': []}
        
        opening = data.get('opening') or "What stood out about today?"
        topics = data.get('topics') or []
        
        return jsonify({'opening': opening, 'topics': topics})
        
    except Exception as e:
        logger.exception("Error generating conversation intro")
        return jsonify({
            'opening': "What's on your mind?",
            'topics': []
        })
