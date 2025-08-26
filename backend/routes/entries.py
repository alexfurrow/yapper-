from flask import Blueprint, request, jsonify, current_app
from extensions import db
from backend.models.users import users
from backend.models.entries import entries
from backend.routes.auth import token_required
from backend.services.initial_processing import process_text
from backend.services.embedding import generate_embedding

entries_bp = Blueprint('entries', __name__, url_prefix='/entries')

@entries_bp.route('/entries', methods=['GET'])
@token_required
def get_entries(current_user):
    """Get all entries for the current user"""
    all_entries = entries.query.filter_by(user_id=current_user.id).order_by(entries.created_at.desc()).all()
    return jsonify([entry.to_dict() for entry in all_entries]), 200

@entries_bp.route('/entries', methods=['POST'])
@token_required
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
        
        # Create new entry
        new_entry = entries(
            user_id=current_user.id,
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
@token_required
def get_entry(current_user, entry_id):
    """Get a specific entry by ID"""
    entry = entries.query.filter_by(entry_id=entry_id, user_id=current_user.id).first()
    
    if not entry:
        return jsonify({'message': 'Entry not found'}), 404
    
    return jsonify(entry.to_dict()), 200

@entries_bp.route('/entries/<int:entry_id>', methods=['PUT'])
@token_required
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
@token_required
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
@token_required
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