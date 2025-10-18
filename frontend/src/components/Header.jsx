import React, { useContext, useState, useRef, useEffect } from 'react';
import { AuthContext } from '../context/AuthContext';
import { NavigationContext } from '../App';
import './Header.css';

function Header() {
  const { currentUser, logout } = useContext(AuthContext);
  const { navigate } = useContext(NavigationContext);
  const [showDropdown, setShowDropdown] = useState(false);
  const dropdownRef = useRef(null);
  
  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handleBulkUpload = () => {
    navigate('/bulk-upload');
    setShowDropdown(false);
  };

  const handleBackToJournal = () => {
    navigate('/');
    setShowDropdown(false);
  };

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);
  
  return (
    <header className="app-header">
      <div className="header-content">
        <h1>Yapper</h1>
        
        {currentUser ? (
          <div className="user-controls">
            <div className="user-menu" ref={dropdownRef}>
              <button 
                className="user-menu-button"
                onClick={() => setShowDropdown(!showDropdown)}
              >
                <span className="username">Hello, {currentUser.username}</span>
                <span className="dropdown-arrow">▼</span>
              </button>
              
              {showDropdown && (
                <div className="user-dropdown">
                  <button 
                    className="dropdown-item"
                    onClick={handleBackToJournal}
                  >
                    📝 Journal
                  </button>
                  <button 
                    className="dropdown-item"
                    onClick={handleBulkUpload}
                  >
                    📁 Bulk Upload
                  </button>
                  <div className="dropdown-divider"></div>
                  <button 
                    className="dropdown-item logout-item"
                    onClick={handleLogout}
                  >
                    🚪 Logout
                  </button>
                </div>
              )}
            </div>
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