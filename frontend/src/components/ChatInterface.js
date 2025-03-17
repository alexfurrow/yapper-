import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import './ChatInterface.css';

function ChatInterface() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [entries, setEntries] = useState([]);
  const [selectedEntry, setSelectedEntry] = useState(null);
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom of messages
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Fetch entries when component mounts
  useEffect(() => {
    fetchEntries();
  }, []);

  const fetchEntries = async () => {
    try {
      const response = await axios.get('http://localhost:5000/api/pages');
      setEntries(response.data);
    } catch (error) {
      console.error('Error fetching entries:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    // Add user message to chat
    const userMessage = { type: 'user', content: input };
    setMessages([...messages, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await axios.post('http://localhost:5000/api/chat', {
        message: input,
        limit: 3
      });

      // Add AI response to chat
      const aiMessage = { 
        type: 'ai', 
        content: response.data.response,
        sources: response.data.sources 
      };
      setMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = { 
        type: 'error', 
        content: 'Sorry, there was an error processing your request.' 
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleEntryClick = (entry) => {
    setSelectedEntry(entry);
  };

  const handleSourceClick = (entryId) => {
    // Find the entry with the matching ID
    const entry = entries.find(e => e.entry_id === entryId);
    if (entry) {
      setSelectedEntry(entry);
      
      // Find the entry element in the DOM and scroll to it
      const entryElement = document.getElementById(`entry-${entryId}`);
      if (entryElement) {
        entryElement.scrollIntoView({ behavior: 'smooth' });
      }
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return date.toLocaleDateString(undefined, options); // e.g., Mar 18, 2025
  };

  return (
    <div className="chat-interface-container">
      <div className="chat-container">
        <div className="chat-header">
          <h2>Journal Assistant</h2>
        </div>
        <div className="messages-container">
          {messages.length === 0 ? (
            <div className="empty-chat">
              <p>Ask me anything about your journal entries!</p>
            </div>
          ) : (
            messages.map((msg, index) => (
              <div key={index} className={`message ${msg.type}`}>
                <div className="message-content">{msg.content}</div>
                {msg.sources && (
                  <div className="message-sources">
                    <p className="sources-title">Sources:</p>
                    {msg.sources.map((source, idx) => (
                      <span 
                        key={idx} 
                        className="source-badge clickable"
                        onClick={() => handleSourceClick(source.entry_id)}
                      >
                        Entry #{source.entry_id}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))
          )}
          {isLoading && (
            <div className="message ai loading">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
        <form onSubmit={handleSubmit} className="chat-input-form">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about your journal entries..."
            disabled={isLoading}
          />
          <button type="submit" disabled={isLoading || !input.trim()}>
            Send
          </button>
        </form>
      </div>
      
      <div className="entries-container">
        <div className="entries-header">
          <h2>Your Journal Entries</h2>
        </div>
        <div className="entries-list">
          {entries.length === 0 ? (
            <div className="empty-entries">
              <p>No entries yet. Start journaling!</p>
            </div>
          ) : (
            entries.map((entry) => (
              <div 
                id={`entry-${entry.entry_id}`}
                key={entry.entry_id} 
                className={`entry-item ${selectedEntry?.entry_id === entry.entry_id ? 'selected' : ''}`}
                onClick={() => handleEntryClick(entry)}
              >
                <div className="entry-header">
                  <span className="entry-id">#{entry.entry_id}</span>
                  <span className="entry-date">{formatDate(entry.created_at)}</span>
                </div>
                <div className="entry-preview">
                  {entry.content.length > 100 
                    ? entry.content.substring(0, 100) + '...' 
                    : entry.content}
                </div>
              </div>
            ))
          )}
        </div>
        {selectedEntry && (
          <div className="entry-detail">
            <h3>Entry #{selectedEntry.entry_id}</h3>
            <div className="entry-date-full">{formatDate(selectedEntry.created_at)}</div>
            <div className="entry-content">{selectedEntry.content}</div>
          </div>
        )}
      </div>
    </div>
  );
}

export default ChatInterface; 