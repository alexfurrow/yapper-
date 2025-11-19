"""
Helper functions for entry creation, including title_date formatting.
"""

from datetime import datetime
from typing import Optional

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

