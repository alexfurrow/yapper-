from flask import Blueprint, request, jsonify
from openai import OpenAI
import os
from dotenv import load_dotenv
from backend.services.embedding import search_by_text
from backend.routes.auth import token_required
from extensions import db
from backend.models.entries import entries

# Load environment variables
load_dotenv(override=True)

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/test', methods=['GET'])
def test_chat_blueprint():
    """Simple test endpoint to verify chat blueprint is working"""
    return jsonify({'message': 'Chat blueprint is working!', 'status': 'ok'}), 200

@chat_bp.route('/debug', methods=['GET', 'OPTIONS'])
@token_required
def debug_user_entries(current_user):
    """Debug endpoint to check user's entries and embeddings"""
    if request.method == 'OPTIONS':
        return '', 200
    try:
        # Get all entries for the user
        user_entries = entries.query.filter_by(user_id=current_user.id).all()
        
        # Count entries with and without embeddings
        total_entries = len(user_entries)
        entries_with_embeddings = len([e for e in user_entries if e.vectors is not None])
        entries_without_embeddings = total_entries - entries_with_embeddings
        
        return jsonify({
            'user_id': current_user.id,
            'total_entries': total_entries,
            'entries_with_embeddings': entries_with_embeddings,
            'entries_without_embeddings': entries_without_embeddings,
            'sample_entries': [
                {
                    'entry_id': e.entry_id,
                    'has_embedding': e.vectors is not None,
                    'content_preview': e.content[:100] + '...' if len(e.content) > 100 else e.content
                } for e in user_entries[:5]  # Show first 5 entries
            ]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@chat_bp.route('/', methods=['POST', 'OPTIONS'])
@token_required
def chat_with_database(current_user):
    if request.method == 'OPTIONS':
        return '', 200
        
    data = request.get_json()
    
    if not data or 'message' not in data:
        return jsonify({'error': 'Message is required'}), 400
    
    try:
        # Get user message
        user_message = data['message']
        print(f"Chat request from user {current_user.id}: {user_message}")
        
        # Search for relevant entries (only for current user)
        limit = data.get('limit', 3)  # Default to 3 most relevant entries
        similar_entries = search_by_text(user_message, limit, user_id=current_user.id)
        
        print(f"Found {len(similar_entries)} similar entries for user {current_user.id}")
        
        # Debug: Print each entry found
        for i, entry in enumerate(similar_entries):
            print(f"Entry {i+1}: ID={entry['entry_id']}, Similarity={entry['similarity']:.3f}")
            print(f"  Content preview: {entry['processed'][:100]}...")
        
        # Extract content from similar entries
        context = ""
        for entry in similar_entries:
            context += f"Entry {entry['entry_id']} (similarity: {entry['similarity']:.2f}):\n{entry['processed']}\n\n"
        
        print(f"Context length: {len(context)} characters")
        print(f"Context preview: {context[:200]}...")
        
        # If no context found, let the AI know
        if not context.strip():
            print("WARNING: No context found - no similar entries or empty processed content")
            context = "No relevant journal entries found for this query."
        
        # Generate response using OpenAI
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": 
                 """You are an AI assistant that answers questions based on the user's journal entries. 
                 You'll be provided with relevant entries from their journal database.
                 Use this context to provide insightful, personalized responses.
                 If the context doesn't contain relevant information, acknowledge that and provide a general response.
                 Always maintain a conversational, helpful tone."""},
                {"role": "user", "content": f"Context from journal entries:\n\n{context}\n\nUser question: {user_message}"}
            ],
            temperature=0.7
        )
        
        ai_response = response.choices[0].message.content
        
        return jsonify({
            'response': ai_response,
            'sources': [{'entry_id': entry['entry_id'], 'similarity': entry['similarity']} for entry in similar_entries]
        }), 200
        
    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500 