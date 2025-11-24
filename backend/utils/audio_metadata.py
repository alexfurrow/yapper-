"""
Audio metadata extraction utilities for m4a and other audio formats.
Handles iOS Voice Memos and Recorder Pro naming patterns.
"""

import os
import re
from datetime import datetime, date
from typing import Optional, Tuple
from pathlib import Path
from backend.config.logging import get_logger

logger = get_logger(__name__)

try:
    from mutagen import File as MutagenFile
    from mutagen.mp4 import MP4
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False
    logger.warning("mutagen library not available. Install with: pip install mutagen")


def extract_date_from_m4a_metadata(file_path: str) -> Optional[datetime]:
    """
    Extract recording date/time from m4a file metadata.
    This is the preferred source for audio file dates as it's embedded in the file.
    
    Args:
        file_path: Path to the m4a file
        
    Returns:
        datetime object if found, None otherwise
    """
    # Import mutagen here to ensure it's available even if module-level import failed
    try:
        from mutagen import File as MutagenFile
        from mutagen.mp4 import MP4
    except ImportError as e:
        logger.warning(f"mutagen not available, cannot extract m4a metadata for {Path(file_path).name}: {e}")
        return None
    
    try:
        audio_file = MutagenFile(file_path)
        if audio_file is None:
            logger.debug(f"Could not open audio file: {file_path}")
            return None
        
        available_tags = list(audio_file.keys())
        logger.info(f"Checking m4a metadata for {Path(file_path).name}, available tags: {available_tags}")
        
        # Try MP4-specific tags (iOS Voice Memos and other QuickTime-based formats)
        if isinstance(audio_file, MP4):
            # iOS Voice Memos typically use these tags:
            # - '©day' for date
            # - '©tim' for time (sometimes combined)
            # - '©too' (encoder/tool) - sometimes contains creation info
            # Also try other QuickTime date tags
            date_tags = ['©day', '©mvd', '©mvi', '©mvc', '©tim', '©too']  # Various QuickTime date tags
            
            # First, check if ©too exists and log its value for debugging
            if '©too' in audio_file:
                too_value = audio_file['©too'][0] if audio_file['©too'] else None
                logger.info(f"Found ©too tag with value: {too_value} (type: {type(too_value)})")
            for tag in date_tags:
                if tag in audio_file:
                    try:
                        date_value = audio_file[tag][0]
                        date_str = str(date_value)
                        logger.info(f"Found tag {tag} with value: {date_str}")
                        
                        # Try parsing various date formats
                        # Format: "2025-11-17" or "2025-11-17T15:45:00Z" or timestamp
                        if 'T' in date_str:
                            parsed = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                            logger.info(f"Parsed date from {tag}: {parsed}")
                            return parsed
                        else:
                            # Try date-only format
                            try:
                                parsed = datetime.strptime(date_str, '%Y-%m-%d')
                                logger.info(f"Parsed date from {tag}: {parsed}")
                                return parsed
                            except ValueError:
                                # Might be a timestamp or other format
                                try:
                                    # Try as timestamp (seconds since epoch)
                                    timestamp = float(date_str)
                                    parsed = datetime.fromtimestamp(timestamp)
                                    logger.info(f"Parsed timestamp from {tag}: {parsed}")
                                    return parsed
                                except (ValueError, OSError):
                                    continue
                    except (ValueError, AttributeError, IndexError, TypeError) as e:
                        logger.info(f"Error parsing tag {tag}: {e}")
                        continue
        
        # Try generic tags
        for tag in ['date', 'creation_date', 'recording_date', 'creation_time', 'TDRC']:
            if tag in audio_file:
                try:
                    date_value = audio_file[tag][0]
                    date_str = str(date_value)
                    logger.info(f"Found generic tag {tag} with value: {date_str}")
                    
                    # Try ISO format first
                    if 'T' in date_str:
                        parsed = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                        logger.info(f"Parsed date from {tag}: {parsed}")
                        return parsed
                    # Try other common formats
                    for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%m/%d/%Y']:
                        try:
                            parsed = datetime.strptime(date_str, fmt)
                            logger.info(f"Parsed date from {tag}: {parsed}")
                            return parsed
                        except ValueError:
                            continue
                except (ValueError, AttributeError, IndexError) as e:
                    logger.info(f"Error parsing generic tag {tag}: {e}")
                    continue
        
        logger.info(f"No date found in m4a metadata for {Path(file_path).name}")
        return None
        
    except Exception as e:
        logger.warning(f"Error extracting m4a metadata from {file_path}: {e}")
        return None


