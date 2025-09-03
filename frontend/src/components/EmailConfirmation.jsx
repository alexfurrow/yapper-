import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { supabase } from '../context/supabase.js';
import './Auth.css';

function EmailConfirmation() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState('confirming');
  const [error, setError] = useState(null);

  useEffect(() => {
    const confirmEmail = async () => {
      try {
        // Get the access_token from URL parameters
        const accessToken = searchParams.get('access_token');
        const refreshToken = searchParams.get('refresh_token');
        
        if (!accessToken) {
          setError('No confirmation token found. Please check your email for the correct link.');
          setStatus('error');
          return;
        }

        // Set the session with the tokens
        const { data, error } = await supabase.auth.setSession({
          access_token: accessToken,
          refresh_token: refreshToken
        });

        if (error) {
          console.error('Session error:', error);
          setError('Failed to confirm email. Please try again or contact support.');
          setStatus('error');
          return;
        }

        if (data.user) {
          // Check if email is confirmed
          if (data.user.email_confirmed_at) {
            setStatus('success');
            // Redirect to login after a short delay
            setTimeout(() => {
              navigate('/login', { 
                state: { message: 'Email confirmed successfully! You can now log in.' }
              });
            }, 3000);
          } else {
            setError('Email confirmation failed. Please try again.');
            setStatus('error');
          }
        }
      } catch (error) {
        console.error('Confirmation error:', error);
        setError('An unexpected error occurred. Please try again.');
        setStatus('error');
      }
    };

    confirmEmail();
  }, [searchParams, navigate]);

  if (status === 'confirming') {
    return (
      <div className="auth-container">
        <div className="auth-form-container">
          <h2>Confirming Your Email</h2>
          <div className="loading-spinner">
            <div className="spinner"></div>
            <p>Please wait while we confirm your email address...</p>
          </div>
        </div>
      </div>
    );
  }

  if (status === 'error') {
    return (
      <div className="auth-container">
        <div className="auth-form-container">
          <h2>Email Confirmation Failed</h2>
          <div className="auth-error">{error}</div>
          <div className="auth-actions">
            <button 
              className="auth-button" 
              onClick={() => navigate('/register')}
            >
              Try Registering Again
            </button>
            <button 
              className="auth-button secondary" 
              onClick={() => navigate('/login')}
            >
              Go to Login
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (status === 'success') {
    return (
      <div className="auth-container">
        <div className="auth-form-container">
          <h2>Email Confirmed! 🎉</h2>
          <div className="auth-success">
            <p>Your email has been successfully confirmed!</p>
            <p>You will be redirected to the login page in a few seconds...</p>
          </div>
          <div className="auth-actions">
            <button 
              className="auth-button" 
              onClick={() => navigate('/login')}
            >
              Go to Login Now
            </button>
          </div>
        </div>
      </div>
    );
  }

  return null;
}

export default EmailConfirmation;
