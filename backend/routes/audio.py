from flask import Blueprint, request, jsonify, g
import os
from werkzeug.utils import secure_filename
import requests
import json
from dotenv import load_dotenv
from backend.services.embedding import generate_embedding
from backend.services.initial_processing  import process_text
import logging
from backend.routes.entries import supabase_auth_required

# Load environment variables
load_dotenv()
logger = logging.getLogger(__name__)

audio_bp = Blueprint('audio', __name__, url_prefix='/api')

@audio_bp.route('/audio', methods=['POST'])
@supabase_auth_required
def upload_audio_api():
    """Process audio file and create journal entry with transcription"""
    try:
        # Validate request
        if 'audio' not in request.files:
            logger.warning("Audio upload request missing audio file", extra={"route": "/api/audio", "method": "POST", "user_id": g.current_user.id})
            return jsonify({'error': 'No audio file provided'}), 400

        audio_file = request.files['audio']
        if audio_file.filename == '':
            logger.warning("Audio upload request with empty filename", extra={"route": "/api/audio", "method": "POST", "user_id": g.current_user.id})
            return jsonify({'error': 'No audio file selected'}), 400

        # Validate file size (max 25MB for Whisper API)
        audio_file.seek(0, os.SEEK_END)
        file_size = audio_file.tell()
        audio_file.seek(0)
        
        max_size = 25 * 1024 * 1024  # 25MB
        if file_size > max_size:
            logger.warning("Audio file too large", extra={"route": "/api/audio", "method": "POST", "user_id": g.current_user.id, "file_size": file_size})
            return jsonify({'error': 'Audio file too large. Maximum size is 25MB.'}), 400

        logger.info("Processing audio file", extra={"route": "/api/audio", "method": "POST", "user_id": g.current_user.id, "file_size": file_size})

        # Save the audio file temporarily
        filename = secure_filename(audio_file.filename)
        temp_path = os.path.join('temp', filename)
        os.makedirs('temp', exist_ok=True)
        audio_file.save(temp_path)

        # Get API key from environment variable
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            logger.error("OpenAI API key not configured", extra={"route": "/api/audio", "method": "POST", "user_id": g.current_user.id})
            return jsonify({'error': 'Audio processing service not configured'}), 500

        # Call OpenAI's Whisper API
        with open(temp_path, 'rb') as audio_data:
            headers = {
                'Authorization': f'Bearer {api_key}'
            }
            response = requests.post(
                'https://api.openai.com/v1/audio/transcriptions',
                headers=headers,
                files={
                    'file': audio_data,
                },
                data={
                    'model': 'whisper-1',
                }
            )
        
        # Clean up the temporary file
        os.remove(temp_path)

        # Process the API response
        if response.status_code == 200:
            result = response.json()
            transcription = result.get('text', '').strip()
            
            if not transcription:
                logger.warning("Empty transcription from Whisper API", extra={"route": "/api/audio", "method": "POST", "user_id": g.current_user.id})
                return jsonify({'error': 'No speech detected in audio file'}), 400

            logger.info("Audio transcription successful", extra={"route": "/api/audio", "method": "POST", "user_id": g.current_user.id, "transcription_length": len(transcription)})

            # Process content through OpenAI for better journal entry
            processed_content = process_text(transcription)
            
            # Get the next user entry ID
            user_entries_response = g.user_supabase.table('entries').select('user_entry_id').execute()
            user_entry_count = len(user_entries_response.data)
            next_user_entry_id = user_entry_count + 1

            # Prepare entry data
            entry_data = {
                'user_id': g.current_user.id,
                'user_entry_id': next_user_entry_id,
                'content': transcription,
                'processed': processed_content
            }

            # Generate embedding for the processed content
            if processed_content:
                embedding = generate_embedding(processed_content)
                if embedding:
                    entry_data['vectors'] = embedding
                    logger.info("Embedding generated for audio entry", extra={"route": "/api/audio", "method": "POST", "user_id": g.current_user.id, "user_entry_id": next_user_entry_id})

            # Create entry in database
            response = g.user_supabase.table('entries').insert(entry_data).execute()
            new_entry = response.data[0] if response.data else None

            if not new_entry:
                logger.error("Failed to create audio entry in database", extra={"route": "/api/audio", "method": "POST", "user_id": g.current_user.id})
                return jsonify({'error': 'Failed to save journal entry'}), 500

            logger.info("Audio entry created successfully", extra={"route": "/api/audio", "method": "POST", "user_id": g.current_user.id, "user_entry_id": next_user_entry_id})

            return jsonify({
                'message': 'Audio processed and journal entry created successfully',
                'transcription': transcription,
                'entry': new_entry
            }), 200
        else:
            logger.error("Whisper API error", extra={"route": "/api/audio", "method": "POST", "user_id": g.current_user.id, "status_code": response.status_code, "response": response.text})
            return jsonify({
                'error': f'Audio processing failed: {response.status_code}',
                'details': response.text
            }), 500

    except Exception as e:
        logger.exception("Error processing audio", extra={"route": "/api/audio", "method": "POST", "user_id": g.current_user.id})
        return jsonify({'error': f'Audio processing failed: {str(e)}'}), 500 