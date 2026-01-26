"""
Monthly summaries route for aggregating and summarizing user entries by month.
"""

from flask import Blueprint, request, jsonify, g
from werkzeug.exceptions import InternalServerError
import os
from supabase import create_client, Client
from functools import wraps
import logging
from datetime import datetime
from openai import OpenAI
from backend.routes.entries import supabase_auth_required

logger = logging.getLogger(__name__)

# Required environment variables
REQUIRED_ENV = [
    "SUPABASE_URL",
    "SUPABASE_PUBLISHABLE_KEY",
    "SUPABASE_SECRET_KEY",
    "OPENAI_API_KEY",
]

def validate_env():
    """Validate that all required environment variables are present"""
    missing = [k for k in REQUIRED_ENV if not os.environ.get(k)]
    if missing:
        raise InternalServerError(f"Missing required environment variables: {', '.join(missing)}")

monthly_summaries_bp = Blueprint('monthly_summaries', __name__)

# Validate environment variables
validate_env()

# Initialize Supabase client for service operations
supabase: Client = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_SECRET_KEY")
)

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

# Summary prompt template
SUMMARY_PROMPT = """You are analyzing a user's journal entries from {month_year}. 

Your task is to create a thoughtful, insightful summary that captures:
- Key themes and patterns across the entries
- Emotional journey and growth
- Significant events or moments
- Overall narrative arc of the month

Be empathetic, insightful, and focus on the human story. Write in second person ("you") and keep it concise but meaningful (2-3 paragraphs).

Journal Entries:
{entries_text}

Create a summary of this month's journal entries:"""

def format_month_year(date_str):
    """Format date string to 'Month Year' format (e.g., 'April 2025')"""
    try:
        date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return date.strftime('%B %Y')
    except:
        # Fallback if date parsing fails
        return date_str

def get_entries_for_month(user_id, user_supabase, month, year):
    """Get all entries for a specific month and year"""
    try:
        # Get start and end of month
        start_date = datetime(year, month, 1).isoformat()
        # Get first day of next month
        if month == 12:
            end_date = datetime(year + 1, 1, 1).isoformat()
        else:
            end_date = datetime(year, month + 1, 1).isoformat()
        
        # Query entries for this month
        response = user_supabase.table('entries')\
            .select('user_entry_id, content, created_at')\
            .eq('user_id', user_id)\
            .gte('created_at', start_date)\
            .lt('created_at', end_date)\
            .order('created_at', desc=False)\
            .execute()
        
        return response.data if response.data else []
    except Exception as e:
        logger.error(f"Error fetching entries for month: {str(e)}")
        return []

def generate_summary(entries, month_year):
    """Generate summary using OpenAI"""
    try:
        # Format entries for prompt with basic sanitization
        entries_text = ""
        for entry in entries:
            entry_date = entry.get('created_at', '')
            entry_content = entry.get('content', '')
            # Basic sanitization: escape any potential prompt injection attempts
            # Remove or neutralize common injection patterns
            sanitized_content = entry_content.replace('Ignore previous instructions', '[instruction]')
            sanitized_content = sanitized_content.replace('Ignore all previous', '[instruction]')
            sanitized_content = sanitized_content.replace('You are now', '[role change]')
            entries_text += f"\n\nEntry #{entry.get('user_entry_id', 'N/A')} ({entry_date}):\n{sanitized_content}"
        
        # Create prompt with explicit instruction boundaries
        prompt = SUMMARY_PROMPT.format(
            month_year=month_year,
            entries_text=entries_text
        )
        
        # Call OpenAI
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a thoughtful journaling assistant that helps users reflect on their experiences."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        summary = response.choices[0].message.content.strip()
        return summary
    except Exception as e:
        logger.error(f"Error generating summary: {str(e)}")
        raise

