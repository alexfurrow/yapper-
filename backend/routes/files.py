# This is for bulk file upload (text from online journal for instance)

# from flask import Blueprint, request, jsonify
# import os
# from werkzeug.utils import secure_filename
# import docx
# import tempfile

# files_bp = Blueprint('files', __name__)

# @files_bp.route('/files/upload', methods=['POST'])
# def upload_file():
#     try:
#         if 'file' not in request.files:
#             return jsonify({'error': 'No file part'}), 400

#         file = request.files['file']
#         if file.filename == '':
#             return jsonify({'error': 'No selected file'}), 400

#         # Get file extension
#         filename = secure_filename(file.filename)
#         file_ext = os.path.splitext(filename)[1].lower()

#         # Create temp directory if it doesn't exist
#         os.makedirs('temp', exist_ok=True)
#         temp_path = os.path.join('temp', filename)
        
#         # Save file temporarily
#         file.save(temp_path)
        
#         # Extract content based on file type
#         content = ""
#         if file_ext == '.txt':
#             with open(temp_path, 'r', encoding='utf-8') as f:
#                 content = f.read()
#         elif file_ext == '.docx':
#             doc = docx.Document(temp_path)
#             content = "\n".join([para.text for para in doc.paragraphs])
#         else:
#             os.remove(temp_path)
#             return jsonify({'error': 'Unsupported file format'}), 400
        
#         # Clean up
#         os.remove(temp_path)
        
#         return jsonify({
#             'message': 'File processed successfully',
#             'content': content
#         }), 200

#     except Exception as e:
#         return jsonify({'error': str(e)}), 500 