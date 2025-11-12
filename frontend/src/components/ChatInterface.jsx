import React, { useState, useRef, useEffect } from 'react';
import './ChatInterface.css';
import { supabase } from '../context/supabase';
import SharedLayout from './SharedLayout';
import NavigationTabs from './NavigationTabs';

function ChatInterface({ journalToggleButton }) {
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
      // Get the current user's access token from Supabase
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session) {
        throw new Error('No active session found');
      }

      const accessToken = session.access_token;
      const backendUrl = import.meta.env.VITE_BACKEND_URL || 'https://your-app.railway.app';
      const chatUrl = `${backendUrl}/api/chat/chat`;
      
      // Make streaming API call
      const response = await fetch(chatUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify({
          message: input,
          limit: 3
        })
      });

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP error! status: ${response.status}, body: ${errorText}`);
      }

      // Handle streaming response
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let aiMessage = { type: 'ai', content: '', sources: [] };

      // Add the AI message to chat immediately (empty content)
      setMessages(prev => [...prev, aiMessage]);
      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value);
          const lines = chunk.split('\n');

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6));
                
                if (data.type === 'sources') {
                  aiMessage.sources = data.sources;
                  setMessages(prev => 
                    prev.map(msg => 
                      msg === aiMessage ? { ...msg, sources: data.sources } : msg
                    )
                  );
                } else if (data.type === 'content') {
                  aiMessage.content += data.content;
                  setMessages(prev => 
                    prev.map(msg => 
                      msg === aiMessage ? { ...msg, content: aiMessage.content } : msg
                    )
                  );
                } else if (data.type === 'error') {
                  throw new Error(data.error);
                }
              } catch (parseError) {
                console.warn('Failed to parse streaming data:', parseError);
              }
            }
          }
        }
      } finally {
        reader.releaseLock();
      }
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
    <SharedLayout activeTab="chat">
      <div className="chat-interface-container">
        <NavigationTabs />
        
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
                          onClick={() => handleSourceClick(source.user_and_entry_id || source.entry_id)}
                        >
                          Entry #{source.user_entry_id || source.user_and_entry_id || source.entry_id}
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
        
        <div className="journal-toggle-container">
          {journalToggleButton}
        </div>
      </div>
    </SharedLayout>
  );
}

export default ChatInterface; 