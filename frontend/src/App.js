import React, { useState } from 'react';
import PageForm from './components/rootPageForm';
import ChatInterface from './components/ChatInterface';
import './App.css';

function App() {
  const [activeTab, setActiveTab] = useState('entry');

  return (
    <div className="App">
      <div className="app-header">
        <h1>Txtile</h1>
        <div className="tabs">
          <button 
            className={activeTab === 'entry' ? 'active' : ''} 
            onClick={() => setActiveTab('entry')}
          >
            Journal Entry
          </button>
          <button 
            className={activeTab === 'chat' ? 'active' : ''} 
            onClick={() => setActiveTab('chat')}
          >
            Chat with Journal
          </button>
        </div>
      </div>
      
      <div className="app-content">
        {activeTab === 'entry' ? (
          <PageForm />
        ) : (
          <ChatInterface />
        )}
      </div>
    </div>
  );
}

export default App; 