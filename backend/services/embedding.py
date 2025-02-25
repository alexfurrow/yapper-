from openai import OpenAI
from flask import current_app
import numpy as np
import os
from dotenv import load_dotenv
from extensions import db
from backend.models.Page_Table import Page_Table
from backend.services.hnsw_index import build_and_save_index, search_similar

# Force reload the .env file
load_dotenv(override=True)

# Initialize the client with the API key from .env
client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

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

def vectorize_all_pages():
    """Generate embeddings for all pages in the database"""
    try:
        # Get all pages that don't have vectors yet
        pages = Page_Table.query.filter(
            Page_Table.processed.isnot(None),
            Page_Table.vectors.is_(None)
        ).all()
        
        print(f"Found {len(pages)} pages to vectorize")
        
        for page in pages:
            if page.processed:
                # Generate embedding for processed text
                embedding = generate_embedding(page.processed)
                if embedding:
                    # Store embedding in database
                    page.vectors = embedding
                    print(f"Generated embedding for page {page.entry_id}")
            
        # Commit all changes
        db.session.commit()
        print("Vectorization complete")
        
        # Rebuild index after vectorization
        rebuild_index()
        
        return True
    except Exception as e:
        print(f"Error vectorizing pages: {str(e)}")
        db.session.rollback()
        return False

def find_similar_pages(query_text, limit=5):
    """Find pages with similar content to the query text"""
    try:
        # Generate embedding for query text
        query_embedding = generate_embedding(query_text)
        if not query_embedding:
            return []
        
        # Convert to numpy array for calculations
        query_vector = np.array(query_embedding)
        
        # Get all pages with vectors
        pages = Page_Table.query.filter(Page_Table.vectors.isnot(None)).all()
        
        # Calculate cosine similarity
        similarities = []
        for page in pages:
            page_vector = np.array(page.vectors)
            # Cosine similarity = dot product / (norm(A) * norm(B))
            similarity = np.dot(query_vector, page_vector) / (np.linalg.norm(query_vector) * np.linalg.norm(page_vector))
            similarities.append((page, similarity))
        
        # Sort by similarity (highest first)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Return top N results
        return [page.to_dict() for page, _ in similarities[:limit]]
    except Exception as e:
        print(f"Error finding similar pages: {str(e)}")
        return []

def rebuild_index():
    """Rebuild the HNSW index"""
    return build_and_save_index()

def search_by_text(query_text, limit=5):
    """Search for pages similar to query text"""
    # Generate embedding for query text
    query_embedding = generate_embedding(query_text)
    if not query_embedding:
        return []
    
    # Search using HNSW index
    similar_ids = search_similar(query_embedding, k=limit)
    
    # Get page details
    results = []
    for item in similar_ids:
        page = Page_Table.query.get(item['entry_id'])
        if page:
            page_dict = page.to_dict()
            page_dict['similarity'] = 1.0 - item['distance']  # Convert distance to similarity score
            results.append(page_dict)
    
    return results 