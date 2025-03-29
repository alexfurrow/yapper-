import React, { useContext } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import './Header.css';

function Header() {
  const { currentUser, logout } = useContext(AuthContext);
  const navigate = useNavigate();
  
  const handleLogout = () => {
    logout();
    navigate('/login');
  };
  
  return (
    <header className="app-header">
      <h1>Yapper</h1>
      
      {currentUser ? (
        <div className="header-nav">
          <div className="tabs">
            <Link to="/">
              <button className={window.location.pathname === '/' ? 'active' : ''}>
                Journal Entry
              </button>
            </Link>
            <Link to="/chat">
              <button className={window.location.pathname === '/chat' ? 'active' : ''}>
                Chat with Journal
              </button>
            </Link>
          </div>
          
          <div className="user-controls">
            <span className="username">Hello, {currentUser.username}</span>
            <button className="logout-button" onClick={handleLogout}>Logout</button>
          </div>
        </div>
      ) : (
        <div className="auth-buttons">
          <Link to="/login">
            <button>Login</button>
          </Link>
          <Link to="/register">
            <button>Register</button>
          </Link>
        </div>
      )}
    </header>
  );
}

export default Header; 