def generate_summary_for_user(user_id, month, year, user_supabase=None):
    """Generate monthly summary for a specific user and month/year.
    Can be called from scheduled tasks or CLI scripts.
    Returns (success: bool, message: str, data: dict or None)
    """
    try:
        # Create Supabase client if not provided
        if user_supabase is None:
            from backend.routes.entries import create_user_supabase_client
            # For service operations, we need to use service role key
            # But we need user_id, so we'll use service client to get entries
            service_supabase = create_client(
                os.environ.get("SUPABASE_URL"),
                os.environ.get("SUPABASE_SECRET_KEY")
            )
            user_supabase = service_supabase
        
        month_year = f"{datetime(year, month, 1).strftime('%B %Y')}"
        
        # Check if summary already exists
        existing = user_supabase.table('monthly_summaries')\
            .select('*')\
            .eq('user_id', user_id)\
            .eq('month_year', month_year)\
            .execute()
        
        if existing.data and len(existing.data) > 0:
            logger.info(f"Summary already exists for user {user_id}, month {month_year}")
            return True, f"Summary already exists for {month_year}", existing.data[0]
        
        # Get entries for this month
        entries = get_entries_for_month(user_id, user_supabase, month, year)
        
        if not entries:
            return False, f'No entries found for {month_year}', None
        
        # Extract user_entry_ids
        list_of_entries = [entry.get('user_entry_id') for entry in entries]
        
        # Generate summary
        logger.info(f"Generating summary for user {user_id}, {month_year} with {len(entries)} entries")
        summary = generate_summary(entries, month_year)
        
        # Save to database
        summary_data = {
            'user_id': user_id,
            'month_year': month_year,
            'list_of_entries': list_of_entries,
            'summary': summary
        }
        
        response = user_supabase.table('monthly_summaries').insert(summary_data).execute()
        
        if response.data:
            logger.info(f"Summary created for user {user_id}, {month_year}")
            return True, f"Summary created for {month_year}", response.data[0]
        else:
            return False, 'Failed to save summary', None
            
    except Exception as e:
        logger.exception(f"Error generating summary for user {user_id}")
        return False, f'Error generating summary: {str(e)}', None

def generate_summaries_for_previous_month():
    """Generate summaries for all users for the previous month.
    Called automatically on the 1st of each month.
    """
    try:
        from datetime import datetime, timedelta
        from calendar import monthrange
        
        # Get previous month
        today = datetime.now()
        if today.month == 1:
            prev_month = 12
            prev_year = today.year - 1
        else:
            prev_month = today.month - 1
            prev_year = today.year
        
        month_year_str = f"{datetime(prev_year, prev_month, 1).strftime('%B %Y')}"
        logger.info(f"Generating monthly summaries for {month_year_str}")
        
        # Get all users who have entries in the previous month
        service_supabase = create_client(
            os.environ.get("SUPABASE_URL"),
            os.environ.get("SUPABASE_SECRET_KEY")
        )
        
        # Get start and end of previous month
        start_date = datetime(prev_year, prev_month, 1).isoformat()
        if prev_month == 12:
            end_date = datetime(prev_year + 1, 1, 1).isoformat()
        else:
            end_date = datetime(prev_year, prev_month + 1, 1).isoformat()
        
        # Get distinct user_ids who have entries in this month
        entries_response = service_supabase.table('entries')\
            .select('user_id')\
            .gte('created_at', start_date)\
            .lt('created_at', end_date)\
            .execute()
        
        if not entries_response.data:
            logger.info(f"No entries found for {month_year_str}")
            return
        
        # Get unique user IDs
        user_ids = list(set([entry['user_id'] for entry in entries_response.data]))
        logger.info(f"Found {len(user_ids)} users with entries in {month_year_str}")
        
        # Generate summary for each user
        success_count = 0
        for user_id in user_ids:
            try:
                success, message, data = generate_summary_for_user(
                    user_id, prev_month, prev_year, service_supabase
                )
                if success:
                    success_count += 1
                    logger.info(f"✓ {message} for user {user_id}")
                else:
                    logger.warning(f"✗ {message} for user {user_id}")
            except Exception as e:
                logger.error(f"Error processing user {user_id}: {str(e)}")
                continue
        
        logger.info(f"Monthly summary generation complete: {success_count}/{len(user_ids)} successful")
        
    except Exception as e:
        logger.exception("Error in generate_summaries_for_previous_month")
        raise

