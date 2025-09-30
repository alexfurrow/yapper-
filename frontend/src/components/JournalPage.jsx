import React, { useState, useRef, useEffect, useContext } from 'react';
import { supabase } from '../context/supabase.js';
import { AuthContext } from '../context/AuthContext';
import './JournalPage.css';

// Chat message component with typewriter effect (simplified)
const ChatMessage = ({ message, isLastMessage, onSourceClick }) => {
  const [displayedText, setDisplayedText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [showSources, setShowSources] = useState(false);
  const intervalId = useRef(null);
  const currentIndex = useRef(0);

  useEffect(() => {
    // Non-AI messages render instantly
    if (message.type !== 'ai') {
      if (intervalId.current) {
        clearInterval(intervalId.current);
        intervalId.current = null;
      }
      currentIndex.current = (message.content || '').length;
      setDisplayedText(message.content || '');
      setIsTyping(false);
      setShowSources(true);
      return;
    }

    const content = message.content || '';

    // Reset state when empty
    if (content.length === 0) {
      if (intervalId.current) {
        clearInterval(intervalId.current);
        intervalId.current = null;
      }
      currentIndex.current = 0;
      setDisplayedText('');
      setIsTyping(false);
      setShowSources(false);
      return;
    }

    // If our index is ahead of current content (rare), clamp it
    if (currentIndex.current > content.length) {
      currentIndex.current = content.length;
    }

    // Start a simple interval-based typewriter when needed
    if (!intervalId.current && currentIndex.current < content.length) {
      setIsTyping(true);
      const delayMs = 7; // ~140 cps
      intervalId.current = setInterval(() => {
        const target = content.length;
        if (currentIndex.current < target) {
          currentIndex.current += 1;
          setDisplayedText(content.slice(0, currentIndex.current));
        } else {
          // Finished animating current content
          clearInterval(intervalId.current);
          intervalId.current = null;
          setIsTyping(false);
          setShowSources(true);
        }
      }, delayMs);
    }

    return () => {
      if (intervalId.current) {
        clearInterval(intervalId.current);
        intervalId.current = null;
      }
    };
  }, [message.content, message.type]);
  
  return (
    <div className={`chat-message ${message.type} ${isTyping ? 'typing' : ''}`}>
      <div className="message-content">
        {displayedText}
        {isTyping && isLastMessage && message.type === 'ai' && <span className="typing-cursor">|</span>}
      </div>
      {message.sources && message.sources.length > 0 && showSources && (
        <div className="message-sources fade-in">
          <span className="sources-label">Sources:</span>
          {(message.sources || []).map((source, idx) => (
            <button 
              key={`${source.entry_id}-${idx}`} 
              className="source-link"
              onClick={() => onSourceClick(source.entry_id)}
            >
              Entry #{source.entry_id}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};
function JournalPage() {
  const [activeTab, setActiveTab] = useState('yap');
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
  // Yap (guided conversation) state
  const [yapMessages, setYapMessages] = useState([]);
  const [yapInput, setYapInput] = useState('');
  const [isYapLoading, setIsYapLoading] = useState(false);
  const [isYapSaved, setIsYapSaved] = useState(false);
  const yapEndRef = useRef(null);
  const [yapMode, setYapMode] = useState('guided'); // 'guided' | 'free'
  const [isComposeOpen, setIsComposeOpen] = useState(false);
  
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const messagesEndRef = useRef(null);
  const { currentUser } = useContext(AuthContext);

  const generateId = () => {
    try {
      if (crypto && typeof crypto.randomUUID === 'function') {
        return crypto.randomUUID();
      }
    } catch (_) {}
    return `m_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
  };

  // Auto-scroll to bottom of chat messages
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatMessages]);

  // Auto-scroll Yap
  useEffect(() => {
    yapEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [yapMessages]);

  // Load entries on component mount
  useEffect(() => {
    if (currentUser) {
    loadEntries();
    }
  }, [currentUser]);

  // Seed Yap with an opening AI prompt the first time the tab is opened
  useEffect(() => {
    if (activeTab === 'yap' && yapMessages.length === 0) {
      (async () => {
        try {
          const { data: { session } } = await supabase.auth.getSession();
          if (!session) throw new Error('no session');
          const backendUrl = import.meta.env.VITE_BACKEND_URL || 'https://your-app.railway.app';
          const introUrl = `${backendUrl}/api/chat/yap_intro`;
          const res = await fetch(introUrl, { headers: { Authorization: `Bearer ${session.access_token}` } });
          if (!res.ok) throw new Error(`HTTP ${res.status}`);
          const payload = await res.json();
          const opening = payload.opening || "What's on your mind? Talk as long as you want.";
          const topics = Array.isArray(payload.topics) ? payload.topics : [];
          setYapMessages([
            { id: generateId(), type: 'ai', content: opening },
            ...(topics.length > 0 ? [{ id: generateId(), type: 'ai', content: `You can pick a topic: ${topics.map(t => `“${t}”`).join(', ')}, or choose “Something new”.` }] : [])
          ]);
        } catch (_) {
          setYapMessages([
            { id: generateId(), type: 'ai', content: "What's on your mind? Talk as long as you want." }
          ]);
        }
      })();
    }
  }, [activeTab]);

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
      
      // Get Supabase session for auth token
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) {
        throw new Error('No authentication session found');
      }

      const accessToken = session.access_token;
      const backendUrl = import.meta.env.VITE_BACKEND_URL || 'https://your-app.railway.app';
      const audioUrl = `${backendUrl}/api/audio`;
      
      console.log('Processing audio via backend API...');
      console.log('Backend URL:', audioUrl);
      
      const formData = new FormData();
      formData.append('audio', blob, 'recording.wav');
      
      const response = await fetch(audioUrl, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`
        },
        body: formData
      });

      console.log('Audio processing response status:', response.status);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.log('Error response body:', errorText);
        throw new Error(`HTTP error! status: ${response.status}, body: ${errorText}`);
      }

      const data = await response.json();
      console.log('Audio processed successfully:', data);
      
      setMessage('Audio processed and journal entry created!');
      
      // Refresh entries list
      loadEntries();
      
      // Clear success message after 3 seconds
      setTimeout(() => {
        setMessage('');
      }, 3000);
      
    } catch (error) {
      console.error('Error processing audio:', error);
      setMessage('Error processing audio: ' + error.message);
      
      // Clear error after 5 seconds
      setTimeout(() => {
        setMessage('');
      }, 5000);
    } finally {
      setIsLoading(false);
    }
  };




  // Chat Functions
  const handleChatSubmit = async (e) => {
    e.preventDefault();
    if (!chatInput.trim()) return;

    const userContent = chatInput;
    setChatInput('');

    // Append user + empty AI bubble atomically
    const userMsgId = generateId();
    const aiMsgId = generateId();
    setChatMessages(prev => [
      ...prev,
      { id: userMsgId, type: 'user', content: userContent },
      { id: aiMsgId, type: 'ai', content: '', sources: [] }
    ]);

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
      const chatUrl = `${backendUrl}/api/chat/stream`;
      
      console.log('Environment check:');
      console.log('VITE_BACKEND_URL:', import.meta.env.VITE_BACKEND_URL);
      console.log('Backend URL used:', backendUrl);
      console.log('Request URL:', chatUrl);
      console.log('Request method:', 'POST');
      console.log('Request headers:', {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken.substring(0, 20)}...`
      });
      
      // Make streaming API call to your Railway backend chat endpoint
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

      if (!response.ok) {
        const errorText = await response.text();
        console.error('Error response body:', errorText);
        throw new Error(`HTTP error! status: ${response.status}, body: ${errorText}`);
      }

      // Handle streaming response (SSE)
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });

          let sep;
          while ((sep = buffer.indexOf('\n\n')) !== -1) {
            const block = buffer.slice(0, sep);
            buffer = buffer.slice(sep + 2);
            const lines = block.split('\n');
            for (const line of lines) {
              if (!line.startsWith('data: ')) continue;
              try {
                const evt = JSON.parse(line.slice(6));
                if (evt.type === 'content') {
                  setChatMessages(prev => {
                    const newMessages = [...prev];
                    const last = newMessages[newMessages.length - 1];
                    if (last && last.type === 'ai') {
                      newMessages[newMessages.length - 1] = {
                        ...last,
                        content: (last.content || '') + (evt.data || '')
                      };
                    }
                    return newMessages;
                  });
                } else if (evt.type === 'sources') {
                  setChatMessages(prev => {
                    const newMessages = [...prev];
                    const last = newMessages[newMessages.length - 1];
                    if (last && last.type === 'ai') {
                      newMessages[newMessages.length - 1] = {
                        ...last,
                        sources: evt.data || []
                      };
                    }
                    return newMessages;
                  });
                } else if (evt.type === 'error') {
                  throw new Error(evt.data || 'Streaming error');
                }
              } catch (e) {
                console.warn('Failed to parse streaming data:', e);
              }
            }
          }
        }
      } finally {
        reader.releaseLock();
      }
            
    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage = { 
        type: 'ai', 
        content: `Sorry, I encountered an error: ${error.message}. Please try again.` 
      };
      setChatMessages(prev => [...prev, errorMessage]);
    } finally {
      // no-op
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

  const YAP_SYSTEM_PROMPT = `You are a warm, concise journaling companion. Help the user capture their day.
- Encourage specifics about factual events and feelings
- Ask follow-up questions sparingly
- Invite notes/reminders for later follow-up
- Keep responses brief and friendly`;

  const assembleYapTranscript = (msgs) => {
    try {
      return (msgs || [])
        .filter(m => (m.content || '').trim().length > 0)
        .map(m => `${m.type === 'user' ? '#user:' : '#AI:'} ${m.content.trim()}`)
        .join(' ');
    } catch (_) { return ''; }
  };

  const saveYapEntry = async (opts = { keepalive: false }) => {
    const transcript = assembleYapTranscript(yapMessages);
    if (!transcript || transcript.trim().length === 0) return;

    // Optimistic placeholder in history list
    try {
      const optimisticId = `temp_${Date.now()}`;
      setEntries(prev => {
        const nextNumber = (prev && prev.length > 0)
          ? ((prev[0].user_entry_id || 0) + 1)
          : 1;
        const optimisticEntry = {
          entry_id: optimisticId,
          user_entry_id: nextNumber,
          content: transcript,
          created_at: new Date().toISOString(),
          __optimistic: true
        };
        return [optimisticEntry, ...(prev || [])];
      });

      // Clear Yap UI immediately for a snappy feel
      setYapMessages([]);

      const { data: { session } } = await supabase.auth.getSession();
      if (!session) return;
      const accessToken = session.access_token;
      const backendUrl = import.meta.env.VITE_BACKEND_URL || 'https://your-app.railway.app';
      const createUrl = `${backendUrl}/api/entries`;
      const res = await fetch(createUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify({ content: transcript }),
        keepalive: !!opts.keepalive
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setIsYapSaved(true);
      // Replace optimistic with server data by reloading
      loadEntries();
    } catch (e) {
      console.warn('Yap save failed:', e.message);
    }
  };

  // Autosave on page hide/navigation if there is unsaved Yap content
  useEffect(() => {
    const onPageHide = () => {
      if (!isYapSaved && (yapMessages || []).some(m => m.type === 'user')) {
        saveYapEntry({ keepalive: true });
      }
    };
    window.addEventListener('pagehide', onPageHide);
    return () => window.removeEventListener('pagehide', onPageHide);
  }, [yapMessages, isYapSaved]);

  const handleYapSubmit = async (e) => {
    e.preventDefault();
    if (!yapInput.trim()) return;
    const userText = yapInput;
    setYapInput('');

    const userMsgId = generateId();
    const aiMsgId = generateId();
    setYapMessages(prev => ([
      ...prev,
      { id: userMsgId, type: 'user', content: userText },
      { id: aiMsgId, type: 'ai', content: '' }
    ]));

    try {
      setIsYapLoading(true);
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) throw new Error('No active session');
      const accessToken = session.access_token;
      const backendUrl = import.meta.env.VITE_BACKEND_URL || 'https://your-app.railway.app';
      const chatUrl = `${backendUrl}/api/chat/stream`;
      const response = await fetch(chatUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify({
          message: `${YAP_SYSTEM_PROMPT}\n\nUser: ${userText}`,
          limit: 3
        })
      });
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          let sep;
          while ((sep = buffer.indexOf('\n\n')) !== -1) {
            const block = buffer.slice(0, sep);
            buffer = buffer.slice(sep + 2);
            const lines = block.split('\n');
            for (const line of lines) {
              if (!line.startsWith('data: ')) continue;
              try {
                const evt = JSON.parse(line.slice(6));
                if (evt.type === 'content') {
                  setYapMessages(prev => {
                    const m = [...prev];
                    const last = m[m.length - 1];
                    if (last && last.type === 'ai') {
                      m[m.length - 1] = { ...last, content: (last.content || '') + (evt.data || '') };
                    }
                    return m;
                  });
                }
              } catch (_) {}
            }
          }
        }
      } finally {
        reader.releaseLock();
      }
    } catch (err) {
      console.error('Yap chat error:', err);
      setYapMessages(prev => ([...prev, { type: 'ai', content: 'Sorry, I ran into an error. Please try again.' }]));
    } finally {
      setIsYapLoading(false);
      setIsYapSaved(false);
    }
  };

  return (
    <div className="journal-page">
      {/* Main Content Area */}
      <div className={`main-content ${isSidebarOpen ? 'with-sidebar' : ''}`}>
        {/* Tab Navigation */}
        <div className="tab-navigation">
          <button 
            className={`tab-button ${activeTab === 'yap' ? 'active' : ''}`}
            onClick={() => setActiveTab('yap')}
          >
            Yap
          </button>
          <button 
            className={`tab-button ${activeTab === 'chat' ? 'active' : ''}`}
            onClick={() => setActiveTab('chat')}
          >
            <span className="tab-icon">💬</span>
            History Chat
          </button>
        </div>

        {/* Tab Content */}
        <div className="tab-content">
          {activeTab === 'yap' && (
            <div className="journal-tab">
              <div className="journal-form">
                <div className="textarea-wrapper">
                  <div className="mode-toggle">
                    <button className={`mode-option ${yapMode === 'guided' ? 'active' : ''}`} onClick={() => setYapMode('guided')}>Converse</button>
                    <button className={`mode-option ${yapMode === 'free' ? 'active' : ''}`} onClick={() => setYapMode('free')}>Free Hand</button>
                  </div>
                  {yapMode === 'guided' ? (
                    <div className="messages-container">
                      {(yapMessages || []).map((msg, idx) => (
                        <div key={msg.id || idx} className={`chat-message ${msg.type}`}>
                          <div className="message-content">{msg.content}</div>
                        </div>
                      ))}
                      <div ref={yapEndRef} />
                    </div>
                  ) : (
                    <textarea
                      value={content}
                      onChange={handleContentChange}
                      placeholder="What's on your mind today?"
                      rows="12"
                      disabled={isLoading}
                      className="journal-textarea"
                    />
                  )}
                </div>
                <div className="form-actions">
                  <div className="left-actions">
                    {yapMode === 'guided' ? (
                      <form onSubmit={handleYapSubmit} style={{ display: 'flex', gap: '12px', width: '100%', alignItems: 'center', flex: 1 }}>
                        <button
                          type="button"
                          className={`voice-button ${isRecording ? 'recording' : ''}`}
                          onClick={isRecording ? stopRecording : startRecording}
                          title={isRecording ? 'Stop Recording' : 'Start Recording'}
                        >
                          <span className="mic-icon">🎤</span>
                        </button>
                        {isComposeOpen && (
                          <div className="chat-input-wrapper">
                            <textarea
                              value={yapInput}
                              onChange={(e) => setYapInput(e.target.value)}
                              placeholder="Type your reply..."
                              className="chat-textarea"
                              disabled={isYapLoading}
                              rows={1}
                              onKeyDown={(e) => {
                                if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
                                  e.preventDefault();
                                  if (yapInput.trim()) handleYapSubmit(e);
                                }
                              }}
                              ref={(el) => {
                                if (!el) return;
                                el.style.height = 'auto';
                                const h = Math.min(el.scrollHeight, 240);
                                el.style.height = h + 'px';
                                const btn = el.parentElement && el.parentElement.querySelector('.send-inline');
                                if (btn) {
                                  if (h <= 56) {
                                    btn.style.top = '8px';
                                    btn.style.height = (h - 16) + 'px';
                                  } else {
                                    btn.style.top = '';
                                    btn.style.height = '36px';
                                  }
                                }
                              }}
                              onInput={(e) => {
                                const el = e.currentTarget;
                                el.style.height = 'auto';
                                const h = Math.min(el.scrollHeight, 240);
                                el.style.height = h + 'px';
                                const btn = el.parentElement && el.parentElement.querySelector('.send-inline');
                                if (btn) {
                                  if (h <= 56) {
                                    btn.style.top = '8px';
                                    btn.style.height = (h - 16) + 'px';
                                  } else {
                                    btn.style.top = '';
                                    btn.style.height = '36px';
                                  }
                                }
                              }}
                            />
                            <button type="submit" className="send-inline" disabled={isYapLoading || !yapInput.trim()} title="Send (Cmd/Ctrl+Enter)">↑</button>
                          </div>
                        )}
                        <button
                          type="button"
                          className="compose-button"
                          onClick={() => setIsComposeOpen(prev => !prev)}
                          title={isComposeOpen ? 'Close typing' : 'Type instead'}
                        >
                          ✏️
                        </button>
                      </form>
                    ) : (
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
                    )}
                  </div>
                  {yapMode === 'guided' ? (
                  <button type="button" className="save-button" onClick={() => saveYapEntry()} disabled={yapMessages.length === 0}>
                    Save Entry
                  </button>
                  ) : (
                    <button 
                      type="button" 
                      onClick={(e) => handleSubmit(e)}
                      disabled={!content.trim()}
                      className="save-button"
                    >
                      <span className="button-icon">💾</span>
                      Save Entry
                    </button>
                  )}
                </div>
                {false && <div></div>}
              </div>
            </div>
          )}
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
                  <h2>History Chat</h2>
                </div>
                
                <div className="messages-container">
                  {(!chatMessages || chatMessages.length === 0) ? (
                    <div className="empty-chat">
                      <h3>Ask about your journal</h3>
                      <p>I can help you reflect on entries, find patterns, or answer questions.</p>
                    </div>
                  ) : (
                    (chatMessages || []).map((msg, index) => {
                      const isLastMessage = index === chatMessages.length - 1;
                      return (
                        <ChatMessage
                          key={msg.id || index}
                          message={msg}
                          isLastMessage={isLastMessage}
                          onSourceClick={handleSourceClick}
                        />
                      );
                    })
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
          <h3>Yap History</h3>
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
                className={`entry-item ${entry.__optimistic ? '__optimistic' : ''} ${selectedEntry?.entry_id === entry.entry_id ? 'selected' : ''}`}
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
