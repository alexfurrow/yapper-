import os
from dotenv import load_dotenv
from pathlib import Path

def load_environment():
    # Determine the environment; default to 'development' if not set
    env = os.getenv('FLASK_ENV', 'development')
    
    # Get the project root directory (assuming this file is in backend/config)
    project_root = Path(__file__).parent.parent.parent
    
    # Construct the path to the specific .env file
    dotenv_path = project_root / f'.env.{env}'
    
    loaded_specific = False
    if dotenv_path.exists():
        load_dotenv(dotenv_path, override=True)
        loaded_specific = True
    else:
        # Fallback to a default .env file if the specific one doesn't exist
        default_dotenv_path = project_root / '.env'
        if default_dotenv_path.exists():
            load_dotenv(default_dotenv_path, override=True) 