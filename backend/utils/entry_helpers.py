"""
Helper functions for entry creation, including title_date formatting.
"""

from datetime import datetime
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)

def format_title_date_only(entry_date) -> str:
    """
    Format entry date as "Month DD, YYYY" (no time).
    Accepts date string or datetime object.
    
    Examples:
        "June 4, 2024"
        "November 17, 2025"
    
    Args:
        entry_date: Date string (e.g., "June 4, 2024") or datetime object
        
    Returns:
        Formatted string in "Month DD, YYYY" format
    """
    from datetime import date
    
    if isinstance(entry_date, str):
        # Already formatted, return as is (assuming it's in correct format)
        return entry_date
    elif isinstance(entry_date, datetime):
        formatted = entry_date.strftime("%B %d, %Y").replace(' 0', ' ')
        return formatted
    elif isinstance(entry_date, date):
        formatted = entry_date.strftime("%B %d, %Y").replace(' 0', ' ')
        return formatted
    else:
        # Fallback to current date
        formatted = datetime.now().strftime("%B %d, %Y").replace(' 0', ' ')
        return formatted

def format_title_date_with_time(entry_datetime: Optional[datetime] = None) -> str:
    """
    Format entry date and time as "Month DD, YYYY at h:MM AM/PM" for title_date.
    If no datetime provided, uses current datetime.
    
    Examples:
        "November 17, 2025 at 3:45 PM"
        "October 27, 2025 at 6:51 PM"
        "October 27, 2025 at 12:51 PM"  (not 012:51 PM)
    
    Args:
        entry_datetime: Optional datetime object. If None, uses current datetime.
        
    Returns:
        Formatted string in "Month DD, YYYY at h:MM AM/PM" format
    """
    if entry_datetime is None:
        entry_datetime = datetime.now()
    
    # Format: "Month DD, YYYY at h:MM AM/PM"
    # Remove leading zero from day
    formatted = entry_datetime.strftime("%B %d, %Y at %I:%M %p").replace(' 0', ' ')
    
    # Remove leading zero from hour (e.g., "09:45" -> "9:45", "012:51" -> "12:51")
    parts = formatted.split(' at ')
    if len(parts) == 2:
        date_part = parts[0]
        time_part = parts[1]
        # Remove leading zero from hour, but keep "12" as "12" (not "012")
        # Split time part: "06:51 PM" -> ["06", "51", "PM"]
        time_components = time_part.split(':')
        if len(time_components) == 2:
            hour = time_components[0]
            minute_and_ampm = time_components[1]
            # Remove leading zero from hour (but keep "12" as is)
            if hour.startswith('0') and hour != '00':
                hour = hour[1:]  # "06" -> "6", "09" -> "9"
            elif hour == '00':
                hour = '12'  # Midnight/noon edge case
            time_part = f"{hour}:{minute_and_ampm}"
        formatted = f"{date_part} at {time_part}"
    
    return formatted

def format_title_date_with_time_from_date(entry_date, entry_time: Optional[datetime] = None) -> str:
    """
    Format entry date and time when you have a date object and optional time.
    If time is not provided, uses current time.
    
    Args:
        entry_date: date or datetime object
        entry_time: Optional datetime for time. If None, uses current time.
        
    Returns:
        Formatted string in "Month DD, YYYY at h:MM AM/PM" format
    """
    from datetime import date, time
    
    if entry_time is None:
        entry_time = datetime.now()
    
    # If entry_date is a date object, combine with time
    if isinstance(entry_date, date) and not isinstance(entry_date, datetime):
        entry_datetime = datetime.combine(entry_date, entry_time.time())
    elif isinstance(entry_date, datetime):
        entry_datetime = entry_date
    else:
        # Fallback to current datetime
        entry_datetime = datetime.now()
    
    return format_title_date_with_time(entry_datetime)


