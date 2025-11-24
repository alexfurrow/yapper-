"""
Auditing service to check that all entries follow the naming convention.
Convention: title should be in format "Month DD, YYYY at h:MM AM/PM"
"""

import re
from typing import List, Dict, Optional
from datetime import datetime
from backend.config.logging import get_logger

logger = get_logger(__name__)

# Pattern for expected title format: "Month DD, YYYY at h:MM AM/PM"
# Examples: "November 17, 2025 at 3:45 PM", "October 27, 2025 at 6:51 PM"
TITLE_PATTERN = re.compile(
    r'^([A-Za-z]+)\s+(\d{1,2}),\s+(\d{4})\s+at\s+(\d{1,2}):(\d{2})\s+(AM|PM)$',
    re.IGNORECASE
)

# Legacy pattern (old format without time): "Month DD, YYYY"
LEGACY_PATTERN = re.compile(
    r'^([A-Za-z]+)\s+(\d{1,2}),\s+(\d{4})$',
    re.IGNORECASE
)


def validate_title_format(title: str) -> Dict[str, any]:
    """
    Validate that a title follows the expected format.
    
    Args:
        title: The title string to validate
        
    Returns:
        Dict with:
            - 'valid': bool
            - 'format': 'correct' | 'legacy' | 'invalid'
            - 'message': str (if invalid)
    """
    if not title:
        return {
            'valid': False,
            'format': 'invalid',
            'message': 'title is empty'
        }
    
    # Check for correct format (with time)
    if TITLE_PATTERN.match(title):
        return {
            'valid': True,
            'format': 'correct',
            'message': None
        }
    
    # Check for legacy format (without time)
    if LEGACY_PATTERN.match(title):
        return {
            'valid': False,
            'format': 'legacy',
            'message': 'title missing time component (legacy format)'
        }
    
    # Invalid format
    return {
        'valid': False,
        'format': 'invalid',
        'message': f'title does not match expected format: "{title}"'
    }


def audit_entries(user_supabase, user_id: Optional[str] = None) -> Dict:
    """
    Audit all entries for a user to check naming convention compliance.
    
    Args:
        user_supabase: Authenticated Supabase client
        user_id: Optional user ID (if None, uses current user from context)
        
    Returns:
        Dict with:
            - 'total_entries': int
            - 'valid_entries': int
            - 'legacy_entries': int (entries without time)
            - 'invalid_entries': int
            - 'issues': List of entry issues
    """
    try:
        # Get all entries for the user
        query = user_supabase.table('entries').select('user_and_entry_id, user_entry_id, title, created_at')
        
        if user_id:
            query = query.eq('user_id', user_id)
        
        response = query.execute()
        entries = response.data if response.data else []
        
        total_entries = len(entries)
        valid_count = 0
        legacy_count = 0
        invalid_count = 0
        issues = []
        
        for entry in entries:
            title = entry.get('title', '')
            validation = validate_title_format(title)
            
            if validation['valid']:
                valid_count += 1
            elif validation['format'] == 'legacy':
                legacy_count += 1
                issues.append({
                    'user_and_entry_id': entry.get('user_and_entry_id'),
                    'user_entry_id': entry.get('user_entry_id'),
                    'title': title,
                    'issue': validation['message'],
                    'created_at': entry.get('created_at')
                })
            else:
                invalid_count += 1
                issues.append({
                    'user_and_entry_id': entry.get('user_and_entry_id'),
                    'user_entry_id': entry.get('user_entry_id'),
                    'title': title,
                    'issue': validation['message'],
                    'created_at': entry.get('created_at')
                })
        
        result = {
            'total_entries': total_entries,
            'valid_entries': valid_count,
            'legacy_entries': legacy_count,
            'invalid_entries': invalid_count,
            'issues': issues
        }
        
        logger.info(f"Entry audit completed: {valid_count} valid, {legacy_count} legacy, {invalid_count} invalid out of {total_entries} total")
        
        return result
        
    except Exception as e:
        logger.exception(f"Error auditing entries: {e}")
        return {
            'error': str(e),
            'total_entries': 0,
            'valid_entries': 0,
            'legacy_entries': 0,
            'invalid_entries': 0,
            'issues': []
        }


def fix_legacy_entry_title(entry: Dict, user_supabase) -> bool:
    """
    Fix a legacy entry by adding time component to title.
    Uses created_at timestamp if available, otherwise uses current time.
    
    Args:
        entry: Entry dict with user_and_entry_id and title
        user_supabase: Authenticated Supabase client
        
    Returns:
        True if fixed successfully, False otherwise
    """
    try:
        from backend.utils.entry_helpers import format_title_date_with_time
        
        # Try to get created_at from entry
        created_at = entry.get('created_at')
        if created_at:
            try:
                if isinstance(created_at, str):
                    entry_datetime = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                else:
                    entry_datetime = created_at
            except (ValueError, AttributeError):
                entry_datetime = datetime.now()
        else:
            entry_datetime = datetime.now()
        
        # Format new title with time
        new_title = format_title_date_with_time(entry_datetime)
        
        # Update entry
        response = user_supabase.table('entries').update({
            'title': new_title
        }).eq('user_and_entry_id', entry['user_and_entry_id']).execute()
        
        if response.data:
            logger.info(f"Fixed legacy entry: {entry['user_and_entry_id']}")
            return True
        else:
            logger.warning(f"Failed to update entry: {entry['user_and_entry_id']}")
            return False
            
    except Exception as e:
        logger.exception(f"Error fixing legacy entry: {e}")
        return False

