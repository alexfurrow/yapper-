from flask import Blueprint, request, jsonify, g, Response, stream_template
from werkzeug.exceptions import InternalServerError
from openai import OpenAI
import os
import json
from dotenv import load_dotenv
from backend.services.embedding import search_by_text
from supabase import create_client, Client
from functools import wraps
from backend.config.logging import get_logger

# Set up logging
logger = get_logger(__name__)

# Required environment variables
REQUIRED_ENV = [
    "SUPABASE_URL",
    "SUPABASE_ANON_KEY",
    "SUPABASE_SERVICE_ROLE_KEY",
    "OPENAI_API_KEY"
]

def validate_env():
    """Validate that all required environment variables are present"""
    missing = [k for k in REQUIRED_ENV if not os.environ.get(k)]
    if missing:
        # Log only the variable names, not values
        raise InternalServerError(f"Missing required environment variables: {', '.join(missing)}")

# Load environment variables
load_dotenv(override=True)

# Validate environment variables
validate_env()

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

# Initialize Supabase client
supabase: Client = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
)

chat_bp = Blueprint('chat', __name__)

# Function to create user-specific Supabase client
def create_user_supabase_client(user_token: str):
    """Create a Supabase client that operates as the authenticated user"""
    client = create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_ANON_KEY"]
    )
    # v2 way: attach JWT to PostgREST
    client.postgrest.auth(user_token)
    return client

# Supabase auth decorator
def supabase_auth_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return jsonify({"msg": "Missing or invalid authorization header"}), 401
            
            token = auth_header.split(' ')[1]
            
            # Verify the token with Supabase
            response = supabase.auth.get_user(token)
            if not response.user:
                return jsonify({"msg": "Invalid or expired token"}), 401
            
            # Create user-specific Supabase client
            user_supabase = create_user_supabase_client(token)
            
            # Store in Flask g for global access
            g.current_user = response.user
            g.user_supabase = user_supabase
            
            # Call the function with original args (no extra arguments)
            return f(*args, **kwargs)
            
        except Exception as e:
            return jsonify({"msg": "Invalid or expired token", "error": str(e)}), 401
    return decorated_function

@chat_bp.route('/chat/stream', methods=['POST'])
@supabase_auth_required
def chat_with_database():
    """Chat endpoint with authentication"""
    logger.info("=== CHAT ENDPOINT DEBUG START ===")
    logger.info("Request method: POST")
    logger.info("Request headers: " + str(dict(request.headers)))
    logger.info("Request data: " + str(request.get_data()))
    
    data = request.get_json()
    logger.info("Parsed JSON data: " + str(data))
    
    if not data or 'message' not in data:
        logger.error("Missing message in request data")
        return jsonify({'error': 'Message is required'}), 400
    
    try:
        # Debug environment variables
        logger.info("=== ENVIRONMENT DEBUG ===")
        logger.info("OPENAI_API_KEY exists: " + str(bool(os.environ.get('OPENAI_API_KEY'))))
        logger.info("OPENAI_API_KEY length: " + str(len(os.environ.get('OPENAI_API_KEY', ''))))
        logger.info("SUPABASE_URL: " + str(os.environ.get('SUPABASE_URL', 'NOT_SET')))
        logger.info("SUPABASE_ANON_KEY exists: " + str(bool(os.environ.get('SUPABASE_ANON_KEY'))))
        
        # Get user message
        user_message = data['message']
        logger.info("Chat request received", extra={"route": "/chat/stream", "method": "POST", "user_id": g.current_user.id, "message_length": len(user_message)})
        
        # Search for relevant entries (only for current user)
        limit = data.get('limit', 3)  # Default to 3 most relevant entries
        similar_entries = search_by_text(user_message, limit, user_id=g.current_user.id, user_client=g.user_supabase)
        logger.info("Similar entries found", extra={"route": "/chat/stream", "method": "POST", "user_id": g.current_user.id, "count": len(similar_entries)})
        
        # Extract content from similar entries
        context = ""
        for entry in similar_entries:
            context += f"Entry {entry.get('user_entry_id', 'N/A')} (similarity: {entry['similarity']:.2f}):\n{entry.get('processed', 'No processed content')}\n\n"
        
        # If no context found, let the AI know
        if not context.strip():
            context = "No relevant journal entries found for this query."
        
        # Generate streaming response using OpenAI
        def generate_stream():
            try:
                stream = client.chat.completions.create(
            model="gpt-5",
            messages=[
                {"role": "system", "content": 
                 """You are an AI assistant that answers questions based on the user's journal entries. 
                 You'll be provided with relevant entries from their journal database.
                 If the context doesn't contain relevant information, acknowledge that and provide a general response.
                 Always maintain a conversational, helpful tone."""},
                {"role": "user", "content": f"Context from journal entries:\n\n{context}\n\nUser question: {user_message}"}
            ],
                    temperature=0.7,
                    stream=True
                )

                # Stream the AI response
                for chunk in stream:
                    if chunk.choices[0].delta.content is not None:
                        content = chunk.choices[0].delta.content
                        yield f"data: {json.dumps({'type': 'content', 'data': content})}\n\n"
                # Send completion signal
                yield f"data: {json.dumps({'type': 'done'})}\n\n"

                # Send sources after completion
                sources_data = [{'entry_id': entry.get('user_entry_id', 'N/A'), 'similarity': entry['similarity']} for entry in similar_entries]
                yield f"data: {json.dumps({'type': 'sources', 'data': sources_data})}\n\n"
                
            except Exception as e:
                logger.exception("Error in streaming chat", extra={"route": "/chat/stream", "method": "POST", "user_id": "unknown"})
                yield f"data: {json.dumps({'type': 'error', 'data': str(e)})}\n\n"
        
        return Response(generate_stream(), mimetype='text/plain')
        
    except Exception as e:
        logger.exception("Error in chat endpoint", extra={"route": "/chat/stream", "method": "POST", "user_id": "unknown"})
        return jsonify({'error': str(e)}), 500 


