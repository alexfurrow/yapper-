"""
Bulk audio upload routes for processing multiple voice note files.
Handles .m4a files with date extraction, transcription, and entry creation.
"""

from flask import Blueprint, request, jsonify, g
from werkzeug.utils import secure_filename
import os
import tempfile
from pathlib import Path
from datetime import datetime
from backend.routes.entries import supabase_auth_required
from backend.services.embedding import generate_embedding
from backend.services.initial_processing import process_text
from backend.utils.audio_transcription import transcribe_audio_file
from backend.utils.audio_metadata import infer_audio_entry_date
from backend.utils.entry_helpers import format_title_date_with_time, format_title_date_with_time_from_date, recalculate_user_entry_ids
from backend.utils.supabase_storage import store_audio_file_in_supabase
from backend.config.logging import get_logger
from typing import List, Dict

logger = get_logger(__name__)

# Create blueprint
audio_bulk_bp = Blueprint('audio_bulk', __name__, url_prefix='/api/audio')

# Allowed file extensions
ALLOWED_EXTENSIONS = {'m4a'}

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Maximum file size: 25MB (Whisper API limit)
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25MB

# Maximum files per batch
MAX_FILES_PER_BATCH = 10


@audio_bulk_bp.route('/bulk-upload', methods=['POST'])
@supabase_auth_required
def bulk_upload_audio():
    """
    Process multiple audio files and create journal entries.
    Accepts up to 10 .m4a files per batch.
    
    Process:
    1. Validate files (count, size, format)
    2. For each file:
       - Extract date from metadata/filename
       - Transcribe audio
       - Store audio file in Supabase Storage
       - Create journal entry with transcription
    3. Return results (successful and failed entries)
    """
    try:
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        if not files or all(f.filename == '' for f in files):
            return jsonify({'error': 'No files selected'}), 400
        
        # Validate file count
        valid_files = [f for f in files if f and f.filename and allowed_file(f.filename)]
        if len(valid_files) > MAX_FILES_PER_BATCH:
            return jsonify({
                'error': f'Too many files. Maximum {MAX_FILES_PER_BATCH} files per batch.'
            }), 400
        
        if not valid_files:
            return jsonify({'error': 'No valid .m4a files to process'}), 400
        
        logger.info(f"Processing {len(valid_files)} audio files for bulk upload", extra={
            "route": "/api/audio/bulk-upload",
            "method": "POST",
            "user_id": g.current_user.id
        })
        
        # Create temporary directory for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            created_entries = []
            failed_entries = []
            
            # Use temporary high IDs during creation to avoid conflicts
            # These will be recalculated at the end based on chronological order
            # Start from a high number (1000000) to ensure no conflicts with existing entries
            temp_id_start = 1000000
            next_user_entry_id = temp_id_start
            
            for file in valid_files:
                file_result = process_single_audio_file(
                    file=file,
                    temp_dir=temp_dir,
                    user_id=g.current_user.id,
                    user_supabase=g.user_supabase,
                    user_entry_id=next_user_entry_id
                )
                
                # Increment for next file
                if file_result['success']:
                    next_user_entry_id += 1
                
                if file_result['success']:
                    created_entries.append(file_result['entry_info'])
                else:
                    failed_entries.append({
                        'filename': file.filename,
                        'error': file_result['error']
                    })
            
            # Recalculate all user_entry_id values based on chronological order
            # This is the default process - ensures IDs are sequential (1, 2, 3, ...) ordered by created_at
            # Runs after every bulk upload to maintain chronological ordering
            logger.info(f"Recalculating entry IDs for user {g.current_user.id} after bulk audio upload (default process)")
            recalculation_result = recalculate_user_entry_ids(g.user_supabase, g.current_user.id)
            if not recalculation_result['success']:
                logger.warning(f"Failed to recalculate entry IDs: {recalculation_result.get('error')}")
            else:
                logger.info(f"Recalculated {recalculation_result['updated_count']} entry IDs")
            
            return jsonify({
                'message': 'Bulk audio upload processed',
                'created_count': len(created_entries),
                'failed_count': len(failed_entries),
                'created_entries': created_entries,
                'failed_entries': failed_entries
            }), 200
            
    except Exception as e:
        logger.exception("Error in bulk audio upload", extra={
            "route": "/api/audio/bulk-upload",
            "method": "POST",
            "user_id": g.current_user.id
        })
        return jsonify({'error': 'Internal server error'}), 500


