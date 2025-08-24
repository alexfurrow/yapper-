import React, { useContext } from 'react';
import { NavigationContext } from '../App';
import './NavigationTabs.css';

function NavigationTabs() {
  const { navigate } = useContext(NavigationContext);
  const currentPath = window.location.pathname;
  
  return (
    <div className="navigation-tabs">
      <button 
        className={currentPath === '/' ? 'active' : ''}
        onClick={() => navigate('/')}
      >
        Journal Entry
      </button>
      <button 
        className={currentPath === '/chat' ? 'active' : ''}
        onClick={() => navigate('/chat')}
      >
        Chat with Journal
      </button>
    </div>
  );
}

export default NavigationTabs;
