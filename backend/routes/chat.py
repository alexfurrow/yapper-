from flask import Blueprint, request, jsonify, g
from werkzeug.exceptions import InternalServerError
from openai import OpenAI
import os
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

@chat_bp.route('/chat/chat', methods=['POST'])
@supabase_auth_required
def chat_with_database():
    """Chat endpoint with authentication"""
    data = request.get_json()
    
    if not data or 'message' not in data:
        return jsonify({'error': 'Message is required'}), 400
    
    try:
        # Get user message
        user_message = data['message']
        logger.info("Chat request received", extra={"route": "/chat/chat", "method": "POST", "user_id": g.current_user.id, "message_length": len(user_message)})
        
        # Search for relevant entries (only for current user)
        limit = data.get('limit', 3)  # Default to 3 most relevant entries
        similar_entries = search_by_text(user_message, limit, user_id=g.current_user.id)
        logger.info("Similar entries found", extra={"route": "/chat/chat", "method": "POST", "user_id": g.current_user.id, "count": len(similar_entries)})
        
        # Extract content from similar entries
        context = ""
        for entry in similar_entries:
            context += f"Entry {entry.get('user_entry_id', 'N/A')} (similarity: {entry['similarity']:.2f}):\n{entry.get('processed', 'No processed content')}\n\n"
        
        # If no context found, let the AI know
        if not context.strip():
            context = "No relevant journal entries found for this query."
        
        # Generate response using OpenAI
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": 
                 """You are an AI assistant that answers questions based on the user's journal entries. 
                 You'll be provided with relevant entries from their journal database.
                 If the context doesn't contain relevant information, acknowledge that and provide a general response.
                 Always maintain a conversational, helpful tone."""},
                {"role": "user", "content": f"Context from journal entries:\n\n{context}\n\nUser question: {user_message}"}
            ],
            temperature=0.7
        )
        
        ai_response = response.choices[0].message.content
        logger.info("Chat response generated", extra={"route": "/chat/chat", "method": "POST", "user_id": g.current_user.id, "response_length": len(ai_response)})
        
        return jsonify({
            'response': ai_response,
            'sources': [{'entry_id': entry.get('user_entry_id', 'N/A'), 'similarity': entry['similarity']} for entry in similar_entries]
        }), 200
        
    except Exception as e:
        logger.exception("Error in chat endpoint", extra={"route": "/chat/chat", "method": "POST", "user_id": g.current_user.id})
        return jsonify({'error': str(e)}), 500