def infer_date_from_ios_voice_memos_filename(filename: str) -> Optional[datetime]:
    """
    Extract date from iOS Voice Memos filename pattern.
    Pattern: "New Recording N" where N is sequence number.
    Note: iOS Voice Memos don't include date in filename, but metadata should have it.
    This function is mainly for logging/debugging purposes.
    
    Args:
        filename: Filename to check
        
    Returns:
        None (iOS Voice Memos don't have date in filename)
    """
    # iOS Voice Memos use "New Recording N" format - no date in filename
    # Date must come from metadata
    pattern = r'New Recording (\d+)'
    match = re.match(pattern, filename, re.IGNORECASE)
    if match:
        # Can't extract date from this pattern, but we know it's a Voice Memo
        return None
    return None


def infer_date_from_recorder_pro_filename(filename: str) -> Optional[datetime]:
    """
    Extract date and time from Recorder Pro filename pattern.
    Pattern: "Mon DD, YYYY at h_MM_SS PM/AM.m4a"
    Example: "Oct 27, 2025 at 6_51_35 PM.m4a"
    
    Args:
        filename: Filename to check
        
    Returns:
        datetime object if pattern matches, None otherwise
    """
    # Remove file extension
    name_without_ext = Path(filename).stem
    
    # Pattern: "Mon DD, YYYY at h_MM_SS PM/AM"
    # Example: "Oct 27, 2025 at 6_51_35 PM"
    pattern = r'([A-Za-z]{3})\s+(\d{1,2}),\s+(\d{4})\s+at\s+(\d{1,2})_(\d{2})_(\d{2})\s+(AM|PM)'
    match = re.match(pattern, name_without_ext)
    
    if match:
        month_abbr, day, year, hour, minute, second, am_pm = match.groups()
        
        try:
            # Convert month abbreviation to number
            month_num = datetime.strptime(month_abbr, '%b').month
            
            # Convert hour to 24-hour format
            hour_int = int(hour)
            if am_pm.upper() == 'PM' and hour_int != 12:
                hour_int += 12
            elif am_pm.upper() == 'AM' and hour_int == 12:
                hour_int = 0
            
            return datetime(
                year=int(year),
                month=month_num,
                day=int(day),
                hour=hour_int,
                minute=int(minute),
                second=int(second)
            )
        except (ValueError, AttributeError) as e:
            logger.debug(f"Error parsing Recorder Pro date from {filename}: {e}")
            return None
    
    return None


def infer_date_from_audio_filename(filename: str) -> Optional[datetime]:
    """
    Try to extract date from various audio filename patterns.
    Checks Recorder Pro format first, then generic date patterns.
    
    Args:
        filename: Filename to check
        
    Returns:
        datetime object if pattern matches, None otherwise
    """
    # Try Recorder Pro format first
    recorder_pro_date = infer_date_from_recorder_pro_filename(filename)
    if recorder_pro_date:
        return recorder_pro_date
    
    # Try generic date patterns (reuse from bulk_upload service)
    date_patterns = [
        r'(\d{1,2})[\.\-/](\d{1,2})[\.\-/](\d{2,4})',  # 10.5.25, 10-5-25, 10/5/25
        r'(\d{4})[\.\-/](\d{1,2})[\.\-/](\d{1,2})',     # 2025.10.5, 2025-10-5, 2025/10/5
        r'(\d{1,2})[\.\-/](\d{1,2})[\.\-/](\d{4})',      # 10.5.2025, 10-5-2025, 10/5/2025
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, filename)
        if match:
            parts = match.groups()
            try:
                if len(parts[2]) == 4:  # Full year
                    if len(parts[0]) == 4:  # YYYY-MM-DD
                        return datetime(int(parts[0]), int(parts[1]), int(parts[2]))
                    else:  # MM-DD-YYYY
                        return datetime(int(parts[2]), int(parts[0]), int(parts[1]))
                else:  # 2-digit year
                    year = int(parts[2])
                    if year < 50:  # Assume 2000s
                        year += 2000
                    else:  # Assume 1900s
                        year += 1900
                    if len(parts[0]) == 4:  # Unlikely but handle it
                        return datetime(year, int(parts[1]), int(parts[0]))
                    else:  # MM-DD-YY
                        return datetime(year, int(parts[0]), int(parts[1]))
            except (ValueError, IndexError):
                continue
    
    return None


