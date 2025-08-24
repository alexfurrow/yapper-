import React, { useState, useContext } from 'react';
import { AuthContext } from '../context/AuthContext';
import './Auth.css';

function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const { login, error } = useContext(AuthContext);
  const navigate = useContext(React.createContext()).navigate; // This will be provided by the router

  const handleSubmit = async (e) => {
    e.preventDefault();
    const success = await login(username, password);
    if (success) {
      // Use window.history for navigation since we're not using React Router
      window.history.pushState({}, '', '/');
      window.location.reload(); // Reload to trigger route change
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-form-container">
        <h2>Login</h2>
        {error && <div className="auth-error">{error}</div>}
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              type="text"
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <button type="submit" className="auth-button">Login</button>
        </form>
        <div className="auth-link">
          Don't have an account? <span onClick={() => {
            window.history.pushState({}, '', '/register');
            window.location.reload();
          }}>Register</span>
        </div>
      </div>
    </div>
  );
}

export default Login; 