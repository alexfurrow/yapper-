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
        <div className="logo-section">
          <h1>Yapper</h1>
          <span className="tagline">tell your life story</span>
        </div>
        
        <div className="user-controls">
          {currentUser ? (
            <>
              <span className="username">Hello, {currentUser.username}</span>
              <button className="logout-button" onClick={handleLogout}>Logout</button>
            </>
          ) : (
            <>
              <button className="login-button" onClick={() => navigate('/login')}>Login</button>
              <button className="register-button" onClick={() => navigate('/register')}>Sign Up</button>
            </>
          )}
        </div>
      </div>
    </header>
  );
}

export default Header; 