def recalculate_user_entry_ids(user_supabase, user_id: str) -> Dict:
    """
    Recalculate user_entry_id for all entries belonging to a user,
    ordered chronologically by created_at.
    
    This ensures that entry IDs are sequential (1, 2, 3, ...) based on
    the chronological order of when entries were created, not when they
    were uploaded.
    
    Args:
        user_supabase: Authenticated Supabase client for the user
        user_id: The user's ID
        
    Returns:
        Dict with 'success' (bool), 'updated_count' (int), and 'error' (str, if any)
    """
    try:
        # Fetch all entries for the user, ordered by created_at
        response = user_supabase.table('entries').select(
            'user_and_entry_id, created_at'
        ).order('created_at', desc=False).execute()
        
        entries = response.data
        if not entries:
            logger.info(f"No entries found for user {user_id} to recalculate")
            return {
                'success': True,
                'updated_count': 0,
                'error': None
            }
        
        logger.info(f"Recalculating entry IDs for {len(entries)} entries for user {user_id}")
        
        updated_count = 0
        errors = []
        
        # Phase 1: Move all entries that need updating to temporary IDs (negative numbers)
        # This avoids primary key conflicts when reassigning IDs
        temp_id_offset = -1000000  # Use negative numbers as temporary IDs
        entries_to_update = []
        
        for index, entry in enumerate(entries, start=1):
            old_user_and_entry_id = entry['user_and_entry_id']
            new_user_entry_id = index
            new_user_and_entry_id = f"{user_id}_{new_user_entry_id}"
            
            # Skip if ID is already correct
            if old_user_and_entry_id == new_user_and_entry_id:
                continue
            
            entries_to_update.append({
                'old_id': old_user_and_entry_id,
                'new_id': new_user_entry_id,
                'new_user_and_entry_id': new_user_and_entry_id
            })
        
        if not entries_to_update:
            logger.info(f"All entry IDs are already correct for user {user_id}")
            return {
                'success': True,
                'updated_count': 0,
                'error': None
            }
        
        # Phase 1: Move to temporary IDs
        for temp_index, entry_update in enumerate(entries_to_update):
            temp_user_entry_id = temp_id_offset - temp_index
            temp_user_and_entry_id = f"{user_id}_{temp_user_entry_id}"
            
            try:
                update_response = user_supabase.table('entries').update({
                    'user_entry_id': temp_user_entry_id,
                    'user_and_entry_id': temp_user_and_entry_id
                }).eq('user_and_entry_id', entry_update['old_id']).execute()
                
                if update_response.data:
                    entry_update['temp_id'] = temp_user_and_entry_id
                    updated_count += 1
                else:
                    error_msg = f"Failed to move entry {entry_update['old_id']} to temporary ID"
                    errors.append(error_msg)
                    logger.warning(error_msg)
                    
            except Exception as e:
                error_msg = f"Error moving entry {entry_update['old_id']} to temporary ID: {str(e)}"
                errors.append(error_msg)
                logger.exception(error_msg)
        
        # Phase 2: Move from temporary IDs to final IDs
        final_updated_count = 0
        for entry_update in entries_to_update:
            if 'temp_id' not in entry_update:
                continue  # Skip entries that failed in phase 1
                
            try:
                update_response = user_supabase.table('entries').update({
                    'user_entry_id': entry_update['new_id'],
                    'user_and_entry_id': entry_update['new_user_and_entry_id']
                }).eq('user_and_entry_id', entry_update['temp_id']).execute()
                
                if update_response.data:
                    final_updated_count += 1
                    logger.debug(f"Updated entry {entry_update['old_id']} -> {entry_update['new_user_and_entry_id']}")
                else:
                    error_msg = f"Failed to move entry from temp ID to final ID {entry_update['new_user_and_entry_id']}"
                    errors.append(error_msg)
                    logger.warning(error_msg)
                    
            except Exception as e:
                error_msg = f"Error moving entry to final ID {entry_update['new_user_and_entry_id']}: {str(e)}"
                errors.append(error_msg)
                logger.exception(error_msg)
        
        updated_count = final_updated_count
        
        if errors:
            logger.warning(f"Recalculation completed with {len(errors)} errors for user {user_id}")
            return {
                'success': True,  # Partial success
                'updated_count': updated_count,
                'error': f"{len(errors)} entries failed to update: {', '.join(errors[:3])}"  # Show first 3 errors
            }
        
        logger.info(f"Successfully recalculated {updated_count} entry IDs for user {user_id}")
        return {
            'success': True,
            'updated_count': updated_count,
            'error': None
        }
        
    except Exception as e:
        logger.exception(f"Error recalculating entry IDs for user {user_id}: {e}")
        return {
            'success': False,
            'updated_count': 0,
            'error': str(e)
        }

