import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key'
    # SQLAlchemy configuration removed - using Supabase
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
