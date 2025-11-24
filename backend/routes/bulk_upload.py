"""
Bulk upload routes for processing multiple journal entries from files.
"""

from flask import Blueprint, request, jsonify, g
from werkzeug.utils import secure_filename
import os
import tempfile
from pathlib import Path
from backend.services.bulk_upload import bulk_upload_service
from backend.routes.entries import supabase_auth_required, create_user_supabase_client
from backend.services.embedding import generate_embedding
from backend.services.initial_processing import process_text
from backend.utils.entry_helpers import recalculate_user_entry_ids, format_title_date_only
from backend.utils.excel_parser import parse_excel_mapping
from backend.utils.audio_transcription import transcribe_audio_file
from backend.utils.supabase_storage import store_audio_file_in_supabase
from supabase import create_client
import logging

logger = logging.getLogger(__name__)

# Create blueprint
bulk_upload_bp = Blueprint('bulk_upload', __name__)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'txt', 'doc', 'docx', 'm4a'}
ALLOWED_EXCEL_EXTENSIONS = {'xlsx', 'xls', 'csv'}

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_excel_file(filename):
    """Check if file is an Excel file."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXCEL_EXTENSIONS

@bulk_upload_bp.route('/bulk-upload/process', methods=['POST'])
@supabase_auth_required
def process_bulk_upload():
    """
    Process uploaded files for bulk entry creation.
    Expects files in request.files
    """
    try:
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        if not files or all(f.filename == '' for f in files):
            return jsonify({'error': 'No files selected'}), 400
        
        # Create temporary directory for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            file_paths = []
            
            # Save uploaded files to temp directory
            for file in files:
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(temp_dir, filename)
                    file.save(file_path)
                    file_paths.append(file_path)
                else:
                    logger.warning(f"Skipping invalid file: {file.filename if file else 'None'}")
            
            if not file_paths:
                return jsonify({'error': 'No valid files to process'}), 400
            
            # Process files
            results = bulk_upload_service.process_multiple_files(file_paths, g.current_user.id)
            
            return jsonify({
                'message': 'Files processed successfully',
                'results': results
            }), 200
            
    except Exception as e:
        logger.exception("Error in bulk upload processing")
        return jsonify({'error': 'Internal server error'}), 500

@bulk_upload_bp.route('/bulk-upload/create-entries', methods=['POST'])
@supabase_auth_required
def create_bulk_entries():
    """
    Create journal entries from uploaded files.
    Accepts files directly and processes them (with transcription for audio files).
    """
    try:
        logger.info("Bulk upload create-entries endpoint called", extra={
            "user_id": g.current_user.id,
            "has_files": 'files' in request.files
        })
        
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        if not files or all(f.filename == '' for f in files):
            return jsonify({'error': 'No files selected'}), 400
        
        created_entries = []
        failed_entries = []
        
        # Use temporary high IDs during creation to avoid conflicts
        # These will be recalculated at the end based on chronological order
        # Start from a high number (1000000) to ensure no conflicts with existing entries
        temp_id_start = 1000000
        next_user_entry_id = temp_id_start
        
        # Create temporary directory for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            file_paths = []
            
            # Save uploaded files to temp directory
            for file in files:
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(temp_dir, filename)
                    file.save(file_path)
                    file_paths.append(file_path)
            
            if not file_paths:
                return jsonify({'error': 'No valid files to process'}), 400
            
            # Process files WITH transcription (skip_transcription=False)
            processed_results = bulk_upload_service.process_multiple_files(
                file_paths, 
                g.current_user.id, 
                skip_transcription=False  # Enable transcription for audio files
            )
            
            # Create entries from processed results
            for entry_data in processed_results['successful']:
                try:
                    # Validate required fields
                    if not all(key in entry_data for key in ['content', 'title']):
                        failed_entries.append({
                            'error': 'Missing required fields',
                            'data': entry_data
                        })
                        continue
                    
                    # Process content through OpenAI
                    processed_content = process_text(entry_data['content'])
                    
                    # Generate embedding
                    embedding = None
                    if processed_content:
                        embedding = generate_embedding(processed_content)
                    
                    # Use the current next_user_entry_id and increment for next iteration
                    current_user_entry_id = next_user_entry_id
                    next_user_entry_id += 1
                    
                    # Create composite primary key: user_id + user_entry_id
                    user_and_entry_id = f"{g.current_user.id}_{current_user_entry_id}"
                    
                    # Use current time for created_at (bulk upload entries)
                    from datetime import datetime
                    created_at = datetime.now().isoformat()
                    
                    # Store audio file in Supabase Storage if it's an audio file
                    storage_path = None
                    file_ext = Path(entry_data.get('filename', '')).suffix.lower()
                    if file_ext == '.m4a':
                        # Find the corresponding file path
                        original_file_path = None
                        for fp in file_paths:
                            if Path(fp).name == entry_data.get('filename'):
                                original_file_path = fp
                                break
                        
                        if original_file_path and os.path.exists(original_file_path):
                            from backend.utils.supabase_storage import store_audio_file_in_supabase
                            storage_path, storage_error = store_audio_file_in_supabase(
                                file_path=original_file_path,
                                user_id=g.current_user.id,
                                user_and_entry_id=user_and_entry_id,
                                supabase_client=g.user_supabase,
                                original_filename=entry_data.get('filename')
                            )
                            if storage_error:
                                logger.warning(f"Failed to store audio file: {storage_error}")
                    
                    # Prepare entry data
                    entry_record = {
                        'user_and_entry_id': user_and_entry_id,  # Composite primary key
                        'user_entry_id': current_user_entry_id,  # Keep as integer
                        'title': entry_data['title'],  # Format: "ID:xxxx-xxxx"
                        'content': entry_data['content'],
                        'processed': processed_content,
                        'created_at': created_at,
                        'vectors': embedding
                    }
                    
                    # Add audio file URL if storage was successful
                    if storage_path:
                        entry_record['audio_file_url'] = storage_path
                    
                    # Save to database
                    response = g.user_supabase.table('entries').insert(entry_record).execute()
                    
                    if response.data:
                        created_entries.append({
                            'user_and_entry_id': response.data[0].get('user_and_entry_id'),
                            'user_entry_id': current_user_entry_id,
                            'title': entry_data['title'],
                            'filename': entry_data.get('filename', 'unknown')
                        })
                    else:
                        failed_entries.append({
                            'error': 'Failed to save to database',
                            'data': entry_data
                        })
                        
                except Exception as e:
                    logger.error(f"Error creating entry: {e}")
                    failed_entries.append({
                        'error': str(e),
                        'data': entry_data
                    })
            
            # Handle failed file processing
            for failed_result in processed_results['failed']:
                failed_entries.append({
                    'error': failed_result.get('error', 'Unknown error'),
                    'filename': failed_result.get('filename', 'unknown')
                })
        
        # Recalculate all user_entry_id values based on chronological order
        # This is the default process - ensures IDs are sequential (1, 2, 3, ...) ordered by created_at
        # Runs after every bulk upload to maintain chronological ordering
        logger.info(f"Recalculating entry IDs for user {g.current_user.id} after bulk upload (default process)")
        recalculation_result = recalculate_user_entry_ids(g.user_supabase, g.current_user.id)
        if not recalculation_result['success']:
            logger.warning(f"Failed to recalculate entry IDs: {recalculation_result.get('error')}")
        else:
            logger.info(f"Recalculated {recalculation_result['updated_count']} entry IDs")
        
        return jsonify({
            'message': 'Bulk entries processed',
            'created_count': len(created_entries),
            'failed_count': len(failed_entries),
            'created_entries': created_entries,
            'failed_entries': failed_entries
        }), 200
        
    except Exception as e:
        logger.exception("Error creating bulk entries", extra={
            "error": str(e),
            "error_type": type(e).__name__
        })
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@bulk_upload_bp.route('/bulk-upload/preview', methods=['POST'])
@supabase_auth_required
def preview_bulk_upload():
    """
    Preview uploaded files without creating entries.
    Returns processed file data for review.
    """
    try:
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files')
        if not files or all(f.filename == '' for f in files):
            return jsonify({'error': 'No files selected'}), 400
        
        # Create temporary directory for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            file_paths = []
            
            # Save uploaded files to temp directory
            for file in files:
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(temp_dir, filename)
                    file.save(file_path)
                    file_paths.append(file_path)
            
            if not file_paths:
                return jsonify({'error': 'No valid files to process'}), 400
            
            # Process files for preview (skip transcription for audio files to make it faster)
            results = bulk_upload_service.process_multiple_files(file_paths, g.current_user.id, skip_transcription=True)
            
            # Return preview data (without creating entries)
            return jsonify({
                'message': 'Files processed for preview',
                'preview_data': results,
                'ready_for_creation': len(results['successful']) > 0
            }), 200
            
    except Exception as e:
        logger.exception("Error in bulk upload preview")
        return jsonify({'error': 'Internal server error'}), 500

@bulk_upload_bp.route('/bulk-upload/excel-files', methods=['POST'])
@supabase_auth_required
def create_entries_from_excel_and_files():
    """
    Create journal entries from Excel spreadsheet mapping and files (audio, text, or documents).
    
    Expects:
    - 'spreadsheet': Excel file (.xlsx or .xls) with filename and date columns
    - 'files': Files (.m4a, .txt, .doc, .docx) matching the filenames in spreadsheet
    
    Process:
    1. Parse Excel to get filename->date mapping
    2. Validate file count matches spreadsheet rows
    3. Validate filenames match spreadsheet
    4. For audio files: transcribe in sequence and upload to Supabase Storage
    5. For text/doc files: extract text content
    6. Create entries with titles from spreadsheet (date only, no time)
    """
    try:
        logger.info("Excel-files bulk upload endpoint called", extra={
            "user_id": g.current_user.id,
            "has_spreadsheet": 'spreadsheet' in request.files,
            "has_files": 'files' in request.files,
            "request_method": request.method,
            "content_type": request.content_type
        })
        
        # Check for spreadsheet
        if 'spreadsheet' not in request.files:
            logger.warning("No spreadsheet in request.files", extra={
                "available_keys": list(request.files.keys()) if request.files else []
            })
            return jsonify({'error': 'No spreadsheet provided'}), 400
        
        spreadsheet_file = request.files['spreadsheet']
        if not spreadsheet_file or not spreadsheet_file.filename:
            return jsonify({'error': 'Spreadsheet file is required'}), 400
        
        if not allowed_excel_file(spreadsheet_file.filename):
            return jsonify({'error': 'Spreadsheet must be .xlsx, .xls, or .csv file'}), 400
        
        # Check for files (audio, text, or documents)
        if 'files' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        uploaded_files = request.files.getlist('files')
        # Filter to only allowed file types: .m4a, .txt, .doc, .docx
        valid_files = [f for f in uploaded_files if f and f.filename and allowed_file(f.filename)]
        
        if not valid_files:
            return jsonify({'error': 'No valid files provided. Supported: .m4a, .txt, .doc, .docx'}), 400
        
        created_entries = []
        failed_entries = []
        
        # Use temporary high IDs during creation
        temp_id_start = 1000000
        next_user_entry_id = temp_id_start
        
        # Create temporary directory for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save and parse spreadsheet
            spreadsheet_path = os.path.join(temp_dir, secure_filename(spreadsheet_file.filename))
            spreadsheet_file.save(spreadsheet_path)
            
            filename_date_mapping, excel_error = parse_excel_mapping(spreadsheet_path)
            if excel_error:
                return jsonify({'error': f'Error parsing spreadsheet: {excel_error}'}), 400
            
            if not filename_date_mapping:
                return jsonify({'error': 'No valid filename-date pairs found in spreadsheet'}), 400
            
            logger.info(f"Parsed {len(filename_date_mapping)} filename-date pairs from spreadsheet")
            
            # Validation 1: Check file count matches
            if len(valid_files) != len(filename_date_mapping):
                return jsonify({
                    'error': f'File count mismatch: {len(valid_files)} files uploaded, but {len(filename_date_mapping)} entries in spreadsheet'
                }), 400
            
            # Save files and create mapping
            file_map = {}  # {filename_without_ext: (file_path, file_extension)}
            uploaded_filenames = []  # Track uploaded filenames for sorting
            for uploaded_file in valid_files:
                original_filename = uploaded_file.filename
                filename = secure_filename(original_filename)
                file_path = os.path.join(temp_dir, filename)
                uploaded_file.save(file_path)
                
                # Get filename without extension for matching
                # Use original filename for matching (before secure_filename processing)
                # to match against Excel which may have different formatting
                original_no_ext = Path(original_filename).stem.strip()
                secure_no_ext = Path(filename).stem.strip()
                
                # Store both versions in the map for flexible matching
                file_ext = Path(original_filename).suffix.lower()
                file_map[original_no_ext] = (file_path, file_ext)
                file_map[secure_no_ext] = (file_path, file_ext)  # Also store secure version
                uploaded_filenames.append(original_no_ext)
                
                logger.debug(f"Uploaded file: original='{original_filename}' -> no_ext='{original_no_ext}', secure='{filename}' -> no_ext='{secure_no_ext}'")
            
            # Sort both lists for consistent matching
            excel_filenames_sorted = sorted(filename_date_mapping.keys())
            uploaded_filenames_sorted = sorted(uploaded_filenames)
            
            logger.info(f"Excel filenames (sorted, first 10): {excel_filenames_sorted[:10]}")
            logger.info(f"Uploaded filenames (sorted, first 10): {uploaded_filenames_sorted[:10]}")
            logger.info(f"File map keys (first 10): {list(file_map.keys())[:10]}")
            
            # Validation 2: Check filenames match (using sorted lists)
            missing_files = []
            extra_files = []
            
            # Check for files in Excel that aren't uploaded
            for excel_filename in excel_filenames_sorted:
                if excel_filename not in file_map:
                    missing_files.append(excel_filename)
            
            # Check for uploaded files that aren't in Excel
            for uploaded_filename in uploaded_filenames_sorted:
                if uploaded_filename not in filename_date_mapping:
                    extra_files.append(uploaded_filename)
            
            if missing_files:
                return jsonify({
                    'error': f'Filenames in spreadsheet do not match uploaded files. Missing: {", ".join(missing_files[:5])}'
                }), 400
            
            if extra_files:
                return jsonify({
                    'error': f'Uploaded files not found in spreadsheet: {", ".join(extra_files[:5])}'
                }), 400
            
            # Store original token for refreshing
            original_token = request.headers.get('Authorization', '').replace('Bearer ', '')
            
            # Helper function to refresh Supabase client if token expired
            def refresh_supabase_client_if_needed():
                """Refresh the Supabase client if the token has expired"""
                try:
                    # Try a simple operation to check if token is still valid
                    test_response = g.user_supabase.table('entries').select('user_entry_id').limit(1).execute()
                    return g.user_supabase
                except Exception as e:
                    error_str = str(e)
                    if 'JWT expired' in error_str or 'PGRST303' in error_str:
                        logger.warning("JWT token expired, attempting to refresh...")
                        # Try to get a new token from the request (frontend should refresh it)
                        # For now, recreate client with original token and hope frontend refreshed it
                        # In production, you might want to return an error asking frontend to retry
                        try:
                            # Recreate client - this won't help if token is expired, but worth trying
                            new_client = create_user_supabase_client(original_token)
                            g.user_supabase = new_client
                            return new_client
                        except Exception as refresh_error:
                            logger.error(f"Failed to refresh Supabase client: {refresh_error}")
                            raise Exception("JWT token expired and could not be refreshed. Please retry the upload.")
                    else:
                        # Some other error, re-raise it
                        raise
            
            # Process each file in sequence (sorted by filename for consistency)
            sorted_mapping = sorted(filename_date_mapping.items())
            for idx, (excel_filename, date_str) in enumerate(sorted_mapping, start=1):
                try:
                    # Refresh client every 5 files to prevent token expiration
                    if idx % 5 == 0:
                        logger.info(f"Refreshing Supabase client after {idx} files processed")
                        refresh_supabase_client_if_needed()
                    
                    file_path, file_ext = file_map[excel_filename]
                    
                    # Extract content based on file type
                    if file_ext == '.m4a':
                        # Transcribe audio file
                        logger.info(f"Transcribing audio file: {excel_filename}")
                        content, error_msg = transcribe_audio_file(file_path)
                        if not content:
                            failed_entries.append({
                                'error': f'Transcription failed: {error_msg}',
                                'filename': excel_filename
                            })
                            continue
                        logger.info(f"Transcription successful for {excel_filename}, length: {len(content)}")
                    else:
                        # Extract text from text/doc files
                        logger.info(f"Extracting text from {file_ext} file: {excel_filename}")
                        content = bulk_upload_service.extract_text_from_file(file_path, skip_transcription=False)
                        if not content or not content.strip():
                            failed_entries.append({
                                'error': 'No content found in file',
                                'filename': excel_filename
                            })
                            continue
                        logger.info(f"Text extraction successful for {excel_filename}, length: {len(content)}")
                    
                    # Process content through OpenAI
                    processed_content = process_text(content)
                    
                    # Generate embedding
                    embedding = None
                    if processed_content:
                        embedding = generate_embedding(processed_content)
                    
                    # Use current next_user_entry_id and increment
                    current_user_entry_id = next_user_entry_id
                    next_user_entry_id += 1
                    
                    # Create composite primary key
                    user_and_entry_id = f"{g.current_user.id}_{current_user_entry_id}"
                    
                    # Format title from spreadsheet date (date only, no time)
                    title = format_title_date_only(date_str)
                    
                    # Store audio file in Supabase Storage (only for .m4a files)
                    storage_path = None
                    storage_error = None
                    if file_ext == '.m4a':
                        try:
                            # Refresh client before storage operation
                            refresh_supabase_client_if_needed()
                            storage_path, storage_error = store_audio_file_in_supabase(
                                file_path=file_path,
                                user_id=g.current_user.id,
                                user_and_entry_id=user_and_entry_id,
                                supabase_client=g.user_supabase,
                                original_filename=Path(file_path).name
                            )
                            if storage_error:
                                logger.warning(f"Failed to store audio file {excel_filename}: {storage_error}")
                        except Exception as e:
                            logger.error(f"Error storing audio file {excel_filename}: {e}")
                    
                    # Prepare entry data
                    entry_record = {
                        'user_and_entry_id': user_and_entry_id,
                        'user_entry_id': current_user_entry_id,
                        'title': title,  # Date from spreadsheet
                        'content': content,
                        'processed': processed_content,
                        'vectors': embedding
                    }
                    
                    # Add audio file URL if storage was successful
                    if storage_path:
                        entry_record['audio_file_url'] = storage_path
                    
                    # Refresh client before database insert (critical operation)
                    refresh_supabase_client_if_needed()
                    
                    # Save to database with retry logic for JWT expiration
                    try:
                        response = g.user_supabase.table('entries').insert(entry_record).execute()
                    except Exception as db_error:
                        error_str = str(db_error)
                        if 'JWT expired' in error_str or 'PGRST303' in error_str:
                            # Try refreshing and retry once
                            logger.warning(f"JWT expired during insert for {excel_filename}, attempting refresh and retry...")
                            try:
                                refresh_supabase_client_if_needed()
                                response = g.user_supabase.table('entries').insert(entry_record).execute()
                            except Exception as retry_error:
                                logger.error(f"Retry failed for {excel_filename}: {retry_error}")
                                failed_entries.append({
                                    'error': f'JWT expired: {str(retry_error)}',
                                    'filename': excel_filename
                                })
                                continue
                        else:
                            # Some other database error
                            raise
                    
                    if response.data:
                        created_entries.append({
                            'user_and_entry_id': response.data[0].get('user_and_entry_id'),
                            'user_entry_id': current_user_entry_id,
                            'title': title,
                            'filename': excel_filename
                        })
                        logger.info(f"Successfully created entry for {excel_filename} with title: {title}")
                    else:
                        failed_entries.append({
                            'error': 'Failed to save to database',
                            'filename': excel_filename
                        })
                        
                except Exception as e:
                    logger.exception(f"Error processing file {excel_filename}: {e}")
                    error_str = str(e)
                    if 'JWT expired' in error_str or 'PGRST303' in error_str:
                        failed_entries.append({
                            'error': 'JWT token expired during processing. Please retry the upload.',
                            'filename': excel_filename
                        })
                    else:
                        failed_entries.append({
                            'error': str(e),
                            'filename': excel_filename
                        })
        
        # Recalculate all user_entry_id values based on chronological order
        logger.info(f"Recalculating entry IDs for user {g.current_user.id} after Excel-files bulk upload")
        recalculation_result = recalculate_user_entry_ids(g.user_supabase, g.current_user.id)
        if not recalculation_result['success']:
            logger.warning(f"Failed to recalculate entry IDs: {recalculation_result.get('error')}")
        else:
            logger.info(f"Recalculated {recalculation_result['updated_count']} entry IDs")
        
        return jsonify({
            'message': 'Excel-files bulk upload processed',
            'created_count': len(created_entries),
            'failed_count': len(failed_entries),
            'created_entries': created_entries,
            'failed_entries': failed_entries
        }), 200
        
    except Exception as e:
        logger.exception("Error in Excel-files bulk upload", extra={
            "error": str(e),
            "error_type": type(e).__name__
        })
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500
