# 🏗️ Local Development Setup

This guide helps you set up a local development environment for Yapper.

## 🚀 Quick Start

1. **Run the setup script:**
   ```bash
   ./setup-local-dev.sh
   ```

2. **Configure your environment:**
   - Edit `.env.development` with your actual values
   - Edit `frontend/.env.local` with your actual values

3. **Start development servers:**
   ```bash
   # Terminal 1: Backend
   python app.py
   
   # Terminal 2: Frontend  
   cd frontend && npm run dev
   ```

## 🔧 Environment Configuration

### Backend (.env.development)
```bash
FLASK_ENV=development
FLASK_DEBUG=True

# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/yapper_dev
SUPABASE_URL=http://localhost:54321
SUPABASE_ANON_KEY=your_local_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_local_service_role_key

# OpenAI API
OPENAI_API_KEY=your_openai_api_key

# Frontend URL
FRONTEND_URL=http://localhost:3000
```

### Frontend (frontend/.env.local)
```bash
VITE_BACKEND_URL=http://localhost:5000
VITE_SUPABASE_URL=http://localhost:54321
VITE_SUPABASE_ANON_KEY=your_local_anon_key
```

## 🗄️ Database Options

### Option 1: Local Supabase (Recommended)
```bash
# Install Supabase CLI
npm install -g supabase

# Start local Supabase
supabase start

# Get your local keys from the output
```

### Option 2: Use Production Database (Quick Setup)
- Copy your production Supabase URL and keys
- Use your production database for development
- ⚠️ Be careful not to mess up production data!

## 🧪 Testing

```bash
# Run backend tests
python -m pytest

# Run specific test
python -m pytest tests/test_entries.py -v
```

## 📁 Branch Strategy

- **`dev`**: Local development branch
- **`prod`**: Production-ready branch
- **`main`**: Default branch (can be used for staging)

### Workflow:
1. Develop on `dev` branch locally
2. Test and commit changes
3. Merge `dev` → `prod` when ready for production
4. Deploy `prod` branch to production

## 🐛 Troubleshooting

### Common Issues:

1. **Port conflicts:**
   - Backend: Change port in `app.py`
   - Frontend: Change port in `frontend/vite.config.mjs`

2. **Database connection:**
   - Check your `DATABASE_URL`
   - Ensure database is running

3. **CORS issues:**
   - Check `CORS_ORIGINS` in backend
   - Check `VITE_BACKEND_URL` in frontend

4. **Missing dependencies:**
   ```bash
   # Backend
   pip install -r requirements.txt
   
   # Frontend
   cd frontend && npm install
   ```

## 🚀 Production Deployment

When ready to deploy:
1. Merge `dev` → `prod`
2. Deploy `prod` branch to Railway/Vercel
3. Update production environment variables
