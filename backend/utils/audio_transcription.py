"""
Audio transcription utility using OpenAI Whisper API.
Can be used by both single audio upload and bulk upload routes.
"""

import os
import requests
from typing import Optional, Tuple
from backend.config.logging import get_logger

logger = get_logger(__name__)

def transcribe_audio_file(file_path: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Transcribe an audio file using OpenAI Whisper API.
    
    Args:
        file_path: Path to the audio file to transcribe
        
    Returns:
        Tuple of (transcription_text, error_message)
        If successful: (text, None)
        If failed: (None, error_message)
    """
    try:
        # Get API key from environment variable
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            error_msg = 'OpenAI API key not configured'
            logger.error(error_msg)
            return None, error_msg

        # Call OpenAI's Whisper API
        with open(file_path, 'rb') as audio_data:
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

        # Process the API response
        if response.status_code == 200:
            result = response.json()
            transcription = result.get('text', '').strip()
            
            if not transcription:
                error_msg = 'No speech detected in audio file'
                logger.warning(error_msg)
                return None, error_msg

            logger.info(f"Audio transcription successful, length: {len(transcription)}")
            return transcription, None
        else:
            error_msg = f'Audio processing failed: {response.status_code} - {response.text}'
            logger.error(error_msg)
            return None, error_msg

    except Exception as e:
        error_msg = f'Audio transcription error: {str(e)}'
        logger.exception(error_msg)
        return None, error_msg

