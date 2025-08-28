import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import './Auth.css';

function EmailVerification() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState('verifying');
  const [message, setMessage] = useState('');

  useEffect(() => {
    const token = searchParams.get('token');
    
    if (token) {
      verifyEmail(token);
    } else {
      setStatus('error');
      setMessage('No verification token provided');
    }
  }, [searchParams]);

  const verifyEmail = async (token) => {
    try {
      const response = await axios.post('/api/auth/verify-email', { token });
      setStatus('success');
      setMessage(response.data.message);
      
      // Redirect to login after 3 seconds
      setTimeout(() => {
        navigate('/login');
      }, 3000);
    } catch (error) {
      setStatus('error');
      setMessage(error.response?.data?.message || 'Verification failed');
    }
  };

  const resendVerification = async () => {
    // This would need the user's email, so you might want to store it in localStorage
    // or have a separate form for resending verification
    setMessage('Please contact support to resend verification email');
  };

  return (
    <div className="auth-container">
      <div className="auth-form-container">
        <h2>Email Verification</h2>
        
        {status === 'verifying' && (
          <div className="verification-status">
            <div className="loading-spinner"></div>
            <p>Verifying your email address...</p>
          </div>
        )}
        
        {status === 'success' && (
          <div className="verification-success">
            <div className="success-icon">✅</div>
            <p>{message}</p>
            <p>Redirecting to login...</p>
          </div>
        )}
        
        {status === 'error' && (
          <div className="verification-error">
            <div className="error-icon">❌</div>
            <p>{message}</p>
            <button onClick={resendVerification} className="auth-button">
              Resend Verification Email
            </button>
            <button onClick={() => navigate('/login')} className="auth-button secondary">
              Go to Login
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default EmailVerification;
