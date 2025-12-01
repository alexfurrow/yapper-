import hnswlib
import numpy as np
import os
import pickle
from flask import current_app
# SQLAlchemy references removed - using Supabase
from supabase import create_client, Client
from dotenv import load_dotenv

# Force reload the .env file to ensure environment variables are loaded
load_dotenv(override=True)

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
        try:
            # Initialize Supabase client
            supabase_url = os.environ.get("SUPABASE_URL")
            supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
            
            print(f"[build_index] Supabase URL: {supabase_url[:30]}..." if supabase_url else "[build_index] ERROR: SUPABASE_URL not set")
            print(f"[build_index] Service key present: {bool(supabase_key)}")
            
            # Debug: Show first few characters of service key to verify it's loaded
            if supabase_key:
                print(f"[build_index] Service key starts with: {supabase_key[:20]}... (length: {len(supabase_key)})")
                # Service role keys typically start with "eyJ" (JWT) and are much longer than anon keys
                if not supabase_key.startswith("eyJ"):
                    print("[build_index] WARNING: Service key doesn't start with 'eyJ' - might be anon key instead!")
            
            if not supabase_url or not supabase_key:
                print("[build_index] ERROR: Missing Supabase credentials")
                return False
            
            supabase = create_client(supabase_url, supabase_key)
            
            # First, test if we can query ANY entries at all (without filters)
            print("[build_index] Testing basic query to verify Supabase connection...")
            test_response = supabase.table('entries').select('user_and_entry_id').limit(1).execute()
            test_entries = test_response.data if test_response.data else []
            print(f"[build_index] Basic test query returned {len(test_entries)} entries")
            
            if test_entries:
                print(f"[build_index] Sample entry ID: {test_entries[0].get('user_and_entry_id')}")
            
            # Get all entries with vectors from Supabase
            print("[build_index] Querying Supabase for entries with vectors...")
            
            # Try multiple query approaches to find entries with vectors
            # Approach 1: Use not_.is_('vectors', 'null')
            try:
                response = supabase.table('entries').select('*').not_.is_('vectors', 'null').execute()
                all_entries = response.data if response.data else []
                print(f"[build_index] Query 1 (not_.is_): Found {len(all_entries)} entries")
            except Exception as e:
                print(f"[build_index] Query 1 failed: {str(e)}")
                all_entries = []
            
            # Approach 2: If first query returns nothing, try getting all entries and filter manually
            if not all_entries:
                print("[build_index] Query 1 returned no results, trying alternative query...")
                try:
                    # Get a sample of entries to check
                    sample_response = supabase.table('entries').select('user_and_entry_id, vectors').limit(10).execute()
                    sample_entries = sample_response.data if sample_response.data else []
                    print(f"[build_index] Sample query returned {len(sample_entries)} entries")
                    
                    # Check if any have vectors
                    entries_with_vectors = [e for e in sample_entries if e.get('vectors') is not None]
                    print(f"[build_index] Sample entries with vectors: {len(entries_with_vectors)}")
                    
                    if entries_with_vectors:
                        # If sample has vectors, try getting all with a different query
                        print("[build_index] Sample shows vectors exist, trying full query...")
                        full_response = supabase.table('entries').select('*').execute()
                        all_entries = [e for e in (full_response.data if full_response.data else []) if e.get('vectors') is not None]
                        print(f"[build_index] Full query with manual filter: Found {len(all_entries)} entries with vectors")
                except Exception as e:
                    print(f"[build_index] Alternative query failed: {str(e)}")
                    import traceback
                    traceback.print_exc()
            
            if not all_entries:
                print("[build_index] ERROR: No vectorized entries found in database")
                # Check total entries to see if any exist at all
                try:
                    total_response = supabase.table('entries').select('user_and_entry_id', count='exact').execute()
                    total_count = total_response.count if hasattr(total_response, 'count') else 0
                    print(f"[build_index] Total entries in database: {total_count}")
                    
                    # Check entries without vectors
                    no_vectors_response = supabase.table('entries').select('user_and_entry_id', count='exact').is_('vectors', 'null').execute()
                    no_vectors_count = no_vectors_response.count if hasattr(no_vectors_response, 'count') else 0
                    print(f"[build_index] Entries without vectors: {no_vectors_count}")
                    
                    # Try to get a few entries to inspect
                    inspect_response = supabase.table('entries').select('user_and_entry_id, vectors').limit(5).execute()
                    inspect_entries = inspect_response.data if inspect_response.data else []
                    print(f"[build_index] Sample entries for inspection: {len(inspect_entries)}")
                    for entry in inspect_entries:
                        has_vectors = entry.get('vectors') is not None
                        print(f"[build_index]   Entry {entry.get('user_and_entry_id')}: vectors={'present' if has_vectors else 'null'}")
                except Exception as e:
                    print(f"[build_index] Error checking entry counts: {str(e)}")
                    import traceback
                    traceback.print_exc()
                return False
            
            print(f"[build_index] Found {len(all_entries)} entries with vectors, building index...")
                
            # Create new index
            self.index = hnswlib.Index(space='cosine', dim=self.dim)
            
            # Initialize with slightly more capacity than needed
            num_elements = len(all_entries)
            self.index.init_index(max_elements=num_elements + 100, ef_construction=self.ef_construction, M=self.M)
            
            # Add vectors to index
            vectors = []
            ids = []
            
            for i, entry in enumerate(all_entries):
                entry_id = entry.get('user_and_entry_id')  # Primary key is 'user_and_entry_id'
                if not entry_id:
                    print(f"Warning: Entry missing 'user_and_entry_id' field, skipping")
                    continue
                vector = entry.get('vectors')
                
                # Validate vector
                if not vector:
                    print(f"Warning: Entry {entry_id} has null/empty vector, skipping")
                    continue
                
                # Ensure vector is a list/array and has correct length
                if not isinstance(vector, (list, np.ndarray)):
                    print(f"Warning: Entry {entry_id} has invalid vector type {type(vector)}, skipping")
                    continue
                
                vector_array = np.array(vector, dtype=np.float32)
                if len(vector_array) != self.dim:
                    print(f"Warning: Entry {entry_id} has vector with wrong dimension {len(vector_array)} (expected {self.dim}), skipping")
                    continue
                
                vectors.append(vector_array)
                ids.append(i)
                self.id_to_entry_id[i] = entry_id
                self.entry_id_to_id[entry_id] = i
            
            if not vectors:
                print("No valid vectors found to add to index")
                return False
                
            self.index.add_items(np.array(vectors), ids)
            
            # Set search parameters
            self.index.set_ef(50)  # ef parameter controls search speed vs accuracy tradeoff
            
            print(f"Built HNSW index with {len(vectors)} vectors (out of {num_elements} entries)")
            return True
        except Exception as e:
            print(f"[build_index] ERROR: Exception during index build: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
        
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
        except FileNotFoundError:
            # Index file doesn't exist yet - this is normal for first run
            return False
        except Exception as e:
            print(f"Error loading index: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

# Global index instance
index = HNSWIndex()

def build_and_save_index():
    """Build and save index"""
    print("[build_and_save_index] Starting index build...")
    try:
        success = index.build_index()
        if success:
            print("[build_and_save_index] Index built successfully, saving...")
            try:
                save_success = index.save('instance/hnsw_index')
                if save_success:
                    print("[build_and_save_index] Index saved successfully")
                    return True
                else:
                    print("[build_and_save_index] WARNING: Index build succeeded but save failed")
                    return False
            except Exception as save_error:
                print(f"[build_and_save_index] ERROR: Index build succeeded but save failed with exception: {str(save_error)}")
                import traceback
                traceback.print_exc()
                return False
        else:
            print("[build_and_save_index] ERROR: Index build failed (returned False)")
            return False
    except Exception as e:
        print(f"[build_and_save_index] ERROR: Index build failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
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
    import logging
    index_logger = logging.getLogger(__name__)
    index_logger.info(f"[search_similar] Starting search, user_id={user_id}, k={k}")
    
    # Try to load index if not already loaded
    if index.index is None:
        index_logger.info("[search_similar] Index not loaded, attempting to load...")
        if not load_index():
            index_logger.info("[search_similar] Failed to load index, building new index...")
            if not build_and_save_index():
                index_logger.error("[search_similar] ERROR: Failed to build index")
                return []
        else:
            index_logger.info("[search_similar] Index loaded successfully")
    else:
        index_logger.info(f"[search_similar] Index already loaded, has {len(index.id_to_entry_id)} entries")
    
    # Search index
    index_logger.info(f"[search_similar] Searching index for {k * 3 if user_id else k} candidates...")
    candidates = index.search(query_vector, k=k * 3 if user_id else k)  # Get more if filtering by user
    
    index_logger.info(f"[search_similar] Index search returned {len(candidates)} candidates")
    if not candidates:
        index_logger.warning("[search_similar] No candidates found from index search")
        return []
    
    # If no user filtering needed, fetch entries and return
    if user_id is None:
        # Fetch full entry data from Supabase
        supabase = create_client(
            os.environ.get("SUPABASE_URL"),
            os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        )
        
        entry_ids = [c['entry_id'] for c in candidates[:k]]
        response = supabase.table('entries').select('*').in_('user_and_entry_id', entry_ids).execute()
        entries = response.data if response.data else []
        
        # Match entries with similarity scores
        entry_map = {e.get('user_and_entry_id'): e for e in entries}
        results = []
        for candidate in candidates[:k]:
            candidate_id = candidate['entry_id']
            if candidate_id in entry_map:
                entry = entry_map[candidate_id]
                entry['similarity'] = candidate['similarity']
                results.append(entry)
        
        return results
    
    # Filter by user_id - fetch entries and filter
    client = user_client if user_client else create_client(
        os.environ.get("SUPABASE_URL"),
        os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    )
    
    entry_ids = [c['entry_id'] for c in candidates]
    index_logger.info(f"[search_similar] Filtering {len(entry_ids)} candidates by user_id={user_id}")
    response = client.table('entries').select('*').in_('user_and_entry_id', entry_ids).eq('user_id', user_id).execute()
    entries = response.data if response.data else []
    index_logger.info(f"[search_similar] Database query returned {len(entries)} entries for user_id={user_id}")
    
    # Match entries with similarity scores and sort by similarity
    entry_map = {e.get('user_and_entry_id'): e for e in entries}
    results = []
    for candidate in candidates:
        candidate_id = candidate['entry_id']
        if candidate_id in entry_map:
            entry = entry_map[candidate_id]
            entry['similarity'] = candidate['similarity']
            results.append(entry)
    
    index_logger.info(f"[search_similar] Matched {len(results)} entries after filtering")
    
    # Sort by similarity (highest first) and return top k
    results.sort(key=lambda x: x['similarity'], reverse=True)
    final_results = results[:k]
    index_logger.info(f"[search_similar] Returning {len(final_results)} final results")
    return final_results

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