import React, { useState } from 'react';
import JournalEntryForm from './components/JournalEntryForm';
import ChatInterface from './components/ChatInterface';
import SharedLayout from './components/SharedLayout';
import './App.css';

function App() {
  const [activeTab, setActiveTab] = useState('entry');

  return (
    <div className="App">
      <div className="app-header">
        <h1>Yapper</h1>
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
      
      <SharedLayout activeTab={activeTab}>
        {activeTab === 'entry' ? (
          <JournalEntryForm />
        ) : (
          <ChatInterface />
        )}
      </SharedLayout>
    </div>
  );
}

export default App; 