@chat_bp.route('/chat/yap_intro', methods=['GET'])
@supabase_auth_required
def yap_intro():
    """Return an opening prompt and ranked topics based on recent user entries.
    Response: { opening: str, topics: [str, ...] }
    """
    try:
        # Fetch recent entries for the user
        res = supabase.table('entries').select('content, created_at, user_entry_id').eq('user_id', g.current_user.id).order('created_at', desc=True).limit(100).execute()
        entries = res.data or []

        if len(entries) == 0:
            return jsonify({
                'opening': "What's on your mind? Talk as long as you want.",
                'topics': []
            })

        # Build context: start with 10, then add 5 until >= 3000 chars or exhausted
        collected = []
        total_len = 0
        take = 10
        idx = 0
        while idx < len(entries):
            batch = entries[idx: idx + take]
            for e in batch:
                text = (e.get('content') or '').strip()
                if not text:
                    continue
                collected.append(f"Entry {e.get('user_entry_id','N/A')}: {text}")
                total_len += len(text) + 20
            if total_len >= 3000 or (idx + take) >= len(entries):
                break
            idx += take
            take = 5

        context = "\n\n".join(collected)

        system_prompt = (
            "You are a warm journaling companion. Given the user's recent journal text, "
            "identify 3 to 7 concise subjects that are especially interesting, emotionally salient, or important. "
            "Rank them in descending order of salience. Then propose a short, inviting opening line for today's conversation. "
            "Respond strictly as JSON with keys 'topics' (array of strings) and 'opening' (string)."
        )

        user_prompt = (
            f"User's recent entries (most recent first):\n\n{context}\n\n"
            "Return JSON only."
        )

        resp = client.chat.completions.create(
            model="gpt-5",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
        )

        content = resp.choices[0].message.content if resp.choices else '{}'
        try:
            data = json.loads(content)
        except Exception:
            # Fallback naive parse
            data = { 'opening': "Let's talk about your day. What stood out?", 'topics': [] }

        opening = data.get('opening') or "Let's talk about your day. What stood out?"
        topics = data.get('topics') or []
        return jsonify({ 'opening': opening, 'topics': topics })

    except Exception as e:
        logger.exception("Error in yap_intro", extra={"route": "/chat/yap_intro", "method": "GET", "user_id": "unknown"})
        return jsonify({'error': str(e)}), 500