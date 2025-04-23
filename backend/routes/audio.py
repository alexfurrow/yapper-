from flask import Blueprint, request, jsonify
import os
from werkzeug.utils import secure_filename
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

audio_bp = Blueprint('audio', __name__, url_prefix='/audio')

@audio_bp.route('/api_call', methods=['POST'])
def upload_audio_api():
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file'}), 400

        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        # Save the audio file temporarily
        filename = secure_filename(audio_file.filename)
        temp_path = os.path.join('temp', filename)
        os.makedirs('temp', exist_ok=True)
        audio_file.save(temp_path)

        # Get API key from environment variable
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            return jsonify({'error': 'API key not configured'}), 500

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
            transcription = result.get('text', '')
            return jsonify({
                'message': 'Audio processed successfully via API',
                'transcription': transcription
            }), 200
        else:
            return jsonify({
                'error': f'API error: {response.status_code}',
                'details': response.text
            }), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500 