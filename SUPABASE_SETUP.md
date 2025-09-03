# Supabase Integration Setup Guide

## Overview
This project has been migrated from a custom Flask authentication system to Supabase for user authentication and management.

## Frontend Environment Variables

Create a `.env` file in your `frontend/` directory with:

```bash
# Supabase Configuration
VITE_SUPABASE_URL=https://your-project-id.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key-here

# Optional: Your backend API URL
VITE_API_URL=https://your-backend-url.railway.app
```

## How to Get Supabase Credentials

1. **Go to your Supabase Dashboard**: https://supabase.com/dashboard
2. **Select your project**
3. **Go to Settings → API**
4. **Copy the values**:
   - **Project URL**: Use this for `VITE_SUPABASE_URL`
   - **anon public**: Use this for `VITE_SUPABASE_ANON_KEY`

## Vercel Deployment

For Vercel deployment, add these environment variables in your Vercel dashboard:

1. **Go to your Vercel project**
2. **Settings → Environment Variables**
3. **Add each variable**:
   - `VITE_SUPABASE_URL` = `https://your-project-id.supabase.co`
   - `VITE_SUPABASE_ANON_KEY` = `your-anon-key-here`

## Backend Environment Variables

Your Railway backend needs these environment variables:

```bash
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

**Note**: Use the `service_role` key (not `anon`) for backend operations.

## Architecture

- **Frontend**: Uses Supabase JavaScript client for authentication
- **Backend**: Uses Supabase Python client for user verification
- **Database**: Entries are linked to users via Supabase user IDs
- **Auth Flow**: Frontend handles login/registration, backend verifies tokens

## Testing

1. **Set up environment variables**
2. **Deploy to Vercel** (should build successfully now)
3. **Test registration** with email/password
4. **Test login** with created account
5. **Verify backend integration** works with Supabase tokens

## Troubleshooting

- **Build fails**: Check that environment variables are set in Vercel
- **Auth not working**: Verify Supabase credentials are correct
- **Backend errors**: Ensure service role key is set in Railway
