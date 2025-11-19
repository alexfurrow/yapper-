"""
Supabase Storage utilities for storing audio files.
"""

import os
from typing import Optional, Tuple
from backend.config.logging import get_logger

logger = get_logger(__name__)

def store_audio_file_in_supabase(
    file_path: str,
    user_id: str,
    user_and_entry_id: str,
    supabase_client,
    original_filename: Optional[str] = None
) -> Tuple[Optional[str], Optional[str]]:
    """
    Store an audio file in Supabase Storage bucket 'voice_notes'.
    
    Path structure: {user_id}/{user_and_entry_id}/voice_note.m4a
    
    Args:
        file_path: Local path to the audio file to upload
        user_id: User ID for the path
        user_and_entry_id: Entry ID for the path
        supabase_client: Authenticated Supabase client
        original_filename: Optional original filename (for extension)
        
    Returns:
        Tuple of (storage_path, error_message)
        If successful: (storage_path, None)
        If failed: (None, error_message)
    """
    try:
        # Determine file extension
        if original_filename:
            file_ext = os.path.splitext(original_filename)[1] or '.m4a'
        else:
            file_ext = os.path.splitext(file_path)[1] or '.m4a'
        
        # Construct storage path
        storage_path = f"{user_id}/{user_and_entry_id}/voice_note{file_ext}"
        
        # Read file content
        with open(file_path, 'rb') as f:
            file_content = f.read()
        
        # Upload to Supabase Storage
        # Note: Bucket 'voice_notes' should be created in Supabase dashboard
        # TODO: When moving to user-specific storage, update this path structure
        response = supabase_client.storage.from_('voice_notes').upload(
            path=storage_path,
            file=file_content,
            file_options={
                'content-type': f'audio/{file_ext[1:]}',  # e.g., 'audio/m4a'
                'upsert': False  # Don't overwrite existing files
            }
        )
        
        if response:
            # Get public URL (if bucket is public) or signed URL
            # For now, return the path - can generate signed URL if needed
            logger.info(f"Audio file stored successfully: {storage_path}")
            return storage_path, None
        else:
            error_msg = "Failed to upload file to Supabase Storage"
            logger.error(error_msg)
            return None, error_msg
            
    except Exception as e:
        error_msg = f"Error storing audio file: {str(e)}"
        logger.exception(error_msg)
        return None, error_msg


def get_audio_file_url(storage_path: str, supabase_client, signed: bool = False) -> Optional[str]:
    """
    Get URL for an audio file stored in Supabase Storage.
    
    Args:
        storage_path: Path to the file in storage (e.g., "user_id/entry_id/voice_note.m4a")
        supabase_client: Authenticated Supabase client
        signed: Whether to generate a signed URL (for private buckets)
        
    Returns:
        URL string if successful, None otherwise
    """
    try:
        if signed:
            # Generate signed URL (valid for 1 hour by default)
            response = supabase_client.storage.from_('voice_notes').create_signed_url(
                path=storage_path,
                expires_in=3600  # 1 hour
            )
            return response.get('signedURL') if response else None
        else:
            # Get public URL
            response = supabase_client.storage.from_('voice_notes').get_public_url(
                path=storage_path
            )
            return response if response else None
    except Exception as e:
        logger.error(f"Error getting audio file URL: {str(e)}")
        return None

