from flask import Blueprint, request, jsonify
from backend.models.page import Page
from backend.services.initial_processing import process_text
from backend.services.Character.Personality_Profile import personality_definer, write_personality_to_db
from backend.models.personality import Personality
from extensions import db

pages_bp = Blueprint('pages', __name__)

@pages_bp.route('/pages', methods=['POST'])
def create_page():
    print("Received request:", request.get_json())  # Debug print
    data = request.get_json()
    
    if not data or 'content' not in data:
        print("Invalid data received")  # Debug print
        return jsonify({'error': 'Content is required'}), 400
    
    try:
        # Process content through OpenAI
        processed_content = process_text(data['content'])
        print(processed_content)
        new_page = Page(
            content=data['content'],
            processed=processed_content
        )

        db.session.add(new_page)
        db.session.commit()
        response_data = new_page.to_dict()
        
        personality = write_personality_to_db(new_page.entry_id,processed_content)        
        response_data['personality'] = personality

        return jsonify(response_data), 201

    except Exception as e:
        print("Error:", str(e))  # Debug print
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@pages_bp.route('/pages', methods=['GET'])
def get_pages():
    pages = Page.query.order_by(Page.created_at.desc()).all()
    return jsonify([page.to_dict() for page in pages])

@pages_bp.route('/pages/<int:entry_id>', methods=['GET'])
def get_page(entry_id):
    page = Page.query.get_or_404(entry_id)
    return jsonify(page.to_dict()) 