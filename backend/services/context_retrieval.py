"""
Context retrieval service for finding similar entries using vector embeddings.
Uses HNSW index for fast similarity search with fallback to brute-force.
"""

import numpy as np
import os
from supabase import create_client, Client
from backend.services.embedding import generate_embedding

# Initialize Supabase client for fallback search
supabase_url = os.environ.get('SUPABASE_URL')
supabase_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
supabase: Client = create_client(supabase_url, supabase_key)

__all__ = ['search_by_text']


def search_by_text(query_text, limit=5, user_id=None, user_client=None):
    """Find entries with similar content to the query text using HNSW index
    
    Args:
        query_text: Text query to search for
        limit: Maximum number of results to return
        user_id: Optional user_id to filter results
        user_client: Optional Supabase client for user-specific queries
    
    Returns:
        List of entry dictionaries with similarity scores
    """
    try:
        # Generate embedding for query text
        query_embedding = generate_embedding(query_text)
        if not query_embedding:
            return []
        
        # Use HNSW index for fast similarity search
        from backend.services.hnsw_index import search_similar
        results = search_similar(query_embedding, k=limit, user_id=user_id, user_client=user_client)
        
        return results
    except Exception as e:
        print(f"Error finding similar entries: {str(e)}")
        # Fallback to brute-force if HNSW fails
        try:
            return _brute_force_search(query_text, limit, user_id, user_client)
        except Exception as e2:
            print(f"Fallback search also failed: {str(e2)}")
            return []