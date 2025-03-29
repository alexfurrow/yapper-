from flask import Blueprint, request, jsonify
from models import db, User, UserInput
from backend.routes.auth import token_required
from backend.services.initial_processing import process_text

entries_bp = Blueprint('entries', __name__)

@entries_bp.route('/entries', methods=['GET'])
@token_required
def get_entries(user):
    entries = UserInput.query.filter_by(user_id=user.id).order_by(UserInput.created_at.desc()).all()
    
    return jsonify([{
        'entry_id': entry.entry_id,
        'content': entry.content,
        'created_at': entry.created_at,
        'updated_at': entry.updated_at
    } for entry in entries]), 200

@entries_bp.route('/entries', methods=['POST'])
@token_required
def create_entry(user):
    data = request.get_json()
    
    if not data or not data.get('content'):
        return jsonify({'message': 'Content is required'}), 400
    
    # Create new entry
    new_entry = UserInput(
        user_id=user.id,
        content=data['content']
    )
    
    # Process the content
    processed_content = process_text(data['content'])
    if processed_content:
        new_entry.processed = processed_content
    
    db.session.add(new_entry)
    db.session.commit()
    
    return jsonify({
        'entry_id': new_entry.entry_id,
        'content': new_entry.content,
        'created_at': new_entry.created_at,
        'updated_at': new_entry.updated_at
    }), 201

@entries_bp.route('/entries/<int:entry_id>', methods=['GET'])
@token_required
def get_entry(user, entry_id):
    entry = UserInput.query.filter_by(entry_id=entry_id, user_id=user.id).first()
    
    if not entry:
        return jsonify({'message': 'Entry not found'}), 404
    
    return jsonify({
        'entry_id': entry.entry_id,
        'content': entry.content,
        'created_at': entry.created_at,
        'updated_at': entry.updated_at
    }), 200

@entries_bp.route('/entries/<int:entry_id>', methods=['PUT'])
@token_required
def update_entry(user, entry_id):
    entry = UserInput.query.filter_by(entry_id=entry_id, user_id=user.id).first()
    
    if not entry:
        return jsonify({'message': 'Entry not found'}), 404
    
    data = request.get_json()
    
    if not data or not data.get('content'):
        return jsonify({'message': 'Content is required'}), 400
    
    entry.content = data['content']
    db.session.commit()
    
    return jsonify({
        'entry_id': entry.entry_id,
        'content': entry.content,
        'created_at': entry.created_at,
        'updated_at': entry.updated_at
    }), 200

@entries_bp.route('/entries/<int:entry_id>', methods=['DELETE'])
@token_required
def delete_entry(user, entry_id):
    entry = UserInput.query.filter_by(entry_id=entry_id, user_id=user.id).first()
    
    if not entry:
        return jsonify({'message': 'Entry not found'}), 404
    
    db.session.delete(entry)
    db.session.commit()
    
    return jsonify({'message': 'Entry deleted successfully'}), 200 