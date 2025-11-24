from flask import Blueprint, request, jsonify, g
import os
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from backend.services.embedding import generate_embedding
from backend.services.initial_processing  import process_text
from datetime import datetime
from backend.config.logging import get_logger
from backend.routes.entries import supabase_auth_required
from backend.utils.audio_transcription import transcribe_audio_file
from backend.utils.entry_helpers import format_title_date_with_time

# Load environment variables
load_dotenv()
logger = get_logger(__name__)

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

        # Process content through OpenAI for better journal entry
        processed_content = process_text(transcription)
        
        # Get the next user entry ID using user context (keep as integer)
        user_entries_response = g.user_supabase.table('entries').select('user_entry_id').execute()
        user_entry_count = len(user_entries_response.data)
        next_user_entry_id = user_entry_count + 1
        
            # Format entry date with time: "Month DD, YYYY at h:MM AM/PM"
            # For in-app recordings, use the datetime from when audio was recorded
            # (frontend should send this, but for now use current time)
        recording_datetime = datetime.now()  # TODO: Get from request if frontend sends it
        title = format_title_date_with_time(recording_datetime)
            
        # Create composite primary key: user_id + user_entry_id
        user_and_entry_id = f"{g.current_user.id}_{next_user_entry_id}"

        # Prepare entry data
        entry_data = {
            'user_and_entry_id': user_and_entry_id,
            'user_id': g.current_user.id,
            'user_entry_id': next_user_entry_id,
            'title': title,
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

        logger.info("Audio entry created successfully", extra={"route": "/api/audio", "method": "POST", "user_id": g.current_user.id, "user_entry_id": next_user_entry_id, "title": title})

        return jsonify({
            'message': 'Audio processed and journal entry created successfully',
            'transcription': transcription,
            'entry': new_entry
        }), 200

    except Exception as e:
        logger.exception("Error processing audio", extra={"route": "/api/audio", "method": "POST", "user_id": g.current_user.id})
        return jsonify({'error': f'Audio processing failed: {str(e)}'}), 500 