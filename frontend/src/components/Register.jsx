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
  const { register, error } = useContext(AuthContext);
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

  return (
    <div className="auth-container">
      <div className="auth-form-container">
        <h2>Create Account</h2>
        {(localError || error) && <div className="auth-error">{localError || error}</div>}
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
            />
            {confirmPassword && password !== confirmPassword && (
              <div className="password-mismatch">Passwords do not match</div>
            )}
          </div>
          
          <button 
            type="submit" 
            className="auth-button"
            disabled={isSubmitting || password !== confirmPassword}
            onClick={() => console.log('Button clicked!')}
          >
            {isSubmitting ? 'Creating Account...' : 'Create Account'}
          </button>
        </form>
        
        <div className="auth-link">
          Already have an account? <span onClick={() => navigate('/login')}>Login</span>
        </div>
        
        <div className="auth-note">
          <p>If you're having trouble registering, you might already have an account. Try logging in instead!</p>
        </div>
      </div>
    </div>
  );
}

export default Register; 