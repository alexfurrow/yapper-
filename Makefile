.PHONY: run test deploy clean

# Run development server
run:
	flask run --debug

# Run tests
test:
	pytest

# Deploy to production
deploy:
	git push heroku main

# Clean up cache files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete 