import hnswlib
import numpy as np
import os
import pickle
from flask import current_app
# SQLAlchemy references removed - using Supabase
from supabase import create_client, Client

class HNSWIndex:
    def __init__(self, dim=1536, ef_construction=200, M=16):
        """Initialize HNSW index
        
        Args:
            dim: Dimensionality of vectors (1536 for OpenAI embeddings)
            ef_construction: Controls index quality vs build time (higher = better quality but slower)
            M: Controls maximum number of outgoing connections in the graph
        """
        self.dim = dim
        self.ef_construction = ef_construction
        self.M = M
        self.index = None
        self.id_to_entry_id = {}  # Maps HNSW internal IDs to database entry_ids
        self.entry_id_to_id = {}  # Maps database entry_ids to HNSW internal IDs
        
    def build_index(self):
        """Build HNSW index from all vectorized entries in the database"""
        # Initialize Supabase client
        supabase = create_client(
            os.environ.get("SUPABASE_URL"),
            os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        )
        
        # Get all entries with vectors from Supabase
        response = supabase.table('entries').select('*').not_.is_('vectors', 'null').execute()
        all_entries = response.data
        
        if not all_entries:
            print("No vectorized entries found in database")
            return False
            
        # Create new index
        self.index = hnswlib.Index(space='cosine', dim=self.dim)
        
        # Initialize with slightly more capacity than needed
        num_elements = len(all_entries)
        self.index.init_index(max_elements=num_elements + 100, ef_construction=self.ef_construction, M=self.M)
        
        # Add vectors to index
        vectors = []
        ids = []
        
        for i, entry in enumerate(all_entries):
            vectors.append(entry['vectors'])
            ids.append(i)
            self.id_to_entry_id[i] = entry['entry_id']
            self.entry_id_to_id[entry['entry_id']] = i
            
        self.index.add_items(np.array(vectors), ids)
        
        # Set search parameters
        self.index.set_ef(50)  # ef parameter controls search speed vs accuracy tradeoff
        
        print(f"Built HNSW index with {num_elements} vectors")
        return True
        
    def search(self, query_vector, k=5):
        """Search for k nearest neighbors to query_vector
        
        Args:
            query_vector: Vector to search for
            k: Number of nearest neighbors to return
            
        Returns:
            List of dictionaries with entry_id and distance
        """
        if self.index is None:
            print("Index not built yet")
            return []
            
        # Convert query vector to numpy array
        query_vector = np.array(query_vector)
        
        # Search index
        labels, distances = self.index.knn_query(query_vector, k=min(k, len(self.id_to_entry_id)))
        
        # Convert to list of dictionaries
        results = []
        for i in range(len(labels[0])):
            internal_id = labels[0][i]
            entry_id = self.id_to_entry_id[internal_id]
            distance = distances[0][i]
            results.append({
                'entry_id': entry_id,
                'distance': float(distance)  # Convert numpy float to Python float for JSON serialization
            })
            
        return results
        
    def save(self, path='hnsw_index'):
        """Save index to disk"""
        if self.index is None:
            print("Index not built yet")
            return False
            
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        # Save index
        self.index.save_index(f"{path}.bin")
        
        # Save mappings
        with open(f"{path}_mappings.pkl", 'wb') as f:
            pickle.dump({
                'id_to_entry_id': self.id_to_entry_id,
                'entry_id_to_id': self.entry_id_to_id
            }, f)
            
        return True
        
    def load(self, path='hnsw_index'):
        """Load index from disk"""
        try:
            # Create new index
            self.index = hnswlib.Index(space='cosine', dim=self.dim)
            
            # Load index
            self.index.load_index(f"{path}.bin")
            
            # Load mappings
            with open(f"{path}_mappings.pkl", 'rb') as f:
                mappings = pickle.load(f)
                self.id_to_entry_id = mappings['id_to_entry_id']
                self.entry_id_to_id = mappings['entry_id_to_id']
                
            # Set search parameters
            self.index.set_ef(50)
            
            return True
        except Exception as e:
            print(f"Error loading index: {str(e)}")
            return False

# Global index instance
index = HNSWIndex()

def build_and_save_index():
    """Build and save index"""
    success = index.build_index()
    if success:
        index.save('instance/hnsw_index')
    return success
    
def load_index():
    """Load index from disk"""
    return index.load('instance/hnsw_index')
    
def search_similar(query_vector, k=5):
    """Search for similar entries"""
    # Try to load index if not already loaded
    if index.index is None:
        if not load_index():
            if not build_and_save_index():
                return []
    
    return index.search(query_vector, k=k) 