"""
Bulk upload service for processing multiple journal entries from files.
Handles text extraction, transcription, and entry creation.
"""

import os
import secrets
import string
from typing import Dict, List, Optional
from pathlib import Path
import logging
from backend.utils.audio_transcription import transcribe_audio_file

logger = logging.getLogger(__name__)

class BulkUploadService:
    """Service for handling bulk upload of journal entries."""
    
    def __init__(self):
        self.supported_extensions = ['.txt', '.doc', '.docx', '.m4a']
    
    def extract_text_from_file(self, file_path: str, skip_transcription: bool = False) -> str:
        """Extract text content from various file types."""
        try:
            file_ext = Path(file_path).suffix.lower()
            
            if file_ext == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            elif file_ext == '.docx':
                # Parse .docx files using python-docx
                try:
                    from docx import Document
                    doc = Document(file_path)
                    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
                    content = '\n'.join(paragraphs)
                    if not content:
                        logger.warning(f"No text content found in .docx file: {file_path}")
                    return content
                except ImportError:
                    logger.error("python-docx library not installed. Cannot parse .docx files.")
                    return ""
                except Exception as e:
                    logger.error(f"Error parsing .docx file {file_path}: {e}")
                    return ""
            elif file_ext == '.doc':
                # .doc files are older format, harder to parse
                # For now, return error message
                logger.warning(f".doc files (not .docx) are not fully supported. File: {file_path}")
                return f"[DOC FILE: {Path(file_path).name} - .doc format not fully supported, please convert to .docx]"
            elif file_ext == '.m4a':
                # For preview mode, skip transcription (too slow)
                if skip_transcription:
                    return f"[Audio file: {Path(file_path).name} - Transcription will occur during entry creation]"
                
                # Transcribe audio file
                logger.info(f"Starting transcription for {Path(file_path).name}")
                transcription, error_msg = transcribe_audio_file(file_path)
                if transcription:
                    logger.info(f"Transcription successful for {Path(file_path).name}, length: {len(transcription)}")
                    return transcription
                else:
                    logger.error(f"Failed to transcribe audio file {file_path}: {error_msg}")
                    return ""
            else:
                logger.warning(f"Unsupported file type: {file_ext}")
                return ""
                
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            return ""
    
    def generate_bulk_upload_id(self) -> str:
        """Generate a unique 8-character ID in format xxxx-xxxx for bulk upload entries."""
        # Generate 8 characters, split into xxxx-xxxx format
        id_chars = ''.join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(8))
        return f"{id_chars[:4]}-{id_chars[4:]}"
    
    def process_uploaded_file(self, file_path: str, user_id: str, skip_transcription: bool = False) -> Dict:
        """
        Process a single uploaded file and return entry data.
        Returns dict with entry info or error details.
        
        Args:
            file_path: Path to the file
            user_id: User ID
            skip_transcription: If True, skip transcription for audio files
        """
        try:
            # Extract text content
            content = self.extract_text_from_file(file_path, skip_transcription=skip_transcription)
            if not content.strip():
                return {
                    'success': False,
                    'error': 'No content found in file',
                    'filename': Path(file_path).name
                }
            
            # Generate unique ID for bulk upload entry title
            unique_id = self.generate_bulk_upload_id()
            title = f"ID:{unique_id}"
            
            logger.info(f"Processed file {Path(file_path).name}, generated title: {title}")
            
            return {
                'success': True,
                'filename': Path(file_path).name,
                'content': content,
                'title': title,
                'content_length': len(content)
            }
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            return {
                'success': False,
                'error': str(e),
                'filename': Path(file_path).name
            }
    
    def process_multiple_files(self, file_paths: List[str], user_id: str, skip_transcription: bool = False) -> Dict:
        """
        Process multiple files and return results.
        
        Args:
            file_paths: List of file paths to process
            user_id: User ID
            skip_transcription: If True, skip transcription for audio files (faster preview)
        """
        results = {
            'successful': [],
            'failed': [],
            'total_files': len(file_paths),
            'summary': {}
        }
        
        for file_path in file_paths:
            result = self.process_uploaded_file(file_path, user_id, skip_transcription=skip_transcription)
            
            if result['success']:
                results['successful'].append(result)
            else:
                results['failed'].append(result)
        
        results['summary'] = {
            'successful_count': len(results['successful']),
            'failed_count': len(results['failed']),
            'success_rate': len(results['successful']) / len(file_paths) if file_paths else 0
        }
        
        return results

# Global instance
bulk_upload_service = BulkUploadService()
