#!/usr/bin/env python3
"""
Test runner script for the Yapper application.
"""
import subprocess
import sys
import os

def run_tests():
    """Run all tests with coverage."""
    print("🧪 Running Yapper Tests...")
    print("=" * 50)
    
    # Set test environment
    os.environ['FLASK_ENV'] = 'testing'
    
    try:
        # Run pytest with coverage
        result = subprocess.run([
            'python', '-m', 'pytest', 
            'tests/', 
            '--verbose',
            '--cov=backend',
            '--cov-report=term-missing',
            '--cov-report=html:htmlcov'
        ], check=True)
        
        print("\n✅ All tests passed!")
        print("📊 Coverage report generated in htmlcov/")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Tests failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print("\n❌ pytest not found. Please install it with: uv add pytest pytest-cov")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
