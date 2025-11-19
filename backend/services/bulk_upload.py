"""
Bulk upload service for processing multiple journal entries from files.
Handles text extraction, date inference, and entry creation.
"""

import os
import re
import json
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class BulkUploadService:
    """Service for handling bulk upload of journal entries."""
    
    def __init__(self):
        self.supported_extensions = ['.txt', '.doc', '.docx', '.m4a']
        self.date_patterns = [
            # File name patterns
            r'(\d{1,2})[\.\-/](\d{1,2})[\.\-/](\d{2,4})',  # 10.5.25, 10-5-25, 10/5/25
            r'(\d{4})[\.\-/](\d{1,2})[\.\-/](\d{1,2})',     # 2025.10.5, 2025-10-5, 2025/10/5
            r'(\d{1,2})[\.\-/](\d{1,2})[\.\-/](\d{4})',      # 10.5.2025, 10-5-2025, 10/5/2025
            
            # Content patterns
            r'entry\s+from\s+(\d{1,2})[\.\-/](\d{1,2})[\.\-/](\d{2,4})',  # "entry from 10/5/25"
            r'(\d{1,2})[\.\-/](\d{1,2})[\.\-/](\d{2,4})',                 # "10/5/25" in content
            r'(\d{4})[\.\-/](\d{1,2})[\.\-/](\d{1,2})',                  # "2025/10/5" in content
            r'(\w+)\s+(\d{1,2}),?\s+(\d{4})',                            # "October 5, 2025"
            r'(\d{1,2})\s+(\w+)\s+(\d{4})',                              # "5 October 2025"
        ]
    
    def extract_text_from_file(self, file_path: str) -> str:
        """Extract text content from various file types."""
        try:
            file_ext = Path(file_path).suffix.lower()
            
            if file_ext == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            elif file_ext in ['.doc', '.docx']:
                # TODO: Implement doc/docx parsing when needed
                # For now, return placeholder
                return f"[DOC FILE: {Path(file_path).name}]"
            elif file_ext == '.m4a':
                # Transcribe audio file
                from backend.utils.audio_transcription import transcribe_audio_file
                transcription, error_msg = transcribe_audio_file(file_path)
                if transcription:
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
    
    def infer_date_from_filename(self, filename: str) -> Optional[date]:
        """Infer date from filename patterns."""
        for pattern in self.date_patterns[:3]:  # File name patterns only
            match = re.search(pattern, filename, re.IGNORECASE)
            if match:
                try:
                    groups = match.groups()
                    if len(groups) == 3:
                        # Handle different year formats
                        if len(groups[2]) == 2:  # 2-digit year
                            year = int(groups[2]) + (2000 if int(groups[2]) < 50 else 1900)
                        else:  # 4-digit year
                            year = int(groups[2])
                        
                        month = int(groups[0]) if len(groups[0]) <= 2 else int(groups[1])
                        day = int(groups[1]) if len(groups[0]) <= 2 else int(groups[0])
                        
                        # Handle different date orders (MM/DD/YYYY vs DD/MM/YYYY)
                        if month > 12:  # Likely DD/MM format
                            month, day = day, month
                        
                        return date(year, month, day)
                except (ValueError, TypeError) as e:
                    logger.debug(f"Date parsing failed for {filename}: {e}")
                    continue
        return None
    
    def infer_date_from_content(self, content: str) -> Optional[date]:
        """Infer date from content patterns."""
        for pattern in self.date_patterns[3:]:  # Content patterns only
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                try:
                    groups = match.groups()
                    if len(groups) == 3:
                        # Handle different formats
                        if groups[0].isdigit() and groups[1].isdigit() and groups[2].isdigit():
                            # Numeric format
                            if len(groups[2]) == 2:  # 2-digit year
                                year = int(groups[2]) + (2000 if int(groups[2]) < 50 else 1900)
                            else:  # 4-digit year
                                year = int(groups[2])
                            
                            month = int(groups[0]) if len(groups[0]) <= 2 else int(groups[1])
                            day = int(groups[1]) if len(groups[0]) <= 2 else int(groups[0])
                            
                            if month > 12:  # Likely DD/MM format
                                month, day = day, month
                            
                            return date(year, month, day)
                        else:
                            # Text format like "October 5, 2025"
                            month_names = {
                                'january': 1, 'february': 2, 'march': 3, 'april': 4,
                                'may': 5, 'june': 6, 'july': 7, 'august': 8,
                                'september': 9, 'october': 10, 'november': 11, 'december': 12
                            }
                            
                            month_name = groups[0].lower() if groups[0].isalpha() else groups[1].lower()
                            if month_name in month_names:
                                month = month_names[month_name]
                                day = int(groups[1]) if groups[1].isdigit() else int(groups[0])
                                year = int(groups[2])
                                return date(year, month, day)
                except (ValueError, TypeError) as e:
                    logger.debug(f"Date parsing failed for content: {e}")
                    continue
        return None
    
    def get_file_metadata_date(self, file_path: str) -> Optional[date]:
        """Get date from file metadata (creation/modification time)."""
        try:
            stat = os.stat(file_path)
            # Use modification time as fallback
            timestamp = stat.st_mtime
            return date.fromtimestamp(timestamp)
        except Exception as e:
            logger.debug(f"Could not get metadata date for {file_path}: {e}")
            return None
    
    def infer_entry_date(self, file_path: str, content: str) -> Tuple[Optional[date], str]:
        """
        Infer the entry date from multiple sources.
        Returns (date, source_description)
        """
        file_ext = Path(file_path).suffix.lower()
        
        # For audio files, use audio-specific date extraction
        if file_ext == '.m4a':
            from backend.utils.audio_metadata import infer_audio_entry_date
            from datetime import date as date_type
            audio_datetime, source = infer_audio_entry_date(file_path)
            if audio_datetime:
                # Convert datetime to date if needed
                if isinstance(audio_datetime, date_type):
                    return audio_datetime, source
                else:
                    return audio_datetime.date(), source
            return None, "none"
        
        # For text files, use existing logic
        # Try filename first
        filename_date = self.infer_date_from_filename(Path(file_path).name)
        if filename_date:
            return filename_date, "filename"
        
        # Try content
        content_date = self.infer_date_from_content(content)
        if content_date:
            return content_date, "content"
        
        # Fallback to file metadata
        metadata_date = self.get_file_metadata_date(file_path)
        if metadata_date:
            return metadata_date, "file_metadata"
        
        return None, "none"
    
    def process_uploaded_file(self, file_path: str, user_id: str) -> Dict:
        """
        Process a single uploaded file and return entry data.
        Returns dict with entry info or error details.
        """
        try:
            # Extract text content
            content = self.extract_text_from_file(file_path)
            if not content.strip():
                return {
                    'success': False,
                    'error': 'No content found in file',
                    'filename': Path(file_path).name
                }
            
            # Infer date
            entry_date, date_source = self.infer_entry_date(file_path, content)
            
            if not entry_date:
                return {
                    'success': False,
                    'error': 'Could not determine entry date',
                    'filename': Path(file_path).name,
                    'content_preview': content[:100] + '...' if len(content) > 100 else content
                }
            
            # Format date with time as title_date in "Month DD, YYYY at h:MM AM/PM" format
            # Convert date to datetime if needed, then format
            from backend.utils.entry_helpers import format_title_date_with_time_from_date
            if isinstance(entry_date, date) and not isinstance(entry_date, datetime):
                # Use current time if only date is available
                title_date = format_title_date_with_time_from_date(entry_date)
            else:
                title_date = format_title_date_with_time(entry_date if isinstance(entry_date, datetime) else None)
            date_str = entry_date.strftime('%m/%d/%Y')  # Keep for display purposes
            
            return {
                'success': True,
                'filename': Path(file_path).name,
                'content': content,
                'entry_date': entry_date,
                'date_string': date_str,  # For display (MM/DD/YYYY)
                'title_date': title_date,  # For database (Month DD, YYYY format)
                'date_source': date_source,
                'content_length': len(content)
            }
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            return {
                'success': False,
                'error': str(e),
                'filename': Path(file_path).name
            }
    
    def process_multiple_files(self, file_paths: List[str], user_id: str) -> Dict:
        """
        Process multiple files and return results.
        """
        results = {
            'successful': [],
            'failed': [],
            'total_files': len(file_paths),
            'summary': {}
        }
        
        for file_path in file_paths:
            result = self.process_uploaded_file(file_path, user_id)
            
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
