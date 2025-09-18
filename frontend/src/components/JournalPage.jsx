import React, { useState, useRef, useEffect, useContext } from 'react';
import { supabase } from '../context/supabase.js';
import { AuthContext } from '../context/AuthContext';
import './JournalPage.css';

function JournalPage() {
  const [activeTab, setActiveTab] = useState('journal');
  const [content, setContent] = useState('');
  const [message, setMessage] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [audioBlob, setAudioBlob] = useState(null);
  const [entries, setEntries] = useState([]);
  const [selectedEntry, setSelectedEntry] = useState(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [isChatLoading, setIsChatLoading] = useState(false);
  
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const messagesEndRef = useRef(null);
  const { currentUser } = useContext(AuthContext);

  // Auto-scroll to bottom of chat messages
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatMessages]);

  // Load entries on component mount
  useEffect(() => {
    if (currentUser) {
    loadEntries();
    }
  }, [currentUser]);

  const loadEntries = async () => {
    try {
      console.log('Loading entries for user:', currentUser?.id);
      
      // Use Supabase directly instead of backend API for now
      // This avoids the URL routing issue
      const { data, error } = await supabase
        .from('entries')
        .select('*')
        .eq('user_id', currentUser?.id)
        .order('created_at', { ascending: false });

      if (error) {
        console.error('Error loading entries:', error);
        setEntries([]);
        return;
      }

      console.log('Entries loaded:', data);
      setEntries(data || []);
    } catch (error) {
      console.error('Error loading entries:', error);
      setEntries([]);
    }
  };

  // Handle content changes
  const handleContentChange = (e) => {
    const newContent = e.target.value;
    setContent(newContent);
  };

  // Journal Entry Functions
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!content.trim()) {
      setMessage('Content cannot be empty');
      return;
    }
    
    try {
      setMessage('Saving...');
      setIsLoading(true);
      
      // Get Supabase session for auth token
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) {
        throw new Error('No authentication session found');
      }

      const accessToken = session.access_token;
      const backendUrl = import.meta.env.VITE_BACKEND_URL || 'https://your-app.railway.app';
      const createUrl = `${backendUrl}/api/entries`;
      
      console.log('Creating entry via backend API...');
      console.log('Backend URL:', createUrl);
      console.log('Content:', content);
      
      const response = await fetch(createUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify({
          content: content
        })
      });

      console.log('Create entry response status:', response.status);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.log('Error response body:', errorText);
        throw new Error(`HTTP error! status: ${response.status}, body: ${errorText}`);
      }

      const data = await response.json();
      console.log('Entry created successfully:', data);
      
      setMessage('Entry saved successfully!');
      setContent('');
      
      // Refresh entries list
      loadEntries();
      
      // Clear success message after 3 seconds
      setTimeout(() => {
        setMessage('');
      }, 3000);
      
    } catch (error) {
      console.error('Error saving entry:', error);
      setMessage('Error saving entry: ' + error.message);
      
      // Clear error after 5 seconds
      setTimeout(() => {
        setMessage('');
      }, 5000);
    } finally {
      setIsLoading(false);
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      chunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };

      mediaRecorderRef.current.onstop = () => {
        const audioBlob = new Blob(chunksRef.current, { type: 'audio/wav' });
        setAudioBlob(audioBlob);
        uploadAudio(audioBlob);
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
    } catch (err) {
      console.error('Error accessing microphone:', err);
      setMessage('Error accessing microphone');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
    }
  };

  const uploadAudio = async (blob) => {
    try {
      setIsLoading(true);
      setMessage('Processing audio...');
      
      // For now, we'll skip audio processing since we don't have the backend endpoint
      // You can implement this later with your backend or a third-party service
      setMessage('Audio recording feature coming soon!');
      
      // Clear the message after 3 seconds
      setTimeout(() => {
        setMessage('');
      }, 3000);
      
    } catch (error) {
      console.error('Error processing audio:', error);
      setMessage('Error processing audio: ' + error.message);
    } finally {
      setIsLoading(false);
    }
  };




  // Chat Functions
  const handleChatSubmit = async (e) => {
    e.preventDefault();
    if (!chatInput.trim()) return;

    const userMessage = { type: 'user', content: chatInput };
    setChatMessages([...chatMessages, userMessage]);
    setChatInput('');
    setIsChatLoading(true);

    try {
      // Get the current user's access token from Supabase
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session) {
        throw new Error('No active session found');
      }

      const accessToken = session.access_token;
      
      console.log('Sending chat request to backend...');
      console.log('User message:', chatInput);
      console.log('Access token (first 20 chars):', accessToken.substring(0, 20) + '...');
      
      // Use the Railway backend URL instead of relative path
      const backendUrl = import.meta.env.VITE_BACKEND_URL || 'https://your-app.railway.app';
      const chatUrl = `${backendUrl}/api/chat/chat`;
      
      console.log('Request URL:', chatUrl);
      console.log('Request method:', 'POST');
      console.log('Request headers:', {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken.substring(0, 20)}...`
      });
      
      // Make API call to your Railway backend chat endpoint
      const response = await fetch(chatUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify({
        message: chatInput,
        limit: 3
        })
      });

      console.log('Response status:', response.status);
      console.log('Response status text:', response.statusText);
      console.log('Response headers:', Object.fromEntries(response.headers.entries()));
      console.log('Response URL:', response.url);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Error response body:', errorText);
        throw new Error(`HTTP error! status: ${response.status}, body: ${errorText}`);
      }

      const data = await response.json();
      console.log('Chat response received:', data);

      if (data.error) {
        throw new Error(data.error);
      }

      const aiMessage = { 
        type: 'ai', 
        content: data.response,
        sources: data.sources 
      };
      
      setChatMessages(prev => [...prev, aiMessage]);
      
    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage = { 
        type: 'ai', 
        content: `Sorry, I encountered an error: ${error.message}. Please try again.` 
      };
      setChatMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsChatLoading(false);
    }
  };

  const handleSourceClick = (entryId) => {
    const entry = entries.find(e => e.entry_id === entryId);
    if (entry) {
      setSelectedEntry(entry);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric', 
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatTimeAgo = (date) => {
    if (!date) return '';
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return formatDate(date);
  };

  return (
    <div className="journal-page">
      {/* Main Content Area */}
      <div className={`main-content ${isSidebarOpen ? 'with-sidebar' : ''}`}>
        {/* Tab Navigation */}
        <div className="tab-navigation">
          <button 
            className={`tab-button ${activeTab === 'journal' ? 'active' : ''}`}
            onClick={() => setActiveTab('journal')}
          >
            <span className="tab-icon">✍️</span>
            Journal Entry
          </button>
          <button 
            className={`tab-button ${activeTab === 'chat' ? 'active' : ''}`}
            onClick={() => setActiveTab('chat')}
          >
            <span className="tab-icon">💬</span>
            Chat Assistant
          </button>
        </div>

        {/* Tab Content */}
        <div className="tab-content">
          {activeTab === 'journal' && (
            <div className="journal-tab">
              {message && (
                <div className={`message-banner ${message.includes('Error') ? 'error' : 'success'}`}>
                  {message}
                </div>
              )}
              
              <form onSubmit={handleSubmit} className="journal-form">
                <div className="textarea-wrapper">
                  <textarea
                    value={content}
                    onChange={handleContentChange}
                    placeholder="What's on your mind today?"
                    rows="12"
                    disabled={isLoading}
                    className="journal-textarea"
                  />
                  
                </div>
                
                <div className="form-actions">
                  <div className="left-actions">
                    <button
                      type="button"
                      onClick={isRecording ? stopRecording : startRecording}
                      className={`record-button ${isRecording ? 'recording' : ''}`}
                      disabled={isLoading}
                    >
                      <span className="button-icon">
                        {isRecording ? '⏹️' : '🎤'}
                      </span>
                      {isRecording ? 'Stop Recording' : 'Start Recording'}
                    </button>
                  </div>
                  
                  <button 
                    type="submit" 
                    disabled={!content.trim()}
                    className="save-button"
                  >
                    <span className="button-icon">💾</span>
                    Save Entry
                  </button>
                </div>
              </form>
              
              {isLoading && (
                <div className="loading-overlay">
                  <div className="loading-spinner"></div>
                  <p>Processing your entry...</p>
                </div>
              )}
            </div>
          )}

          {activeTab === 'chat' && (
            <div className="chat-tab">
              <div className="chat-container">
                <div className="chat-header">
                  <h2>Journal Assistant</h2>
                </div>
                
                <div className="messages-container">
                  {(!chatMessages || chatMessages.length === 0) ? (
                    <div className="empty-chat">
                      <div className="empty-icon">🤖</div>
                      <h3>Ask me anything about your journal</h3>
                      <p>I can help you reflect on your entries, find patterns, or answer questions about your thoughts.</p>
                    </div>
                  ) : (
                    (chatMessages || []).map((msg, index) => (
                      <div key={index} className={`chat-message ${msg.type}`}>
                        <div className="message-content">{msg.content}</div>
                        {msg.sources && (
                          <div className="message-sources">
                            <span className="sources-label">Sources:</span>
                            {(msg.sources || []).map((source, idx) => (
                              <button 
                                key={idx} 
                                className="source-link"
                                onClick={() => handleSourceClick(source.entry_id)}
                              >
                                Entry #{source.entry_id}
                              </button>
                            ))}
                          </div>
                        )}
                      </div>
                    ))
                  )}
                  {isChatLoading && (
                    <div className="chat-message ai loading">
                      <div className="typing-indicator">
                        <span></span>
                        <span></span>
                        <span></span>
                      </div>
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                </div>
                
                <form onSubmit={handleChatSubmit} className="chat-input-form">
                  <input
                    type="text"
                    value={chatInput}
                    onChange={(e) => setChatInput(e.target.value)}
                    placeholder="Ask about your journal entries..."
                    disabled={isChatLoading}
                    className="chat-input"
                  />
                  <button 
                    type="submit" 
                    disabled={isChatLoading || !chatInput.trim()}
                    className="send-button"
                  >
                    <span className="button-icon">📤</span>
                  </button>
                </form>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Sidebar */}
      <div className={`sidebar ${isSidebarOpen ? 'open' : ''}`}>
        <div className="sidebar-header">
          <h3>Journal History</h3>
          <button 
            className="sidebar-toggle"
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
          >
            <span className="toggle-icon">📚</span>
          </button>
        </div>
        
        <div className="entries-list">
          {(!entries || entries.length === 0) ? (
            <div className="empty-entries">
              <div className="empty-icon">📝</div>
              <p>No entries yet</p>
              <span>Start writing to see your journal history here</span>
            </div>
          ) : (
            (entries || []).map((entry) => (
              <div 
                key={entry.entry_id}
                className={`entry-item ${selectedEntry?.entry_id === entry.entry_id ? 'selected' : ''}`}
                onClick={() => setSelectedEntry(entry)}
              >
                <div className="entry-header">
                  <span className="entry-id">#{entry.user_entry_id || entry.entry_id}</span>
                  <span className="entry-date">{formatDate(entry.created_at)}</span>
                </div>
                <div className="entry-preview">
                  {entry.content.length > 80 
                    ? entry.content.substring(0, 80) + '...' 
                    : entry.content}
                </div>
              </div>
            ))
          )}
        </div>
        
        {selectedEntry && (
          <div className="entry-detail">
            <div className="detail-header">
              <h4>Entry #{selectedEntry.user_entry_id || selectedEntry.entry_id}</h4>
              <span className="detail-date">{formatDate(selectedEntry.created_at)}</span>
            </div>
            <div className="detail-content">{selectedEntry.content}</div>
          </div>
        )}
      </div>

      {/* Sidebar Toggle Button (when sidebar is closed) */}
      {!isSidebarOpen && (
        <button 
          className="sidebar-toggle-button"
          onClick={() => setIsSidebarOpen(true)}
          title="Show Journal History"
        >
          <span className="toggle-icon">📚</span>
        </button>
      )}
    </div>
  );
}

export default JournalPage;
