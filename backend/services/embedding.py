from openai import OpenAI
from flask import current_app
import numpy as np
import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Force reload the .env file
load_dotenv(override=True)

# Initialize the clients
client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

# Initialize Supabase client
supabase_url = os.environ.get('SUPABASE_URL')
supabase_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
supabase: Client = create_client(supabase_url, supabase_key)

__all__ = ['search_by_text', 'generate_embedding', 'vectorize_all_entries']

def generate_embedding(text):
    """Generate embedding for a single text using OpenAI API"""
    try:
        response = client.embeddings.create(
            model="text-embedding-3-large",
            input=text,
            dimensions=1536  # Specify dimensions for the embedding
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error generating embedding: {str(e)}")
        return None

def vectorize_all_entries():
    """Generate embeddings for all entries in the database"""
    try:
        # Get all entries that don't have vectors yet from Supabase
        response = supabase.table('entries').select('*').is_('vectors', 'null').not_.is_('processed', 'null').execute()
        vectorless = response.data
        
        for entry in vectorless:
            if entry.get('processed'):
                # Generate embedding for processed text
                embedding = generate_embedding(entry['processed'])
                if embedding:
                    # Store embedding in Supabase
                    supabase.table('entries').update({
                        'vectors': embedding
                    }).eq('entry_id', entry['entry_id']).execute()
        return True
    except Exception as e:
        print(f"Error vectorizing entries: {str(e)}")
        return False

def search_by_text(query_text, limit=5, user_id=None, user_client=None):
    """Find entries with similar content to the query text"""
    try:
        # Generate embedding for query text
        query_embedding = generate_embedding(query_text)
        if not query_embedding:
            return []
        
        # Convert to numpy array for calculations
        query_vector = np.array(query_embedding)
        
        # Use user client if provided, otherwise fall back to service client
        client = user_client if user_client else supabase
        
        # Build Supabase query with proper filtering
        query = client.table('entries').select('*').not_.is_('vectors', 'null')
        
        # Add user_id filter if provided
        if user_id is not None:
            query = query.eq('user_id', user_id)
        
        # Get all matching entries
        response = query.execute()
        all_entries = response.data
        
        # Debug logging
        print(f"DEBUG: search_by_text found {len(all_entries) if all_entries else 0} entries for user_id={user_id}")
        if all_entries:
            print(f"DEBUG: First entry keys: {list(all_entries[0].keys())}")
            print(f"DEBUG: First entry user_id: {all_entries[0].get('user_id')}")
        
        if not all_entries:
            return []
        
        # Calculate cosine similarity
        similarities = []
        for entry in all_entries:
            entry_vector = np.array(entry['vectors'])
            # Cosine similarity = dot product / (norm(A) * norm(B))
            similarity = np.dot(query_vector, entry_vector) / (np.linalg.norm(query_vector) * np.linalg.norm(entry_vector))
            similarities.append((entry, similarity))
        
        # Sort by similarity (highest first)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Return top N results with similarity scores
        results = []
        for entry, similarity in similarities[:limit]:
            entry['similarity'] = float(similarity)  # Add similarity score to the dictionary
            results.append(entry)
            
        return results
    except Exception as e:
        print(f"Error finding similar entries: {str(e)}")
        return [] 