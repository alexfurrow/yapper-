import React, { useContext } from 'react';
import { AuthContext } from '../context/AuthContext';
import { NavigationContext } from '../App';
import './Header.css';

function Header() {
  const { currentUser, logout } = useContext(AuthContext);
  const { navigate } = useContext(NavigationContext);
  
  const handleLogout = () => {
    logout();
    navigate('/login');
  };
  
  return (
    <header className="app-header">
      <div className="header-content">
        <h1>Yapper</h1>
        
        {currentUser ? (
          <div className="user-controls">
            <span className="username">Hello, {currentUser.username}</span>
            <button className="logout-button" onClick={handleLogout}>Logout</button>
          </div>
        ) : (
          <div className="auth-buttons">
            <button onClick={() => navigate('/login')}>Login</button>
            <button onClick={() => navigate('/register')}>Register</button>
          </div>
        )}
      </div>
    </header>
  );
}

export default Header; 