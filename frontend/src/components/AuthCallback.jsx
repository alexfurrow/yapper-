import React, { useEffect, useContext } from 'react';
import { supabase } from '../context/supabase.js';
import { NavigationContext } from '../App';

function AuthCallback() {
  const { navigate } = useContext(NavigationContext);

  useEffect(() => {
    const handleAuthCallback = async () => {
      try {
        // Google OAuth returns tokens in hash fragment (#access_token=...)
        // Check hash fragment first
        const hashParams = new URLSearchParams(window.location.hash.substring(1));
        const accessToken = hashParams.get('access_token');
        const refreshToken = hashParams.get('refresh_token');

        if (accessToken && refreshToken) {
          const { data, error } = await supabase.auth.setSession({
            access_token: accessToken,
            refresh_token: refreshToken
          });

          if (error || !data.session) {
            console.error('Auth callback error:', error);
            navigate('/login?error=auth_callback_failed');
            return;
          }

          // Clear hash fragment for security (tokens no longer in URL)
          window.history.replaceState(null, '', '/auth/callback');
          navigate('/');
          return;
        }

        // Fallback: Check for code in query string (PKCE flow)
        const code = new URLSearchParams(window.location.search).get('code');
        if (code) {
          const { data, error } = await supabase.auth.exchangeCodeForSession({ code });

          if (error || !data.session) {
            console.error('Auth callback error:', error);
            navigate('/login?error=auth_callback_failed');
            return;
          }

          navigate('/');
          return;
        }

        // No tokens or code found
        navigate('/login?error=no_session');
      } catch (err) {
        console.error('Auth callback exception:', err);
        navigate('/login?error=auth_callback_exception');
      }
    };

    handleAuthCallback();
  }, [navigate]);

  return (
    <div style={{ 
      display: 'flex', 
      justifyContent: 'center', 
      alignItems: 'center', 
      height: '100vh',
      fontSize: '18px'
    }}>
      Completing sign-in...
    </div>
  );
}

export default AuthCallback;
