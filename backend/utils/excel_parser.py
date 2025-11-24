"""
Utility for parsing Excel spreadsheets and CSV files that map filenames to dates.
Expected format:
- Column 1: File names (e.g., "New Recording 23")
- Column 2: Date Created (e.g., "Jun 4 2024", "June 4 2024")
"""

import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

def parse_excel_mapping(file_path: str) -> Tuple[Dict[str, str], Optional[str]]:
    """
    Parse Excel or CSV file to extract filename-to-date mapping.
    
    Expected format:
    - First column: File names (without extension)
    - Second column: Date Created (various formats accepted)
    
    Args:
        file_path: Path to Excel file (.xlsx, .xls) or CSV file (.csv)
        
    Returns:
        Tuple of (mapping_dict, error_message)
        - mapping_dict: {filename: formatted_date_string}
        - error_message: None if successful, error string if failed
    """
    try:
        # Detect file type and read accordingly
        file_ext = Path(file_path).suffix.lower()
        if file_ext == '.csv':
            # Read CSV file (try to detect header, try common delimiters and encodings)
            try:
                # Try UTF-8 first (most common)
                df = pd.read_csv(file_path, encoding='utf-8')
            except UnicodeDecodeError:
                # Fallback to latin-1 if UTF-8 fails
                try:
                    df = pd.read_csv(file_path, encoding='latin-1')
                except Exception as e:
                    return {}, f"Error reading CSV file: {str(e)}"
        else:
            # Read Excel file (pandas will auto-detect header)
            df = pd.read_excel(file_path)
        
        if df.empty:
            file_type = "CSV" if file_ext == '.csv' else "Excel"
            return {}, f"{file_type} file is empty"
        
        # Get first two columns
        if df.shape[1] < 2:
            file_type = "CSV" if file_ext == '.csv' else "Excel"
            return {}, f"{file_type} file must have at least 2 columns (File names, Date Created)"
        
        # Detect column order by checking first non-null row
        # Look for which column contains what looks like a date vs filename
        col1 = df.iloc[:, 0]
        col2 = df.iloc[:, 1]
        
        # Find first row with both values
        first_valid_idx = None
        for idx in range(len(df)):
            if not pd.isna(col1.iloc[idx]) and not pd.isna(col2.iloc[idx]):
                first_valid_idx = idx
                break
        
        if first_valid_idx is None:
            file_type = "CSV" if file_ext == '.csv' else "Excel"
            return {}, f"No valid data rows found in {file_type} file"
        
        # Check which column is likely the date and which is the filename
        val1 = str(col1.iloc[first_valid_idx]).strip()
        val2 = str(col2.iloc[first_valid_idx]).strip()
        
        # Try to parse both as dates to determine order
        date_in_col1 = parse_date_string(val1) is not None
        date_in_col2 = parse_date_string(val2) is not None
        
        # Determine column order
        if date_in_col1 and not date_in_col2:
            # Column 1 is date, column 2 is filename
            date_col = col1
            filename_col = col2
            logger.info("Detected: Column 1 = Date, Column 2 = Filename")
        elif date_in_col2 and not date_in_col1:
            # Column 1 is filename, column 2 is date (expected order)
            filename_col = col1
            date_col = col2
            logger.info("Detected: Column 1 = Filename, Column 2 = Date")
        else:
            # Ambiguous - default to expected order (filename, date)
            filename_col = col1
            date_col = col2
            logger.warning("Could not determine column order, using default: Column 1 = Filename, Column 2 = Date")
        
        mapping = {}
        errors = []
        
        for idx, (filename, date_value) in enumerate(zip(filename_col, date_col), start=1):
            # Skip empty rows
            if pd.isna(filename) or pd.isna(date_value):
                continue
            
            # Skip header-like rows (check if it looks like a header)
            filename_str = str(filename).strip()
            date_str = str(date_value).strip()
            
            # Skip if either value looks like a header (case-insensitive check for common header names)
            header_keywords = ['date', 'file', 'name', 'created', 'filename', 'file name']
            if any(keyword in filename_str.lower() for keyword in header_keywords) or \
               any(keyword in date_str.lower() for keyword in header_keywords):
                logger.debug(f"Skipping row {idx} (appears to be header): '{filename_str}' / '{date_str}'")
                continue
            
            # Clean filename (remove extension if present, strip whitespace)
            filename_clean = filename_str.strip()
            if '.' in filename_clean:
                # Remove extension
                filename_clean = Path(filename_clean).stem.strip()
            else:
                # Already stripped, but ensure no trailing spaces
                filename_clean = filename_clean.strip()
            
            # Parse date
            formatted_date = parse_date_string(date_str)
            
            if not formatted_date:
                errors.append(f"Row {idx}: Could not parse date '{date_str}' for file '{filename_clean}'")
                continue
            
            mapping[filename_clean] = formatted_date
            logger.debug(f"Row {idx}: Mapped '{filename_str}' -> '{filename_clean}' -> '{formatted_date}'")
        
        if errors:
            error_msg = "; ".join(errors)
            logger.warning(f"Excel parsing completed with errors: {error_msg}")
            # Still return mapping for rows that succeeded
        
        if not mapping:
            file_type = "CSV" if Path(file_path).suffix.lower() == '.csv' else "Excel"
            return {}, f"No valid filename-date pairs found in {file_type} file"
        
        file_type = "CSV" if Path(file_path).suffix.lower() == '.csv' else "Excel"
        logger.info(f"Successfully parsed {len(mapping)} filename-date pairs from {file_type}")
        return mapping, None
        
    except Exception as e:
        file_type = "CSV" if Path(file_path).suffix.lower() == '.csv' else "Excel"
        logger.exception(f"Error parsing {file_type} file {file_path}: {e}")
        return {}, f"Error parsing {file_type} file: {str(e)}"


def parse_date_string(date_str: str) -> Optional[str]:
    """
    Parse date string in various formats and return "Month DD, YYYY" format.
    
    Accepts formats like:
    - "Jun 4 2024"
    - "June 4 2024"
    - "6/4/2024"
    - "2024-06-04"
    - etc.
    
    Args:
        date_str: Date string in various formats
        
    Returns:
        Formatted date string "Month DD, YYYY" or None if parsing fails
    """
    if not date_str or not date_str.strip():
        return None
    
    date_str = str(date_str).strip()
    
    # Try common date formats
    date_formats = [
        "%B %d, %Y",      # June 4, 2024
        "%b %d, %Y",      # Jun 4, 2024
        "%B %d %Y",       # June 4 2024
        "%b %d %Y",       # Jun 4 2024
        "%m/%d/%Y",       # 6/4/2024
        "%m-%d-%Y",       # 6-4-2024
        "%Y-%m-%d",       # 2024-06-04
        "%d/%m/%Y",       # 4/6/2024 (European)
        "%d-%m-%Y",       # 4-6-2024 (European)
    ]
    
    for fmt in date_formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            # Format as "Month DD, YYYY" (remove leading zero from day)
            formatted = dt.strftime("%B %d, %Y").replace(' 0', ' ')
            return formatted
        except ValueError:
            continue
    
    # Try pandas date parsing as fallback
    try:
        dt = pd.to_datetime(date_str)
        formatted = dt.strftime("%B %d, %Y").replace(' 0', ' ')
        return formatted
    except Exception:
        pass
    
    logger.warning(f"Could not parse date string: {date_str}")
    return None

