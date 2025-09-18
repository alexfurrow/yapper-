"""
Tests for journal entry functionality.
"""
import pytest
import json
from unittest.mock import Mock, patch

class TestEntryCreation:
    """Test journal entry creation functionality."""
    
    def test_create_entry_success(self, test_app, mock_supabase, mock_openai, sample_user, sample_entry):
        """Test successful journal entry creation."""
        # Mock the authentication
        mock_supabase.auth.get_user.return_value = Mock(user=Mock(id=sample_user['id']))
        
        # Mock the Supabase table operations
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        
        # Mock the insert operation
        mock_insert = Mock()
        mock_table.insert.return_value = mock_insert
        mock_insert.execute.return_value = Mock(data=[sample_entry])
        
        # Mock OpenAI processing
        mock_openai.chat.completions.create.return_value = Mock(
            choices=[Mock(message=Mock(content=sample_entry['processed']))]
        )
        
        # Mock embedding generation
        with patch('backend.routes.entries.generate_embedding') as mock_embedding:
            mock_embedding.return_value = sample_entry['vectors']
            
            # Make the request
            response = test_app.post('/api/entries', 
                headers={'Authorization': 'Bearer test-token'},
                json={'content': sample_entry['content']}
            )
            
            # Assertions
            assert response.status_code == 201
            data = json.loads(response.data)
            assert data['message'] == 'Entry created successfully'
            assert data['entry']['content'] == sample_entry['content']
            assert data['entry']['user_entry_id'] == sample_entry['user_entry_id']
    
    def test_create_entry_missing_content(self, test_app, mock_supabase, sample_user):
        """Test entry creation with missing content."""
        # Mock authentication
        mock_supabase.auth.get_user.return_value = Mock(user=Mock(id=sample_user['id']))
        
        # Make request without content
        response = test_app.post('/api/entries',
            headers={'Authorization': 'Bearer test-token'},
            json={}
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'Content is required' in data['message']
    
    def test_create_entry_unauthorized(self, test_app):
        """Test entry creation without authentication."""
        response = test_app.post('/api/entries',
            json={'content': 'Test content'}
        )
        
        assert response.status_code == 401

class TestEntryRetrieval:
    """Test journal entry retrieval functionality."""
    
    def test_get_entries_success(self, test_app, mock_supabase, sample_user, sample_entry):
        """Test successful entry retrieval."""
        # Mock authentication
        mock_supabase.auth.get_user.return_value = Mock(user=Mock(id=sample_user['id']))
        
        # Mock Supabase query
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.order.return_value = mock_table
        mock_table.execute.return_value = Mock(data=[sample_entry])
        
        response = test_app.get('/api/entries',
            headers={'Authorization': 'Bearer test-token'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['entries']) == 1
        assert data['entries'][0]['content'] == sample_entry['content']
    
    def test_get_entries_unauthorized(self, test_app):
        """Test entry retrieval without authentication."""
        response = test_app.get('/api/entries')
        
        assert response.status_code == 401

class TestEntryUpdate:
    """Test journal entry update functionality."""
    
    def test_update_entry_success(self, test_app, mock_supabase, sample_user, sample_entry):
        """Test successful entry update."""
        # Mock authentication
        mock_supabase.auth.get_user.return_value = Mock(user=Mock(id=sample_user['id']))
        
        # Mock Supabase operations
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = Mock(data=[sample_entry])
        
        # Mock update operation
        mock_table.update.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = Mock(data=[{**sample_entry, 'content': 'Updated content'}])
        
        response = test_app.put('/api/entries/1',
            headers={'Authorization': 'Bearer test-token'},
            json={'content': 'Updated content'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['message'] == 'Entry updated successfully'
    
    def test_update_entry_not_found(self, test_app, mock_supabase, sample_user):
        """Test updating non-existent entry."""
        # Mock authentication
        mock_supabase.auth.get_user.return_value = Mock(user=Mock(id=sample_user['id']))
        
        # Mock empty result
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = Mock(data=[])
        
        response = test_app.put('/api/entries/999',
            headers={'Authorization': 'Bearer test-token'},
            json={'content': 'Updated content'}
        )
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'not found' in data['error'].lower()

class TestEntryDeletion:
    """Test journal entry deletion functionality."""
    
    def test_delete_entry_success(self, test_app, mock_supabase, sample_user, sample_entry):
        """Test successful entry deletion."""
        # Mock authentication
        mock_supabase.auth.get_user.return_value = Mock(user=Mock(id=sample_user['id']))
        
        # Mock Supabase operations
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = Mock(data=[sample_entry])
        
        # Mock delete operation
        mock_table.delete.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = Mock(data=[sample_entry])
        
        response = test_app.delete('/api/entries/1',
            headers={'Authorization': 'Bearer test-token'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['message'] == 'Entry deleted successfully'
    
    def test_delete_entry_not_found(self, test_app, mock_supabase, sample_user):
        """Test deleting non-existent entry."""
        # Mock authentication
        mock_supabase.auth.get_user.return_value = Mock(user=Mock(id=sample_user['id']))
        
        # Mock empty result
        mock_table = Mock()
        mock_supabase.table.return_value = mock_table
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = Mock(data=[])
        
        response = test_app.delete('/api/entries/999',
            headers={'Authorization': 'Bearer test-token'}
        )
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'not found' in data['error'].lower()
