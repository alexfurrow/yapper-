from flask import Blueprint, request, jsonify, current_app
from extensions import db
from backend.models.entries import entries
# Remove this line: from backend.routes.auth import token_required
from backend.services.initial_processing import process_text
from backend.services.embedding import generate_embedding
import os
from supabase import create_client, Client

entries_bp = Blueprint('entries', __name__, url_prefix='/entries')

# Initialize Supabase client
supabase: Client = createClient(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
)

# New Supabase auth decorator
def supabase_auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'message': 'Token is missing!'}), 401
        
        token = auth_header.split(' ')[1]
        
        try:
            # Verify token with Supabase
            user = supabase.auth.get_user(token)
            if not user.user:
                return jsonify({'message': 'Invalid token!'}), 401
            return f(user.user, *args, **kwargs)
        except Exception as e:
            return jsonify({'message': 'Token verification error!'}), 401
    
    return decorated

# Update all your route decorators from @token_required to @supabase_auth_required
@entries_bp.route('/entries', methods=['GET'])
@supabase_auth_required
def get_entries(current_user):
    """Get all entries for the current user"""
    all_entries = entries.query.filter_by(user_id=current_user.id).order_by(entries.created_at.desc()).all()
    return jsonify([entry.to_dict() for entry in all_entries]), 200

@entries_bp.route('/entries', methods=['POST'])

def create_entry(current_user):
    """Create a new entry with processed content and immediate embedding"""
    print("Received request:", request.get_json())  # Debug print
    data = request.get_json()
    
    if not data or not data.get('content'):
        print("Invalid data received")  # Debug print
        return jsonify({'message': 'Content is required'}), 400
    
    try:
        # Process content through OpenAI
        processed_content = process_text(data['content'])
        print(f"Processed content: {processed_content}")
        
        # Get the next user entry ID atomically
        with db.session.begin():
            user_entry_count = entries.query.filter_by(user_id=current_user.id).count()
            next_user_entry_id = user_entry_count + 1
            
            # Create new entry
            new_entry = entries(
                user_id=current_user.id,
                user_entry_id=next_user_entry_id,
                content=data['content'],
                processed=processed_content
            )
            
            db.session.add(new_entry)
            db.session.flush()  # Get the entry_id without committing
            
            # Generate embedding immediately for real-time search
            if processed_content:
                embedding = generate_embedding(processed_content)
                if embedding:
                    new_entry.vectors = embedding
                    print(f"Generated embedding for entry {new_entry.entry_id}")
                else:
                    print(f"Failed to generate embedding for entry {new_entry.entry_id}")
        
        db.session.commit()
        
        response_data = new_entry.to_dict()
        
        # Uncomment if you want to add personality or story generation
        # personality = create_personality_and_write_to_db(new_entry.entry_id, processed_content)        
        # response_data['personality'] = personality
        
        # story = write_story_and_write_to_db(new_entry.entry_id, processed_content)
        # response_data['story'] = story
        
        return jsonify(response_data), 201
    except Exception as e:
        print(f"Error creating entry: {str(e)}")
        db.session.rollback()
        return jsonify({'message': f'Error creating entry: {str(e)}'}), 500

@entries_bp.route('/entries/<int:entry_id>', methods=['GET'])
@supabase_auth_required
def get_entry(current_user, entry_id):
    """Get a specific entry by ID"""
    entry = entries.query.filter_by(entry_id=entry_id, user_id=current_user.id).first()
    
    if not entry:
        return jsonify({'message': 'Entry not found'}), 404
    
    return jsonify(entry.to_dict()), 200

@entries_bp.route('/entries/<int:entry_id>', methods=['PUT'])
@supabase_auth_required
def update_entry(current_user, entry_id):
    """Update an existing entry"""
    entry = entries.query.filter_by(entry_id=entry_id, user_id=current_user.id).first()
    
    if not entry:
        return jsonify({'message': 'Entry not found'}), 404
    
    data = request.get_json()
    
    if not data or not data.get('content'):
        return jsonify({'message': 'Content is required'}), 400
    
    try:
        entry.content = data['content']
        
        # Re-process the content if requested
        if data.get('reprocess', False):
            processed_content = process_text(data['content'])
            entry.processed = processed_content
            
        db.session.commit()
        
        return jsonify(entry.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error updating entry: {str(e)}'}), 500

@entries_bp.route('/entries/<int:entry_id>', methods=['DELETE'])
@supabase_auth_required
def delete_entry(current_user, entry_id):
    """Delete an entry"""
    entry = entries.query.filter_by(entry_id=entry_id, user_id=current_user.id).first()
    
    if not entry:
        return jsonify({'message': 'Entry not found'}), 404
    
    try:
        db.session.delete(entry)
        db.session.commit()
        
        return jsonify({'message': 'Entry deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error deleting entry: {str(e)}'}), 500

@entries_bp.route('/entries/search', methods=['POST'])
@supabase_auth_required
def search_entries(current_user):
    """Search for similar entries using vector embeddings"""
    data = request.get_json()
    
    if not data or 'query' not in data:
        return jsonify({'error': 'Query is required'}), 400
    
    try:
        from backend.services.embedding import search_by_text
        
        limit = data.get('limit', 5)
        # Only search the current user's entries
        similar_entries = search_by_text(data['query'], limit, user_id=current_user.id)
        
        return jsonify({
            'results': similar_entries
        }), 200
    except Exception as e:
        print(f"Error searching entries: {str(e)}")
        return jsonify({'error': str(e)}), 500 