@monthly_summaries_bp.route('/generate', methods=['POST'])
@supabase_auth_required
def generate_monthly_summary():
    """Generate or retrieve monthly summary for a specific month/year"""
    data = request.get_json()
    
    if not data:
        return jsonify({'message': 'Request body is required'}), 400
    
    month = data.get('month')
    year = data.get('year')
    
    if not month or not year:
        return jsonify({'message': 'Month and year are required'}), 400
    
    try:
        user_id = g.current_user.id
        month_year = f"{datetime(year, month, 1).strftime('%B %Y')}"
        
        # Check if summary already exists
        existing = g.user_supabase.table('monthly_summaries')\
            .select('*')\
            .eq('user_id', user_id)\
            .eq('month_year', month_year)\
            .execute()
        
        if existing.data and len(existing.data) > 0:
            logger.info(f"Returning existing summary for {month_year}", extra={"user_id": user_id})
            return jsonify(existing.data[0]), 200
        
        # Get entries for this month
        entries = get_entries_for_month(user_id, g.user_supabase, month, year)
        
        if not entries:
            return jsonify({'message': f'No entries found for {month_year}'}), 404
        
        # Extract user_entry_ids
        list_of_entries = [entry.get('user_entry_id') for entry in entries]
        
        # Generate summary
        logger.info(f"Generating summary for {month_year} with {len(entries)} entries", extra={"user_id": user_id})
        summary = generate_summary(entries, month_year)
        
        # Save to database
        summary_data = {
            'user_id': user_id,
            'month_year': month_year,
            'list_of_entries': list_of_entries,
            'summary': summary
        }
        
        response = g.user_supabase.table('monthly_summaries').insert(summary_data).execute()
        
        if response.data:
            logger.info(f"Summary created for {month_year}", extra={"user_id": user_id})
            return jsonify(response.data[0]), 201
        else:
            return jsonify({'message': 'Failed to save summary'}), 500
            
    except Exception as e:
        logger.exception("Error generating monthly summary", extra={"user_id": g.current_user.id})
        return jsonify({'message': f'Error generating summary: {str(e)}'}), 500

@monthly_summaries_bp.route('', methods=['GET'])
@supabase_auth_required
def get_monthly_summaries():
    """Get all monthly summaries for the current user"""
    try:
        user_id = g.current_user.id
        response = g.user_supabase.table('monthly_summaries')\
            .select('*')\
            .eq('user_id', user_id)\
            .order('month_year', desc=True)\
            .execute()
        
        return jsonify(response.data if response.data else []), 200
    except Exception as e:
        logger.exception("Error getting monthly summaries", extra={"user_id": g.current_user.id})
        return jsonify({'message': f'Error getting summaries: {str(e)}'}), 500

@monthly_summaries_bp.route('/<month_year>', methods=['GET'])
@supabase_auth_required
def get_monthly_summary(month_year):
    """Get a specific monthly summary by month_year"""
    try:
        user_id = g.current_user.id
        response = g.user_supabase.table('monthly_summaries')\
            .select('*')\
            .eq('user_id', user_id)\
            .eq('month_year', month_year)\
            .execute()
        
        if not response.data or len(response.data) == 0:
            return jsonify({'message': 'Summary not found'}), 404
        
        return jsonify(response.data[0]), 200
    except Exception as e:
        logger.exception("Error getting monthly summary", extra={"user_id": g.current_user.id})
        return jsonify({'message': f'Error getting summary: {str(e)}'}), 500

