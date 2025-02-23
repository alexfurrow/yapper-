from flask import Blueprint, request, jsonify
import os
from werkzeug.utils import secure_filename
import whisper

audio_bp = Blueprint('audio', __name__)

# Initialize Whisper model
model = whisper.load_model("base")

@audio_bp.route('/audio', methods=['POST'])
def upload_audio():
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

        # Transcribe the audio
        result = model.transcribe(temp_path, fp16=False) #CHANGE THIS TO TRUE, to save a lot of memory and speed up processing. do this once you migrate bc my cpu cant use this=True for some reason. 
        transcription = result["text"]

        # Clean up the temporary file
        os.remove(temp_path)

        return jsonify({
            'message': 'Audio processed successfully',
            'transcription': transcription
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500 