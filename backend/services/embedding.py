from openai import OpenAI
from flask import current_app
import numpy as np
import os
from dotenv import load_dotenv
from extensions import db
from backend.models.entries import entries

# Force reload the .env file
load_dotenv(override=True)

# Initialize the client with the API key from .env
client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

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
        # Get all entries that don't have vectors yet
        vectorless = entries.query.filter(
            entries.processed.isnot(None),
            entries.vectors.is_(None)
        ).all()
        
        print(f"Found {len(vectorless)} entries to vectorize")
        
        for entry in vectorless:
            if entry.processed:
                # Generate embedding for processed text
                embedding = generate_embedding(entry.processed)
                if embedding:
                    # Store embedding in database
                    entry.vectors = embedding
                    print(f"Generated embedding for entry {entry.entry_id}")
            
        # Commit all changes
        db.session.commit()
        print("Vectorization complete")
        return True
    except Exception as e:
        print(f"Error vectorizing entries: {str(e)}")
        db.session.rollback()
        return False

def search_by_text(query_text, limit=5, user_id=None):
    """Find entries with similar content to the query text"""
    try:
        # Generate embedding for query text
        query_embedding = generate_embedding(query_text)
        if not query_embedding:
            print("Failed to generate embedding for query text")
            return []
        
        # Convert to numpy array for calculations
        query_vector = np.array(query_embedding)
        
        # Build database query with proper filtering
        query = entries.query.filter(entries.vectors.isnot(None))
        
        # Add user_id filter if provided
        if user_id is not None:
            query = query.filter(entries.user_id == user_id)
            print(f"Filtering entries for user_id: {user_id}")
        
        # Get all matching entries
        all_entries = query.all()
        print(f"Found {len(all_entries)} entries with vectors (user_id filter: {user_id is not None})")
        
        if not all_entries:
            print("No entries found with vectors")
            return []
        
        # Calculate cosine similarity
        similarities = []
        for entry in all_entries:
            entry_vector = np.array(entry.vectors)
            # Cosine similarity = dot product / (norm(A) * norm(B))
            similarity = np.dot(query_vector, entry_vector) / (np.linalg.norm(query_vector) * np.linalg.norm(entry_vector))
            similarities.append((entry, similarity))
        
        # Sort by similarity (highest first)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Return top N results with similarity scores
        results = []
        for entry, similarity in similarities[:limit]:
            entry_dict = entry.to_dict()
            entry_dict['similarity'] = float(similarity)  # Add similarity score to the dictionary
            results.append(entry_dict)
            
        print(f"Returning {len(results)} results with similarities: {[r['similarity'] for r in results]}")
        return results
    except Exception as e:
        print(f"Error finding similar entries: {str(e)}")
        return [] 