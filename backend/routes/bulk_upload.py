"""
Bulk upload routes for processing multiple journal entries from files.
"""

from flask import Blueprint, request, jsonify, g
from werkzeug.utils import secure_filename
import os
import tempfile
from backend.services.bulk_upload import bulk_upload_service
from backend.routes.entries import supabase_auth_required
from backend.services.embedding import generate_embedding
from backend.services.initial_processing import process_text
import logging

logger = logging.getLogger(__name__)

# Create blueprint
bulk_upload_bp = Blueprint('bulk_upload', __name__)

# Allowed file extensions
ALLOWED_EXTENSIONS = {'txt', 'doc', 'docx'}

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
    Create journal entries from processed file data.
    Expects JSON with entry data array.
    """
    try:
        data = request.get_json()
        
        if not data or 'entries' not in data:
            return jsonify({'error': 'No entry data provided'}), 400
        
        entries_data = data['entries']
        if not isinstance(entries_data, list):
            return jsonify({'error': 'Entries must be an array'}), 400
        
        created_entries = []
        failed_entries = []
        
        for entry_data in entries_data:
            try:
                # Validate required fields
                if not all(key in entry_data for key in ['content', 'entry_date', 'date_string', 'title_date']):
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
                
                # Get the next user entry ID using user context (keep as integer)
                user_entries_response = g.user_supabase.table('entries').select('user_entry_id').execute()
                user_entry_count = len(user_entries_response.data)
                next_user_entry_id = user_entry_count + 1
                
                # Create composite primary key: user_id + user_entry_id
                user_and_entry_id = f"{g.current_user.id}_{next_user_entry_id}"
                
                # Handle date - could be string (from frontend) or date object
                entry_date = entry_data['entry_date']
                if isinstance(entry_date, str):
                    # Already a string, use directly
                    created_at = entry_date
                else:
                    # Date object, convert to ISO string
                    created_at = entry_date.isoformat()
                
                # Prepare entry data
                entry_record = {
                    'user_and_entry_id': user_and_entry_id,  # Composite primary key
                    'user_entry_id': next_user_entry_id,  # Keep as integer
                    'title_date': entry_data['title_date'],  # Use "Month DD, YYYY" format
                    'content': entry_data['content'],
                    'processed': processed_content,
                    'created_at': created_at,
                    'vectors': embedding
                }
                
                # Save to database
                response = g.user_supabase.table('entries').insert(entry_record).execute()
                
                if response.data:
                    created_entries.append({
                        'user_and_entry_id': response.data[0].get('user_and_entry_id'),
                        'user_entry_id': next_user_entry_id,
                        'title_date': entry_data['title_date'],
                        'date_string': entry_data['date_string'],  # For display
                        'date_source': entry_data.get('date_source', 'unknown'),
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
        
        return jsonify({
            'message': 'Bulk entries processed',
            'created_count': len(created_entries),
            'failed_count': len(failed_entries),
            'created_entries': created_entries,
            'failed_entries': failed_entries
        }), 200
        
    except Exception as e:
        logger.exception("Error creating bulk entries")
        return jsonify({'error': 'Internal server error'}), 500

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
            
            # Process files for preview
            results = bulk_upload_service.process_multiple_files(file_paths, g.current_user.id)
            
            # Serialize date objects to strings for JSON
            for entry in results['successful']:
                if 'entry_date' in entry and entry['entry_date']:
                    entry['entry_date'] = entry['entry_date'].isoformat()
            
            # Return preview data (without creating entries)
            return jsonify({
                'message': 'Files processed for preview',
                'preview_data': results,
                'ready_for_creation': len(results['successful']) > 0
            }), 200
            
    except Exception as e:
        logger.exception("Error in bulk upload preview")
        return jsonify({'error': 'Internal server error'}), 500
