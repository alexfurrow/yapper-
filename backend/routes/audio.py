from flask import Blueprint, request, jsonify, g
import os
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from backend.services.embedding import generate_embedding
from backend.services.initial_processing  import process_text
import logging
from backend.routes.entries import supabase_auth_required
from backend.utils.audio_transcription import transcribe_audio_file
from backend.utils.entry_helpers import format_title_date_with_time

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

        # Transcribe using utility function
        transcription, error_msg = transcribe_audio_file(temp_path)
        
        # Clean up the temporary file
        os.remove(temp_path)
        
        if transcription is None:
            logger.warning(f"Transcription failed: {error_msg}", extra={"route": "/api/audio", "method": "POST", "user_id": g.current_user.id})
            return jsonify({'error': error_msg}), 400

        logger.info("Audio transcription successful", extra={"route": "/api/audio", "method": "POST", "user_id": g.current_user.id, "transcription_length": len(transcription)})

            # Return just the transcription - let frontend decide what to do with it
            # Frontend will handle saving to DB or sending to chat based on mode
            return jsonify({
                'transcription': transcription,
                'success': True
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