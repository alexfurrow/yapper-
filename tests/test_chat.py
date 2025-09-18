"""
Tests for AI chat functionality.
"""
import pytest
import json
from unittest.mock import Mock, patch

class TestChatFunctionality:
    """Test AI chat functionality."""
    
    def test_chat_success(self, test_app, mock_supabase, mock_openai, sample_user, sample_entry):
        """Test successful chat interaction."""
        # Mock authentication
        mock_supabase.auth.get_user.return_value = Mock(user=Mock(id=sample_user['id']))
        
        # Mock vector search
        with patch('backend.routes.chat.search_by_text') as mock_search:
            mock_search.return_value = [{
                'user_entry_id': sample_entry['user_entry_id'],
                'similarity': 0.85,
                'processed': sample_entry['processed']
            }]
            
            # Mock OpenAI response
            mock_openai.chat.completions.create.return_value = Mock(
                choices=[Mock(message=Mock(content="This is a test AI response."))]
            )
            
            response = test_app.post('/api/chat/chat',
                headers={'Authorization': 'Bearer test-token'},
                json={'message': 'What did I write about today?'}
            )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'response' in data
            assert data['response'] == "This is a test AI response."
            assert 'sources' in data
            assert len(data['sources']) == 1
    
    def test_chat_missing_message(self, test_app, mock_supabase, sample_user):
        """Test chat with missing message."""
        # Mock authentication
        mock_supabase.auth.get_user.return_value = Mock(user=Mock(id=sample_user['id']))
        
        response = test_app.post('/api/chat/chat',
            headers={'Authorization': 'Bearer test-token'},
            json={}
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'Message is required' in data['error']
    
    def test_chat_unauthorized(self, test_app):
        """Test chat without authentication."""
        response = test_app.post('/api/chat/chat',
            json={'message': 'Test message'}
        )
        
        assert response.status_code == 401
    
    def test_chat_no_context(self, test_app, mock_supabase, mock_openai, sample_user):
        """Test chat when no relevant entries are found."""
        # Mock authentication
        mock_supabase.auth.get_user.return_value = Mock(user=Mock(id=sample_user['id']))
        
        # Mock empty search results
        with patch('backend.routes.chat.search_by_text') as mock_search:
            mock_search.return_value = []
            
            # Mock OpenAI response
            mock_openai.chat.completions.create.return_value = Mock(
                choices=[Mock(message=Mock(content="I don't have any relevant journal entries to reference."))]
            )
            
            response = test_app.post('/api/chat/chat',
                headers={'Authorization': 'Bearer test-token'},
                json={'message': 'What did I write about today?'}
            )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'response' in data
            assert 'sources' in data
            assert len(data['sources']) == 0

class TestVectorSearch:
    """Test vector search functionality."""
    
    def test_search_by_text(self, sample_entry):
        """Test vector search functionality."""
        with patch('backend.services.embedding.supabase') as mock_supabase:
            # Mock Supabase query
            mock_table = Mock()
            mock_supabase.table.return_value = mock_table
            mock_table.select.return_value = mock_table
            mock_table.eq.return_value = mock_table
            mock_table.not_null.return_value = mock_table
            mock_table.execute.return_value = Mock(data=[sample_entry])
            
            # Mock embedding generation
            with patch('backend.services.embedding.generate_embedding') as mock_embedding:
                mock_embedding.return_value = sample_entry['vectors']
                
                # Mock cosine similarity calculation
                with patch('backend.services.embedding.cosine_similarity') as mock_similarity:
                    mock_similarity.return_value = 0.85
                    
                    from backend.services.embedding import search_by_text
                    
                    results = search_by_text("test query", limit=1, user_id=sample_entry['user_id'])
                    
                    assert len(results) == 1
                    assert results[0]['user_entry_id'] == sample_entry['user_entry_id']
                    assert results[0]['similarity'] == 0.85

class TestAuthentication:
    """Test authentication functionality."""
    
    def test_valid_token(self, test_app, mock_supabase, sample_user):
        """Test with valid authentication token."""
        # Mock successful authentication
        mock_supabase.auth.get_user.return_value = Mock(user=Mock(id=sample_user['id']))
        
        # Mock Supabase query
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.order.return_value = mock_table
        mock_table.execute.return_value = Mock(data=[])
        
        response = test_app.get('/api/entries',
            headers={'Authorization': 'Bearer valid-token'}
        )
        
        assert response.status_code == 200
    
    def test_invalid_token(self, test_app, mock_supabase):
        """Test with invalid authentication token."""
        # Mock failed authentication
        mock_supabase.auth.get_user.return_value = Mock(user=None)
        
        response = test_app.get('/api/entries',
            headers={'Authorization': 'Bearer invalid-token'}
        )
        
        assert response.status_code == 401
    
    def test_missing_token(self, test_app):
        """Test with missing authentication token."""
        response = test_app.get('/api/entries')
        
        assert response.status_code == 401
    
    def test_malformed_token(self, test_app):
        """Test with malformed authentication token."""
        response = test_app.get('/api/entries',
            headers={'Authorization': 'InvalidFormat token'}
        )
        
        assert response.status_code == 401
