"""
Test configuration and fixtures for the Yapper application.
"""
import pytest
import os
from unittest.mock import Mock, patch
from dotenv import load_dotenv

# Load test environment variables
load_dotenv(override=True)

@pytest.fixture
def test_app():
    """Create a test Flask application."""
    # Set test environment variables BEFORE importing app
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['SUPABASE_URL'] = 'https://test.supabase.co'
    os.environ['SUPABASE_SERVICE_ROLE_KEY'] = 'test-service-role-key'
    os.environ['OPENAI_API_KEY'] = 'test-openai-key'
    
    # Mock the Supabase client before importing app
    with patch('backend.routes.entries.supabase') as mock_entries_supabase:
        with patch('backend.routes.chat.supabase') as mock_chat_supabase:
            with patch('backend.services.embedding.supabase') as mock_embedding_supabase:
                from app import create_app
                
                app = create_app()
                app.config['TESTING'] = True
                
                with app.test_client() as client:
                    yield client

@pytest.fixture
def mock_supabase():
    """Mock Supabase client for testing."""
    with patch('backend.routes.entries.supabase') as mock_supabase:
        with patch('backend.routes.chat.supabase') as mock_chat_supabase:
            with patch('backend.services.embedding.supabase') as mock_embedding_supabase:
                yield mock_supabase

@pytest.fixture
def mock_openai():
    """Mock OpenAI client for testing."""
    with patch('backend.services.initial_processing.client') as mock_client:
        with patch('backend.routes.chat.client') as mock_chat_client:
            yield mock_client

@pytest.fixture
def sample_user():
    """Sample user data for testing."""
    return {
        'id': 'test-user-123',
        'email': 'test@example.com'
    }

@pytest.fixture
def sample_entry():
    """Sample journal entry data for testing."""
    return {
        'user_id': 'test-user-123',
        'user_entry_id': 1,
        'content': 'This is a test journal entry about my day.',
        'processed': 'This is a processed test journal entry about my day.',
        'vectors': [0.1, 0.2, 0.3] * 1536,  # Mock embedding vector
        'created_at': '2024-01-01T00:00:00Z'
    }
