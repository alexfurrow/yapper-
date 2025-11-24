"""Service for permanently deleting entries that have been soft-deleted for 30+ days"""
from datetime import datetime, timedelta
import os
from supabase import create_client, Client
from backend.config.logging import get_logger

logger = get_logger(__name__)

def permanently_delete_old_entries():
    """Permanently delete entries that have been soft-deleted for 30+ days"""
    try:
        # Initialize Supabase client with service role key for admin operations
        supabase: Client = create_client(
            os.environ.get("SUPABASE_URL"),
            os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        )
        
        # Calculate the cutoff date (30 days ago)
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        cutoff_date_str = cutoff_date.isoformat()
        
        logger.info("Starting permanent deletion of old entries", extra={
            "cutoff_date": cutoff_date_str
        })
        
        # Find all entries that were deleted 30+ days ago
        # We need to query entries where deleted_at is not null and is <= cutoff_date
        response = supabase.table('entries').select('user_and_entry_id, deleted_at, user_id').not_.is_('deleted_at', 'null').lte('deleted_at', cutoff_date_str).execute()
        
        entries_to_delete = response.data if response.data else []
        
        if not entries_to_delete:
            logger.info("No entries found for permanent deletion", extra={
                "cutoff_date": cutoff_date_str
            })
            return {'deleted_count': 0, 'message': 'No entries to delete'}
        
        logger.info(f"Found {len(entries_to_delete)} entries to permanently delete", extra={
            "count": len(entries_to_delete),
            "cutoff_date": cutoff_date_str
        })
        
        # Delete entries in batches (Supabase has limits on batch operations)
        deleted_count = 0
        batch_size = 100
        
        for i in range(0, len(entries_to_delete), batch_size):
            batch = entries_to_delete[i:i + batch_size]
            entry_ids = [entry['user_and_entry_id'] for entry in batch]
            
            # Permanently delete the batch
            for entry_id in entry_ids:
                try:
                    supabase.table('entries').delete().eq('user_and_entry_id', entry_id).execute()
                    deleted_count += 1
                except Exception as e:
                    logger.error(f"Error deleting entry {entry_id}", extra={
                        "entry_id": entry_id,
                        "error": str(e)
                    })
        
        logger.info("Permanent deletion completed", extra={
            "deleted_count": deleted_count,
            "total_found": len(entries_to_delete)
        })
        
        return {
            'deleted_count': deleted_count,
            'total_found': len(entries_to_delete),
            'message': f'Successfully deleted {deleted_count} entries'
        }
        
    except Exception as e:
        logger.exception("Error in permanent deletion process", extra={
            "error": str(e)
        })
        raise

