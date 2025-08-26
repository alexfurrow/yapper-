import React, { useState, useRef, useEffect, useContext } from 'react';
import axios from 'axios';
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
  
  // Auto-save states
  const [autoSaveStatus, setAutoSaveStatus] = useState(''); // 'saving', 'saved', 'error'
  const [lastSavedTime, setLastSavedTime] = useState(null);
  const [draftId, setDraftId] = useState(null);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const messagesEndRef = useRef(null);
  const autoSaveTimeoutRef = useRef(null);
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
    loadEntries();
  }, []);

  // Auto-save effect
  useEffect(() => {
    // Clear existing timeout
    if (autoSaveTimeoutRef.current) {
      clearTimeout(autoSaveTimeoutRef.current);
    }

    // Only auto-save if content is substantial enough
    if (content.trim().length >= 50 && hasUnsavedChanges) {
      autoSaveTimeoutRef.current = setTimeout(() => {
        autoSaveDraft();
      }, 3000); // 3 second delay
    }

    return () => {
      if (autoSaveTimeoutRef.current) {
        clearTimeout(autoSaveTimeoutRef.current);
      }
    };
  }, [content, hasUnsavedChanges]);

  const loadEntries = async () => {
    try {
      const response = await axios.get('/api/entries');
      setEntries(response.data);
    } catch (error) {
      console.error('Error loading entries:', error);
    }
  };

  // Auto-save draft function
  const autoSaveDraft = async () => {
    if (!content.trim() || content.trim().length < 50) return;

    try {
      setAutoSaveStatus('saving');
      
      const response = await axios.post('/api/entries', { 
        content: content,
        is_draft: true 
      });
      
      setDraftId(response.data.entry_id);
      setAutoSaveStatus('saved');
      setHasUnsavedChanges(false);
      setLastSavedTime(new Date());
      
      // Refresh entries list
      loadEntries();
      
      // Clear saved status after 2 seconds
      setTimeout(() => {
        setAutoSaveStatus('');
      }, 2000);
      
    } catch (error) {
      console.error('Auto-save error:', error);
      setAutoSaveStatus('error');
      
      // Clear error status after 3 seconds
      setTimeout(() => {
        setAutoSaveStatus('');
      }, 3000);
    }
  };

  // Handle content changes
  const handleContentChange = (e) => {
    const newContent = e.target.value;
    setContent(newContent);
    setHasUnsavedChanges(true);
  };

  // Journal Entry Functions
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!content.trim()) {
      setMessage('Content cannot be empty');
      return;
    }
    
    // Clear any pending auto-save
    if (autoSaveTimeoutRef.current) {
      clearTimeout(autoSaveTimeoutRef.current);
    }
    
    try {
      setAutoSaveStatus('saving');
      
      // If we have a draft, update it; otherwise create new entry
      const endpoint = draftId ? `/api/entries/${draftId}` : '/api/entries';
      const method = draftId ? 'put' : 'post';
      
      const response = await axios[method](endpoint, { 
        content: content,
        is_draft: false // Mark as final entry
      });
      
      setMessage('Entry saved successfully!');
      setContent('');
      setDraftId(null);
      setHasUnsavedChanges(false);
      setAutoSaveStatus('saved');
      setLastSavedTime(new Date());
      
      // Refresh entries list
      loadEntries();
      
      // Clear success message after 3 seconds
      setTimeout(() => {
        setMessage('');
        setAutoSaveStatus('');
      }, 3000);
      
    } catch (error) {
      setMessage('Error saving entry: ' + error.message);
      setAutoSaveStatus('error');
      
      // Clear error after 5 seconds
      setTimeout(() => {
        setMessage('');
        setAutoSaveStatus('');
      }, 5000);
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
      const formData = new FormData();
      formData.append('audio', blob, 'recording.wav');

      const response = await axios.post('/api/audio', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      if (response.data.transcription) {
        setContent(response.data.transcription);
        setHasUnsavedChanges(true);
        
        // Auto-save the transcribed content
        setTimeout(() => {
          autoSaveDraft();
        }, 1000);
      }
    } catch (error) {
      console.error('Error:', error);
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
      console.log('Sending chat request to:', '/api/chat');
      console.log('Request payload:', { message: chatInput, limit: 3 });
      
      const response = await axios.post('/api/chat/', {
        message: chatInput,
        limit: 3
      });

      console.log('Chat response received:', response.data);

      const aiMessage = { 
        type: 'ai', 
        content: response.data.response,
        sources: response.data.sources 
      };
      setChatMessages(prev => [...prev, aiMessage]);
    } catch (error) {
      console.error('Chat API Error Details:', {
        message: error.message,
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data,
        config: {
          url: error.config?.url,
          method: error.config?.method,
          headers: error.config?.headers
        }
      });
      
      const errorMessage = { 
        type: 'error', 
        content: `Error: ${error.response?.data?.error || error.message || 'Unknown error occurred'}`
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
                  
                  {/* Auto-save status indicator */}
                  <div className="auto-save-indicator">
                    {autoSaveStatus === 'saving' && (
                      <span className="status-saving">💾 Saving draft...</span>
                    )}
                    {autoSaveStatus === 'saved' && (
                      <span className="status-saved">✅ Draft saved</span>
                    )}
                    {autoSaveStatus === 'error' && (
                      <span className="status-error">❌ Save failed</span>
                    )}
                    {lastSavedTime && !autoSaveStatus && (
                      <span className="status-last-saved">
                        Last saved: {formatTimeAgo(lastSavedTime)}
                      </span>
                    )}
                  </div>
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
                  {chatMessages.length === 0 ? (
                    <div className="empty-chat">
                      <div className="empty-icon">🤖</div>
                      <h3>Ask me anything about your journal</h3>
                      <p>I can help you reflect on your entries, find patterns, or answer questions about your thoughts.</p>
                    </div>
                  ) : (
                    chatMessages.map((msg, index) => (
                      <div key={index} className={`chat-message ${msg.type}`}>
                        <div className="message-content">{msg.content}</div>
                        {msg.sources && (
                          <div className="message-sources">
                            <span className="sources-label">Sources:</span>
                            {msg.sources.map((source, idx) => (
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
          {entries.length === 0 ? (
            <div className="empty-entries">
              <div className="empty-icon">📝</div>
              <p>No entries yet</p>
              <span>Start writing to see your journal history here</span>
            </div>
          ) : (
            entries.map((entry) => (
              <div 
                key={entry.entry_id}
                className={`entry-item ${selectedEntry?.entry_id === entry.entry_id ? 'selected' : ''}`}
                onClick={() => setSelectedEntry(entry)}
              >
                <div className="entry-header">
                  <span className="entry-id">#{entry.entry_id}</span>
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
              <h4>Entry #{selectedEntry.entry_id}</h4>
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
