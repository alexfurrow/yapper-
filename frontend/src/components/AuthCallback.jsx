import React, { useEffect, useContext } from 'react';
import { supabase } from '../context/supabase.js';
import { NavigationContext } from '../App';

function AuthCallback() {
  const { navigate } = useContext(NavigationContext);

  useEffect(() => {
    const handleAuthCallback = async () => {
      try {
        // Exchange the code for a session
        const { data, error } = await supabase.auth.exchangeCodeForSession({
          code: new URLSearchParams(window.location.search).get('code'),
        });

        if (error) {
          console.error('Auth callback error:', error);
          // Redirect to login with error
          navigate('/login?error=auth_callback_failed');
          return;
        }

        if (data.session) {
          console.log('Auth callback successful, session created');
          // Redirect to main app
          navigate('/');
        } else {
          console.error('No session created');
          navigate('/login?error=no_session');
        }
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