def get_file_metadata_date(file_path: str) -> Optional[date]:
    """
    Get date from file system metadata (creation time preferred, modification time as fallback).
    
    Args:
        file_path: Path to the file
        
    Returns:
        date object if available, None otherwise
    """
    try:
        stat = os.stat(file_path)
        # Try to get creation time (birthtime) - available on macOS and some Linux systems
        # Fallback to modification time if creation time not available
        if hasattr(stat, 'st_birthtime'):
            timestamp = stat.st_birthtime  # Creation time (macOS)
        elif hasattr(stat, 'st_ctime'):
            # On some systems, st_ctime is creation time, on others it's metadata change time
            # Use it as fallback
            timestamp = stat.st_ctime
        else:
            timestamp = stat.st_mtime  # Modification time as last resort
        return date.fromtimestamp(timestamp)
    except Exception as e:
        logger.debug(f"Could not get metadata date for {file_path}: {e}")
        return None


def infer_audio_entry_date(file_path: str) -> Tuple[Optional[datetime], str]:
    """
    Infer the entry date from multiple sources for audio files.
    Priority:
    1. m4a file metadata (recording date)
    2. Filename patterns (Recorder Pro, generic dates)
    3. File system metadata (modification time - "Date Modified" in Finder)
    
    Args:
        file_path: Path to the audio file
        
    Returns:
        Tuple of (datetime, source_description)
        If no date found: (None, "none")
    """
    filename = Path(file_path).name
    logger.info(f"Inferring date for audio file: {filename}")
    
    # Try m4a metadata first (most accurate for recording date)
    metadata_date = extract_date_from_m4a_metadata(file_path)
    if metadata_date:
        logger.info(f"Found date in m4a metadata: {metadata_date}")
        return metadata_date, "m4a_metadata"
    else:
        logger.info(f"No date found in m4a metadata for {filename}, trying other sources...")
    
    # Try filename patterns
    filename_date = infer_date_from_audio_filename(filename)
    if filename_date:
        logger.info(f"Found date in filename: {filename_date}")
        return filename_date, "filename"
    else:
        logger.info(f"No date found in filename pattern for {filename}")
    
    # Fallback to file system metadata
    # Use modification time (st_mtime) which corresponds to "Date Modified" in Finder
    # This is what the user expects to see
    try:
        stat = os.stat(file_path)
        # Use modification time (st_mtime) - this is "Date Modified" in Finder
        timestamp = stat.st_mtime
        # Convert timestamp to datetime
        fs_datetime = datetime.fromtimestamp(timestamp)
        logger.info(f"Using file modification time for {Path(file_path).name}: {fs_datetime}")
        return fs_datetime, "file_metadata"
    except Exception as e:
        logger.warning(f"Could not get file metadata timestamp for {file_path}: {e}")
        # Last resort: try to get date from get_file_metadata_date
        fs_date = get_file_metadata_date(file_path)
        if fs_date:
            # Combine with current time (not ideal, but better than nothing)
            logger.warning(f"Using date with current time as fallback: {fs_date}")
            return datetime.combine(fs_date, datetime.now().time()), "file_metadata"
    
    return None, "none"

