#!/usr/bin/env python
import os
import sys
import subprocess
from pathlib import Path

# Get the project root directory
root_dir = Path(__file__).parent.parent.absolute()

# Change to the project directory
os.chdir(root_dir)

# Activate the virtual environment and run the command
try:
    # For Unix/Linux/Mac
    if sys.platform != "win32":
        subprocess.run(f"source .venv/bin/activate && flask vectorize-pages", shell=True)
    # For Windows
    else:
        subprocess.run(f".venv\\Scripts\\activate && flask vectorize-pages", shell=True)
    print("Vectorization completed successfully")
except Exception as e:
    print(f"Error running vectorization: {str(e)}") 