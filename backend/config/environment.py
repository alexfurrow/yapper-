import os
from dotenv import load_dotenv
from pathlib import Path

def load_environment():
    # Determine the environment; default to 'development' if not set
    env = os.getenv('FLASK_ENV', 'development')
    print(f"--- DEBUG [load_environment]: FLASK_ENV = {env}")
    
    # Get the project root directory (assuming this file is in backend/config)
    project_root = Path(__file__).parent.parent.parent
    
    # Construct the path to the specific .env file
    dotenv_path = project_root / f'.env.{env}'
    print(f"--- DEBUG [load_environment]: Looking for specific env file: {dotenv_path}")
    
    loaded_specific = False
    if dotenv_path.exists():
        load_dotenv(dotenv_path, override=True)
        print(f"--- DEBUG [load_environment]: SUCCESS - Loaded environment from {dotenv_path}")
        loaded_specific = True
    else:
        print(f"--- DEBUG [load_environment]: Specific env file NOT FOUND: {dotenv_path}")
        # Fallback to a default .env file if the specific one doesn't exist
        default_dotenv_path = project_root / '.env'
        print(f"--- DEBUG [load_environment]: Looking for fallback env file: {default_dotenv_path}")
        if default_dotenv_path.exists():
            load_dotenv(default_dotenv_path, override=True)
            print(f"--- DEBUG [load_environment]: SUCCESS - Loaded environment from fallback {default_dotenv_path}")
        else:
            print(f"--- DEBUG [load_environment]: Fallback env file NOT FOUND: {default_dotenv_path}")

    # Print DATABASE_URL immediately after attempting load
    db_url_after_load = os.environ.get('DATABASE_URL')
    print(f"--- DEBUG [load_environment]: DATABASE_URL immediately after load attempt: {db_url_after_load}") 