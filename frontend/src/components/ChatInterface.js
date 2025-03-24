import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import './ChatInterface.css';

function ChatInterface() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  // Auto-scroll to bottom of messages
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

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

  const handleSourceClick = (entryId) => {
    // Find the entry element in the DOM and scroll to it
    const entryElement = document.getElementById(`entry-${entryId}`);
    if (entryElement) {
      entryElement.scrollIntoView({ behavior: 'smooth' });
      // Highlight the entry
      entryElement.click();
    }
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
    </div>
  );
}

export default ChatInterface; 