def process_single_audio_file(
    file,
    temp_dir: str,
    user_id: str,
    user_supabase,
    user_entry_id: int
) -> Dict:
    """
    Process a single audio file: extract date, transcribe, store, create entry.
    
    Returns:
        Dict with 'success' (bool) and either 'entry_info' or 'error'
    """
    filename = secure_filename(file.filename)
    temp_path = os.path.join(temp_dir, filename)
    
    try:
        # Save file temporarily
        file.save(temp_path)
        
        # Validate file size
        file_size = os.path.getsize(temp_path)
        if file_size > MAX_FILE_SIZE:
            return {
                'success': False,
                'error': f'File too large: {file_size / (1024*1024):.1f}MB. Maximum size is {MAX_FILE_SIZE / (1024*1024):.0f}MB.'
            }
        
        # Extract date from audio file
        entry_datetime, date_source = infer_audio_entry_date(temp_path)
        
        if entry_datetime is None:
            # Use current datetime if no date found
            entry_datetime = datetime.now()
            date_source = "current_time_fallback"
            logger.warning(f"Could not extract date from {filename}, using current time", extra={
                "filename": filename,
                "user_id": user_id
            })
        
        # Transcribe audio
        transcription, error_msg = transcribe_audio_file(temp_path)
        if transcription is None:
            return {
                'success': False,
                'error': f'Transcription failed: {error_msg}'
            }
        
        # Process content through OpenAI
        processed_content = process_text(transcription)
        
        # Use the provided user_entry_id (calculated once before the loop)
        # Create composite primary key
        user_and_entry_id = f"{user_id}_{user_entry_id}"
        
        # Format title with time
        title = format_title_date_with_time(entry_datetime)
        
        # Store audio file in Supabase Storage
        storage_path, storage_error = store_audio_file_in_supabase(
            file_path=temp_path,
            user_id=user_id,
            user_and_entry_id=user_and_entry_id,
            supabase_client=user_supabase,
            original_filename=filename
        )
        
        if storage_path is None:
            logger.warning(f"Failed to store audio file, continuing without storage: {storage_error}", extra={
                "filename": filename,
                "user_id": user_id
            })
            # Continue without storage - entry will be created but audio file won't be stored
        
        # Generate embedding
        embedding = None
        if processed_content:
            embedding = generate_embedding(processed_content)
        
        # Prepare entry data
        entry_data = {
            'user_and_entry_id': user_and_entry_id,
            'user_entry_id': user_entry_id,
            'title': title,
            'content': transcription,
            'processed': processed_content,
            'created_at': entry_datetime.isoformat() if isinstance(entry_datetime, datetime) else None
        }
        
        if embedding:
            entry_data['vectors'] = embedding
        
        # Add audio file URL if storage was successful
        # Note: Not exposing to frontend yet, but storing in backend
        if storage_path:
            entry_data['audio_file_url'] = storage_path  # Store path, can generate URL later if needed
        
        # Create entry in database
        response = user_supabase.table('entries').insert(entry_data).execute()
        
        if response.data:
            logger.info(f"Created entry from audio file: {filename}", extra={
                "user_id": user_id,
                "user_entry_id": user_entry_id,
                "filename": filename
            })
            
            return {
                'success': True,
                'entry_info': {
                    'user_and_entry_id': response.data[0].get('user_and_entry_id'),
                    'user_entry_id': user_entry_id,
                    'title': title,
                    'filename': filename,
                    'date_source': date_source,
                    'has_audio_file': storage_path is not None
                }
            }
        else:
            return {
                'success': False,
                'error': 'Failed to save entry to database'
            }
            
    except Exception as e:
        logger.exception(f"Error processing audio file {filename}", extra={
            "filename": filename,
            "user_id": user_id
        })
        return {
            'success': False,
            'error': f'Processing error: {str(e)}'
        }

