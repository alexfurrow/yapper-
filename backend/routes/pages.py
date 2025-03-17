from flask import Blueprint, request, jsonify
from extensions import db

from backend.models.Page_Table import Page_Table

#Initial Processing
from backend.services.initial_processing import process_text

#Personality
from backend.services.personality_profile import personality_prompt, create_personality_and_write_to_db
from backend.models.Personality_Table import Personality_Table

#Story Components
# from backend.services import plot_set_char_prompt, create_story_components_and_write_to_db
# from backend.models.Plot_Set_Char_Table import Plot_Set_Char_Table

#Story
from backend.services.write_story import write_story_and_write_to_db
from backend.models.Story_Table import Story_Table

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
        new_page = Page_Table(
            content=data['content'],
            processed=processed_content
        )

        db.session.add(new_page)
        db.session.commit()
        response_data = new_page.to_dict()
        
        personality = create_personality_and_write_to_db(new_page.entry_id,processed_content)        
        response_data['personality'] = personality

        story = write_story_and_write_to_db(new_page.entry_id,processed_content)
        # story = write_story_and_write_to_db(new_page.entry_id,data['content'])
        response_data['story'] = story

        return jsonify(response_data), 201

    except Exception as e:
        print("Error:", str(e))  # Debug print
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@pages_bp.route('/pages', methods=['GET'])
def get_pages():
    pages = Page_Table.query.order_by(Page_Table.created_at.desc()).all()
    return jsonify([page.to_dict() for page in pages])

@pages_bp.route('/pages/<int:entry_id>', methods=['GET'])
def get_page(entry_id):
    page = Page_Table.query.get_or_404(entry_id)
    return jsonify(page.to_dict())

@pages_bp.route('/pages/search', methods=['POST'])
def search_similar_pages():
    data = request.get_json()
    
    if not data or 'query' not in data:
        return jsonify({'error': 'Query is required'}), 400
    
    try:
        from backend.services.embedding_service import find_similar_pages
        
        limit = data.get('limit', 5)
        similar_pages = find_similar_pages(data['query'], limit)
        
        return jsonify({
            'results': similar_pages
        }), 200
    except Exception as e:
        print(f"Error searching pages: {str(e)}")
        return jsonify({'error': str(e)}), 500 