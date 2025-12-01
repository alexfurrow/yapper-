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
    """Vectorize all entries that have processed content but no vectors
    Flow: Only vectorize entries that have been processed (step 1 complete)
    """
    try:
        # Get all entries that have processed content but no vectors
        response = supabase.table('entries').select('*').is_('vectors', 'null').not_.is_('processed', 'null').execute()
        vectorless = response.data
        
        if not vectorless:
            print("No entries found that need vectorization (all have vectors or are missing processed content)")
            return True
        
        print(f"Found {len(vectorless)} entries that need vectorization")
        
        for i, entry in enumerate(vectorless):
            entry_id = entry.get('user_and_entry_id')  # Primary key is 'user_and_entry_id'
            if not entry_id:
                print(f"Skipping entry: missing 'user_and_entry_id' field")
                continue
            processed_content = entry.get('processed', '').strip()
            
            if not processed_content:
                print(f"Skipping entry {entry_id}: no processed content")
                continue
            
            try:
                print(f"Vectorizing entry {entry_id} ({i+1}/{len(vectorless)})...")
                # Generate embedding from processed content
                embedding = generate_embedding(processed_content)
                
                if embedding:
                    # Store embedding in Supabase
                    supabase.table('entries').update({
                        'vectors': embedding
                    }).eq('user_and_entry_id', entry_id).execute()
                    print(f"✓ Entry {entry_id} vectorized successfully")
                else:
                    print(f"✗ Failed to generate embedding for entry {entry_id}")
            except Exception as e:
                print(f"✗ Error vectorizing entry {entry_id}: {str(e)}")
                continue
        
        print(f"Vectorization complete! Processed {len(vectorless)} entries.")
        return True
    except Exception as e:
        print(f"Error vectorizing entries: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
