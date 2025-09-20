#!/bin/bash

# Setup script for local development environment

echo "🏗️ Setting up local development environment..."

# Create .env.development file
cat > .env.development << 'EOF'
# Local Development Environment Configuration
FLASK_ENV=development
FLASK_DEBUG=True

# Database - Use local Supabase or your dev database
DATABASE_URL=postgresql://postgres:password@localhost:5432/yapper_dev
SUPABASE_URL=http://localhost:54321
SUPABASE_ANON_KEY=your_local_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_local_service_role_key

# OpenAI API (use your API key)
OPENAI_API_KEY=your_openai_api_key

# Frontend URL for local development
FRONTEND_URL=http://localhost:3000

# CORS settings for local development
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Logging
LOG_LEVEL=DEBUG
EOF

# Create frontend .env.local file
cat > frontend/.env.local << 'EOF'
# Local Development Frontend Environment
VITE_BACKEND_URL=http://localhost:5000
VITE_SUPABASE_URL=http://localhost:54321
VITE_SUPABASE_ANON_KEY=your_local_anon_key
EOF

echo "✅ Environment files created!"
echo ""
echo "📝 Next steps:"
echo "1. Update .env.development with your actual values"
echo "2. Update frontend/.env.local with your actual values"
echo "3. Set up local Supabase or use your dev database"
echo "4. Run: python app.py (backend)"
echo "5. Run: cd frontend && npm run dev (frontend)"
echo ""
echo "🔧 To start local development:"
echo "  Backend:  python app.py"
echo "  Frontend: cd frontend && npm run dev"
