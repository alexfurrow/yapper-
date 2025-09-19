# Email Confirmation Setup

## What We've Done

✅ **Enabled Supabase Email Confirmations**
- Set `enable_confirmations = true` in `supabase/config.toml`
- Configured SMTP settings to use your existing email credentials

✅ **Removed Redundant Custom Email System**
- Deleted `backend/services/email_service.py` (custom SMTP service)
- Deleted `frontend/src/components/EmailVerification.jsx` (custom verification component)
- Kept `frontend/src/components/EmailConfirmation.jsx` (Supabase-based confirmation)

## What You Need to Do

### 1. Set Up Environment Variables

Create a `.env` file in your project root with these variables:

```bash
# Supabase Configuration (you should already have these)
SUPABASE_URL=your-supabase-url
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# SMTP Configuration for Email Sending
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password  # Use App Password for Gmail
FROM_EMAIL=your-email@gmail.com
```

### 2. Gmail App Password Setup

If using Gmail, you need to:
1. Enable 2-Factor Authentication on your Google account
2. Generate an App Password: https://myaccount.google.com/apppasswords
3. Use the App Password (not your regular password) for `SMTP_PASSWORD`

### 3. Deploy Supabase Configuration

Run these commands to apply the Supabase configuration:

```bash
# If using Supabase CLI locally
supabase db reset
# or
supabase start
```

### 4. Test the Flow

1. **Register a new user** - should now receive an email
2. **Check email** - click the confirmation link
3. **Verify redirect** - should redirect to `/confirm-email` route
4. **Login** - should work after email confirmation

## How It Works Now

1. **User registers** → Supabase sends confirmation email automatically
2. **User clicks email link** → Redirects to `/confirm-email` with tokens
3. **EmailConfirmation component** → Handles the confirmation using Supabase tokens
4. **User can login** → After successful confirmation

## Troubleshooting

- **No emails received**: Check SMTP credentials and Gmail App Password
- **Confirmation link doesn't work**: Check that `site_url` in `supabase/config.toml` matches your domain
- **Redirect issues**: Ensure `/confirm-email` route is properly configured in your app

## Next Steps (Optional)

- **Google SSO**: Can be added later using Supabase OAuth providers
- **Custom email templates**: Can be customized in Supabase dashboard
- **Email branding**: Update sender name and templates as needed
