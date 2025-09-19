import React, { useState, useContext } from 'react';
import { AuthContext } from '../context/AuthContext';
import { NavigationContext } from '../App';
import './Auth.css';

function Register() {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordStrength, setPasswordStrength] = useState({ score: 0, feedback: [] });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [localError, setLocalError] = useState('');
  const { register, loginWithGoogle, error } = useContext(AuthContext);
  const { navigate } = useContext(NavigationContext);

  const validatePassword = (password) => {
    const feedback = [];
    let score = 0;

    if (password.length >= 8) {
      score += 1;
    } else {
      feedback.push('At least 8 characters');
    }

    if (/[A-Z]/.test(password)) {
      score += 1;
    } else {
      feedback.push('One uppercase letter');
    }

    if (/[a-z]/.test(password)) {
      score += 1;
    } else {
      feedback.push('One lowercase letter');
    }

    if (/\d/.test(password)) {
      score += 1;
    } else {
      feedback.push('One number');
    }

    if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
      score += 1;
    } else {
      feedback.push('One special character');
    }

    return { score, feedback };
  };

  const handlePasswordChange = (e) => {
    const newPassword = e.target.value;
    setPassword(newPassword);
    setPasswordStrength(validatePassword(newPassword));
  };

  const getPasswordStrengthColor = () => {
    if (passwordStrength.score <= 2) return '#ef4444';
    if (passwordStrength.score <= 3) return '#f59e0b';
    if (passwordStrength.score <= 4) return '#10b981';
    return '#059669';
  };

  const getPasswordStrengthText = () => {
    if (passwordStrength.score <= 2) return 'Weak';
    if (passwordStrength.score <= 3) return 'Fair';
    if (passwordStrength.score <= 4) return 'Good';
    return 'Strong';
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    console.log('Form submitted!');
    console.log('Form data:', { username, email, password: '***', confirmPassword: '***' });
    console.log('Password strength:', passwordStrength);
    console.log('Passwords match:', password === confirmPassword);
    
    setLocalError('');
    
    if (password !== confirmPassword) {
      setLocalError('Passwords do not match');
      return;
    }
    
    if (passwordStrength.score < 5) {
      setLocalError('Please meet all password requirements');
      return;
    }
    
    console.log('Starting registration...');
    setIsSubmitting(true);
    
    try {
      await register(username, email, password);
      console.log('Registration call completed');
      // AuthContext will handle the flow and show appropriate messages
    } catch (error) {
      console.error('Registration error:', error);
      setLocalError('Registration failed. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleGoogleLogin = async () => {
    await loginWithGoogle();
  };


  return (
    <div className="auth-container">
      <div className="auth-form-container">
        <h2>Create Your Account</h2>
        {(localError || error) && <div className="auth-error">{localError || error}</div>}
        
        {/* SSO Buttons */}
        <div className="sso-buttons">
          <button 
            type="button" 
            className="sso-button google" 
            onClick={handleGoogleLogin}
            disabled={isSubmitting}
          >
            <svg width="20" height="20" viewBox="0 0 24 24">
              <path fill="#db4437" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
              <path fill="#34a853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
              <path fill="#fbbc05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
              <path fill="#ea4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
            </svg>
            Continue with Google
          </button>
          
        </div>

        <div className="divider">
          <span>or</span>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              type="text"
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              minLength={3}
              maxLength={64}
              placeholder="Choose a username"
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              placeholder="Enter your email"
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={handlePasswordChange}
              required
              minLength={8}
              placeholder="Create a strong password"
            />
            {password && (
              <div className="password-strength">
                <div className="strength-bar">
                  <div 
                    className="strength-fill" 
                    style={{ 
                      width: `${(passwordStrength.score / 5) * 100}%`,
                      backgroundColor: getPasswordStrengthColor()
                    }}
                  ></div>
                </div>
                <span className="strength-text" style={{ color: getPasswordStrengthColor() }}>
                  {getPasswordStrengthText()}
                </span>
                {passwordStrength.feedback.length > 0 && (
                  <ul className="password-requirements">
                    {passwordStrength.feedback.map((req, index) => (
                      <li key={index} className="requirement-item">• {req}</li>
                    ))}
                  </ul>
                )}
              </div>
            )}
          </div>
          
          <div className="form-group">
            <label htmlFor="confirmPassword">Confirm Password</label>
            <input
              type="password"
              id="confirmPassword"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              placeholder="Confirm your password"
            />
            {confirmPassword && password !== confirmPassword && (
              <div className="password-mismatch">Passwords do not match</div>
            )}
          </div>
          
          <button 
            type="submit" 
            className="auth-button"
            disabled={isSubmitting || password !== confirmPassword}
          >
            {isSubmitting ? 'Creating Account...' : 'Create Account'}
          </button>
        </form>
        
        <div className="auth-link">
          Already have an account? <span onClick={() => navigate('/login')}>Sign in</span>
        </div>
      </div>
    </div>
  );
}

export default Register; 