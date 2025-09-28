from flask import Blueprint, request, jsonify, g, Response
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
client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY')
)

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
def chat_stream():
    """Streaming chat endpoint with authentication"""
    data = request.get_json()
    
    if not data or 'message' not in data:
        return jsonify({'error': 'Message is required'}), 400
    
    # Capture user context before generator function
    user_id = g.current_user.id
    user_supabase = g.user_supabase
    user_message = data['message']
    limit = data.get('limit', 3)
    
    def generate():
        try:
            logger.info("Generator function started", extra={"route": "/chat/stream", "method": "POST", "user_id": user_id})
            logger.info("Streaming chat request received", extra={"route": "/chat/stream", "method": "POST", "user_id": user_id, "message_length": len(user_message)})
            
            # Search for relevant entries (only for current user)
            similar_entries = search_by_text(user_message, limit, user_id=user_id, user_client=user_supabase)
            logger.info("Similar entries found", extra={"route": "/chat/stream", "method": "POST", "user_id": user_id, "count": len(similar_entries)})
            
            # Extract content from similar entries
            context = ""
            for entry in similar_entries:
                context += f"Entry {entry.get('user_entry_id', 'N/A')} (similarity: {entry['similarity']:.2f}):\n{entry.get('processed', 'No processed content')}\n\n"
            
            # If no context found, let the AI know
            if not context.strip():
                context = "No relevant journal entries found for this query."
            
            # Store sources for later (we'll send them after the response is complete)
            sources = [{'entry_id': entry.get('user_entry_id', 'N/A'), 'similarity': entry['similarity']} for entry in similar_entries]
            
            # Generate streaming response using OpenAI
            stream = client.chat.completions.create(
                model="gpt-4o",
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
            
            # Stream the response
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    yield f"data: {json.dumps({'type': 'content', 'data': content})}\n\n"
            
            # Send completion signal first
            logger.info("Streaming completed, sending done signal", extra={"route": "/chat/stream", "method": "POST", "user_id": user_id})
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
            
            # Send sources after the response is complete
            logger.info("Sending sources", extra={"route": "/chat/stream", "method": "POST", "user_id": user_id, "sources_count": len(sources), "sources_data": sources})
            yield f"data: {json.dumps({'type': 'sources', 'data': sources})}\n\n"
            logger.info("Sources sent successfully", extra={"route": "/chat/stream", "method": "POST", "user_id": user_id})
            
        except Exception as e:
            # Don't access Flask context in exception handler during streaming
            logger.exception("Error in streaming chat endpoint", extra={"route": "/chat/stream", "method": "POST", "user_id": "unknown"})
            yield f"data: {json.dumps({'type': 'error', 'data': str(e)})}\n\n"
    
    return Response(generate(), mimetype='text/plain', headers={
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Content-Type': 'text/plain; charset=utf-8'
    })