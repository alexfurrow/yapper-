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
        
    def add_entry(self, entry_id, vector):
        """Add a single entry to the index (for incremental updates)
        
        Args:
            entry_id: Database entry_id
            vector: Embedding vector for the entry
        """
        if self.index is None:
            # Initialize index if it doesn't exist
            self.index = hnswlib.Index(space='cosine', dim=self.dim)
            self.index.init_index(max_elements=1000, ef_construction=self.ef_construction, M=self.M)
            self.index.set_ef(50)
        
        # Check if entry already exists
        if entry_id in self.entry_id_to_id:
            # Entry already in index, skip
            return False
        
        # Check if we need to resize the index
        current_count = len(self.id_to_entry_id)
        try:
            max_elements = self.index.max_elements
            current_elements = self.index.element_count
            
            # Resize if needed (add 100 more capacity)
            if current_elements >= max_elements:
                try:
                    new_max = max_elements + 100
                    self.index.resize_index(new_max)
                except Exception as e:
                    print(f"Warning: Could not resize index: {str(e)}. Rebuilding index...")
                    # If resize fails, rebuild the index
                    return False
        except AttributeError:
            # If we can't check, just try to add and let it fail gracefully
            pass
        
        # Get current count to use as internal ID
        internal_id = len(self.id_to_entry_id)
        
        # Add to index
        self.index.add_items(np.array([vector]), [internal_id])
        
        # Update mappings
        self.id_to_entry_id[internal_id] = entry_id
        self.entry_id_to_id[entry_id] = internal_id
        
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
            
        if len(self.id_to_entry_id) == 0:
            return []
            
        # Convert query vector to numpy array
        query_vector = np.array(query_vector)
        
        # Search index - search for more results than needed to account for user filtering
        search_k = min(k * 3, len(self.id_to_entry_id))  # Get 3x results to filter by user
        labels, distances = self.index.knn_query(query_vector, k=search_k)
        
        # Convert to list of dictionaries
        results = []
        for i in range(len(labels[0])):
            internal_id = labels[0][i]
            entry_id = self.id_to_entry_id[internal_id]
            distance = distances[0][i]
            # Convert distance to similarity (1 - distance for cosine similarity)
            similarity = 1.0 - float(distance)
            results.append({
                'entry_id': entry_id,
                'distance': float(distance),
                'similarity': similarity
            })
            
        return results
        
    def save(self, path='hnsw_index'):
        """Save index to disk"""
        if self.index is None:
            print("Index not built yet")
            return False
            
        # Create directory if it doesn't exist
        dir_path = os.path.dirname(path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        
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
    
def search_similar(query_vector, k=5, user_id=None, user_client=None):
    """Search for similar entries using HNSW index
    
    Args:
        query_vector: Embedding vector to search for
        k: Number of results to return
        user_id: Optional user_id to filter results
        user_client: Optional Supabase client for user-specific queries
        
    Returns:
        List of entry dictionaries with similarity scores
    """
    # Try to load index if not already loaded
    if index.index is None:
        if not load_index():
            if not build_and_save_index():
                return []
    
    # Search index
    candidates = index.search(query_vector, k=k * 3 if user_id else k)  # Get more if filtering by user
    
    if not candidates:
        return []
    
    # If no user filtering needed, fetch entries and return
    if user_id is None:
        # Fetch full entry data from Supabase
        supabase = create_client(
            os.environ.get("SUPABASE_URL"),
            os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        )
        
        entry_ids = [c['entry_id'] for c in candidates[:k]]
        response = supabase.table('entries').select('*').in_('entry_id', entry_ids).execute()
        entries = response.data if response.data else []
        
        # Match entries with similarity scores
        entry_map = {e['entry_id']: e for e in entries}
        results = []
        for candidate in candidates[:k]:
            if candidate['entry_id'] in entry_map:
                entry = entry_map[candidate['entry_id']]
                entry['similarity'] = candidate['similarity']
                results.append(entry)
        
        return results
    
    # Filter by user_id - fetch entries and filter
    client = user_client if user_client else create_client(
        os.environ.get("SUPABASE_URL"),
        os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    )
    
    entry_ids = [c['entry_id'] for c in candidates]
    response = client.table('entries').select('*').in_('entry_id', entry_ids).eq('user_id', user_id).execute()
    entries = response.data if response.data else []
    
    # Match entries with similarity scores and sort by similarity
    entry_map = {e['entry_id']: e for e in entries}
    results = []
    for candidate in candidates:
        if candidate['entry_id'] in entry_map:
            entry = entry_map[candidate['entry_id']]
            entry['similarity'] = candidate['similarity']
            results.append(entry)
    
    # Sort by similarity (highest first) and return top k
    results.sort(key=lambda x: x['similarity'], reverse=True)
    return results[:k]

def add_entry_to_index(entry_id, vector):
    """Add a single entry to the index (for incremental updates)
    
    Args:
        entry_id: Database entry_id
        vector: Embedding vector for the entry
    
    Returns:
        True if successful, False otherwise (index will be rebuilt on next search)
    """
    try:
        # Try to load index if not already loaded
        if index.index is None:
            if not load_index():
                # If no index exists, we'll build it on next search
                return False
        
        success = index.add_entry(entry_id, vector)
        if success:
            # Save updated index
            index.save('instance/hnsw_index')
        return success
    except Exception as e:
        print(f"Error adding entry to index: {str(e)}. Index will be rebuilt on next search.")
        # Clear the index so it gets rebuilt on next search
        index.index = None
        return False 