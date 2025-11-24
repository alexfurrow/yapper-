"""
Tests for embedding and vector search functionality.
"""
import pytest
import numpy as np
from unittest.mock import Mock, patch

class TestEmbeddingGeneration:
    """Test embedding generation functionality."""
    
    def test_generate_embedding_success(self):
        """Test successful embedding generation."""
        with patch('backend.services.embedding.client') as mock_client:
            # Mock OpenAI response
            mock_client.embeddings.create.return_value = Mock(
                data=[Mock(embedding=[0.1, 0.2, 0.3] * 1536)]
            )
            
            from backend.services.embedding import generate_embedding
            
            result = generate_embedding("Test text for embedding")
            
            assert result is not None
            assert len(result) == 1536
            assert result[0] == 0.1
            assert result[1] == 0.2
            assert result[2] == 0.3
    
    def test_generate_embedding_failure(self):
        """Test embedding generation failure."""
        with patch('backend.services.embedding.client') as mock_client:
            # Mock OpenAI error
            mock_client.embeddings.create.side_effect = Exception("API Error")
            
            from backend.services.embedding import generate_embedding
            
            result = generate_embedding("Test text")
            
            assert result is None
    
    def test_generate_embedding_empty_text(self):
        """Test embedding generation with empty text."""
        from backend.services.embedding import generate_embedding
        
        result = generate_embedding("")
        
        assert result is None

class TestVectorSearch:
    """Test vector search functionality."""
    
    def test_search_by_text_success(self, sample_entry):
        """Test successful vector search."""
        with patch('backend.services.context_retrieval.search_similar') as mock_search:
            # Mock HNSW search results
            mock_search.return_value = [{**sample_entry, 'similarity': 0.85}]
            
            from backend.services.context_retrieval import search_by_text
            
            results = search_by_text("test query", limit=1, user_id=sample_entry['user_id'])
            
            assert len(results) == 1
            assert results[0]['user_entry_id'] == sample_entry['user_entry_id']
            assert results[0]['similarity'] == 0.85
    
    def test_search_by_text_no_entries(self):
        """Test vector search with no entries."""
        with patch('backend.services.context_retrieval.search_similar') as mock_search:
            mock_search.return_value = []
            
            from backend.services.context_retrieval import search_by_text
            
            results = search_by_text("test query", limit=1, user_id="test-user")
            
            assert len(results) == 0
    
    def test_search_by_text_embedding_failure(self):
        """Test vector search when embedding generation fails."""
        with patch('backend.services.embedding.generate_embedding') as mock_embedding:
            mock_embedding.return_value = None
            
            from backend.services.context_retrieval import search_by_text
            
            results = search_by_text("test query", limit=1, user_id="test-user")
            
            assert len(results) == 0

class TestTextProcessing:
    """Test text processing functionality."""
    
    def test_process_text_success(self):
        """Test successful text processing."""
        with patch('backend.services.initial_processing.client') as mock_client:
            # Mock OpenAI response
            mock_client.chat.completions.create.return_value = Mock(
                choices=[Mock(message=Mock(content="Processed text content"))]
            )
            
            from backend.services.initial_processing import process_text
            
            result = process_text("Original text content")
            
            assert result == "Processed text content"
    
    def test_process_text_failure(self):
        """Test text processing failure."""
        with patch('backend.services.initial_processing.client') as mock_client:
            # Mock OpenAI error
            mock_client.chat.completions.create.side_effect = Exception("API Error")
            
            from backend.services.initial_processing import process_text
            
            result = process_text("Original text content")
            
            assert result is None
    
    def test_process_text_empty_input(self):
        """Test text processing with empty input."""
        from backend.services.initial_processing import process_text
        
        result = process_text("")
        
        assert result is None
