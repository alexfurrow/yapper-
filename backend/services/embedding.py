"""
Embedding service for generating vector embeddings using OpenAI API.
Handles embedding generation and vectorization of entries.
"""

from openai import OpenAI
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

__all__ = ['generate_embedding', 'vectorize_all_entries']

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
