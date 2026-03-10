import React, { useState, useRef, useEffect, useContext, useLayoutEffect } from 'react';
import { supabase } from '../context/supabase.js';
import ReactMarkdown from 'react-markdown';
import { AuthContext } from '../context/AuthContext';
import { NavigationContext } from '../App';
import * as d3 from 'd3';
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
        <ReactMarkdown>{displayedText}</ReactMarkdown>
        {isTyping && isLastMessage && message.type === 'ai' && <span className="typing-cursor">|</span>}
      </div>
      {message.sources && message.sources.length > 0 && showSources && (
        <div className="message-sources fade-in">
          <span className="sources-label">Sources:</span>
          {(message.sources || []).map((source, idx) => (
            <button 
              key={`${source.user_entry_id ?? 'na'}-${idx}`} 
              className="source-link"
                onClick={() => onSourceClick(source.entry_id)}
            >
              Entry #{source.user_entry_id}
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
  const [monthlySummaries, setMonthlySummaries] = useState([]);
  const [selectedEntry, setSelectedEntry] = useState(null);
  const [selectedSummary, setSelectedSummary] = useState(null);
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
  const [yapMode, setYapMode] = useState('free'); // 'guided' | 'free'
  
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const messagesEndRef = useRef(null);
  const yapTextareaRef = useRef(null);
  const [yapSendTick, setYapSendTick] = useState(0); // increment after each send
  const [showSignInModal, setShowSignInModal] = useState(false);
  const [hasTriedToSave, setHasTriedToSave] = useState(false);
  const [guestMessageCount, setGuestMessageCount] = useState(0);
  const { currentUser } = useContext(AuthContext);
  const navigationContext = useContext(NavigationContext);
  const navigate = navigationContext?.navigate || ((path) => { window.location.href = path; });

  const generateId = () => {
    try {
      if (crypto && typeof crypto.randomUUID === 'function') {
        return crypto.randomUUID();
      }
    } catch (_) {}
    return `m_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
  };

  // localStorage helpers for unauthenticated users
  const STORAGE_KEY = 'yapper_local_entries';
  
  const loadLocalEntries = () => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        return JSON.parse(stored);
      }
    } catch (error) {
      console.error('Error loading local entries:', error);
    }
    return [];
  };

  const saveLocalEntry = (entry) => {
    try {
      const entries = loadLocalEntries();
      entries.unshift(entry);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(entries));
      return entries;
    } catch (error) {
      console.error('Error saving local entry:', error);
      return [];
    }
  };

  const clearLocalEntries = () => {
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch (error) {
      console.error('Error clearing local entries:', error);
    }
  };

  // Sync local entries to backend when user logs in
  const syncLocalEntries = async () => {
    const localEntries = loadLocalEntries();
    if (localEntries.length === 0) return;

    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) return;

      const accessToken = session.access_token;
      const backendUrl = import.meta.env.VITE_BACKEND_URL || 'https://your-app.railway.app';
      const createUrl = `${backendUrl}/api/entries`;

      // Sync each local entry to backend
      for (const entry of localEntries) {
        try {
          const response = await fetch(createUrl, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${accessToken}`
            },
            body: JSON.stringify({
              content: entry.content
            })
          });

          if (response.ok) {
            console.log('Synced local entry to backend');
          }
        } catch (error) {
          console.error('Error syncing entry:', error);
        }
      }

      // Clear local entries after successful sync
      clearLocalEntries();
      // Reload entries from backend
      loadEntries();
    } catch (error) {
      console.error('Error syncing local entries:', error);
    }
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

  const loadMonthlySummaries = async () => {
    try {
      console.log('Loading monthly summaries for user:', currentUser?.id);
      
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) {
        console.error('No authentication session found');
        return;
      }

      const accessToken = session.access_token;
      const backendUrl = import.meta.env.VITE_BACKEND_URL || 'https://yapper-production-a5e0.up.railway.app';
      const summariesUrl = `${backendUrl}/api/monthly-summaries`;
      
      const response = await fetch(summariesUrl, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${accessToken}`
        }
      });

      if (!response.ok) {
        console.error('Error loading monthly summaries:', response.status);
        setMonthlySummaries([]);
        return;
      }

      const data = await response.json();
      console.log('Monthly summaries loaded:', data);
      setMonthlySummaries(data || []);
    } catch (error) {
      console.error('Error loading monthly summaries:', error);
      setMonthlySummaries([]);
    }
  };

  // Load entries on component mount
  useEffect(() => {
    if (currentUser) {
      loadEntries();
      loadMonthlySummaries();
      // Sync local entries when user logs in
      syncLocalEntries();
      // Close modal if user logs in
      setShowSignInModal(false);
      // Reset guest message count when user logs in
      setGuestMessageCount(0);
    } else {
      // Load from localStorage when not authenticated
      const localEntries = loadLocalEntries();
      setEntries(localEntries);
      
      // Start 2-minute timer for unauthenticated users
      const timer = setTimeout(() => {
        if (!currentUser && !hasTriedToSave) {
          setShowSignInModal(true);
        }
      }, 2 * 60 * 1000); // 2 minutes
      
      return () => clearTimeout(timer);
    }
  }, [currentUser, hasTriedToSave]);

  // Seed Yap with a static opening message the first time the tab is opened
  useEffect(() => {
    if (activeTab === 'yap' && yapMessages.length === 0) {
      setYapMessages([
        { id: generateId(), type: 'ai', content: "What stood out today?" }
      ]);
    }
  }, [activeTab, yapMessages.length]);

  const loadEntries = async () => {
    if (!currentUser) {
      // Load from localStorage when not authenticated
      const localEntries = loadLocalEntries();
      setEntries(localEntries);
      return;
    }

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
    
    const savedContent = content; // Save content before clearing
    
    // If not authenticated, show sign-in modal
    if (!currentUser) {
      setHasTriedToSave(true);
      setShowSignInModal(true);
      return;
    }
    
    // Optimistic UI update - add entry immediately
    const optimisticId = `temp_${Date.now()}`;
    setEntries(prev => {
      const nextNumber = (prev && prev.length > 0)
        ? ((prev[0].user_entry_id || 0) + 1)
        : 1;
      const optimisticEntry = {
        entry_id: optimisticId,
        user_entry_id: nextNumber,
        content: savedContent,
        created_at: new Date().toISOString(),
        __optimistic: true
      };
      return [optimisticEntry, ...(prev || [])];
    });
    
    // Clear content immediately for snappy feel
    setContent('');
    setMessage('Saving...');
    setIsLoading(true);
    
    try {
      // Get Supabase session for auth token
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) {
        throw new Error('No authentication session found');
      }

      const accessToken = session.access_token;
      const backendUrl = import.meta.env.VITE_BACKEND_URL || 'https://your-app.railway.app';
      const createUrl = `${backendUrl}/api/entries`;
      
      const response = await fetch(createUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify({
          content: savedContent
        })
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`HTTP error! status: ${response.status}, body: ${errorText}`);
      }

      const data = await response.json();
      
      // Replace optimistic entry with real entry
      setEntries(prev => {
        const filtered = prev.filter(entry => entry.entry_id !== optimisticId);
        return [data, ...filtered];
      });
      
      setMessage('Entry saved successfully!');
      
      // Clear success message after 3 seconds
      setTimeout(() => {
        setMessage('');
      }, 3000);
      
    } catch (error) {
      console.error('Error saving entry:', error);
      
      // Remove optimistic entry on error
      setEntries(prev => prev.filter(entry => entry.entry_id !== optimisticId));
      
      // Restore content so user can try again
      setContent(savedContent);
      
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
      
      const transcription = data.transcription || '';
      
      if (!transcription.trim()) {
        setMessage('No speech detected in recording');
        setTimeout(() => setMessage(''), 3000);
        return;
      }
      
        // Handle transcription based on current mode
      if (yapMode === 'guided') {
        // Yap mode: Send transcription to chat
        setMessage('Transcription received! Sending to chat...');
        
        // Use the transcription as if the user typed it
        const userText = transcription;
        
        // Add user message and empty AI message, and get updated messages for API call
        const userMsgId = generateId();
        const aiMsgId = generateId();
        let updatedMessages;
        setYapMessages(prev => {
          updatedMessages = [
            ...prev,
            { id: userMsgId, type: 'user', content: userText },
            { id: aiMsgId, type: 'ai', content: '' }
          ];
          return updatedMessages;
        });

        try {
          setIsYapLoading(true);
          
          // Get auth token
          const { data: { session } } = await supabase.auth.getSession();
          if (!session) throw new Error('No active session');
          
          // Build messages array for API (exclude the empty AI message we just added)
          const messagesForAPI = updatedMessages.slice(0, -1).map(m => ({
            type: m.type,
            content: m.content || ''
          }));
          
          // Call backend endpoint
          const backendUrl = import.meta.env.VITE_BACKEND_URL || 'https://your-app.railway.app';
          const response = await fetch(`${backendUrl}/api/converse/stream`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${session.access_token}`
            },
            body: JSON.stringify({
              messages: messagesForAPI,
              user_input: userText
            })
          });
          
          if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`HTTP ${response.status}: ${errorText}`);
          }
          
          // Stream the response
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
          
          setMessage('Transcription sent to chat!');
          setTimeout(() => setMessage(''), 2000);
        } catch (err) {
          console.error('Yap chat error:', err);
          setYapMessages(prev => ([...prev, { id: generateId(), type: 'ai', content: 'Sorry, I ran into an error. Please try again.' }]));
          setMessage('Error sending to chat: ' + err.message);
          setTimeout(() => setMessage(''), 5000);
        } finally {
          setIsYapLoading(false);
          setIsYapSaved(false);
        }
      } else {
        // Free Hand mode: Populate textarea with transcription
        setContent(transcription);
        setMessage('Transcription ready! Review and edit before saving.');
        setTimeout(() => setMessage(''), 3000);
      }
      
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

    // If not authenticated, show message
    if (!currentUser) {
      setMessage('Please sign in to use the chat feature.');
      setTimeout(() => setMessage(''), 5000);
      return;
    }

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
      const chatUrl = `${backendUrl}/api/converse/stream`;
      
      console.log('Environment check:');
      console.log('VITE_BACKEND_URL:', import.meta.env.VITE_BACKEND_URL);
      console.log('Backend URL used:', backendUrl);
      console.log('Request URL:', chatUrl);
      console.log('Request method:', 'POST');
      console.log('Request headers:', {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken.substring(0, 20)}...`
      });
      
      // Build conversation messages for converse endpoint
      const yapMessages = (chatMessages || []).map(m => ({
        type: m.type,
        content: m.content || ''
      }));

      // Make streaming API call to converse endpoint with RAG
      const response = await fetch(chatUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify({ 
          messages: yapMessages,
          user_input: userContent,
          use_rag: true  // Chat tab uses RAG to answer questions about past entries
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
        id: generateId(),
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

    // If not authenticated, show sign-in modal
    if (!currentUser) {
      setHasTriedToSave(true);
      setShowSignInModal(true);
      return;
    }

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

      // Get auth token
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) return;
      
      // Use new backend endpoint
      const backendUrl = import.meta.env.VITE_BACKEND_URL || 'https://your-app.railway.app';
      const res = await fetch(`${backendUrl}/api/converse/save`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`
        },
        body: JSON.stringify({ conversation: transcript }),
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

  // After a message is sent and the DOM has updated, refocus + set caret.
  useLayoutEffect(() => {
    if (!yapTextareaRef.current) return;
    requestAnimationFrame(() => {
      const el = yapTextareaRef.current;
      try {
        el.focus();
        const len = el.value ? el.value.length : 0;
        el.setSelectionRange(len, len);
      } catch {}
    });
  }, [yapSendTick]);

  const handleYapSubmit = async (e) => {
    e.preventDefault();
    if (!yapInput.trim()) return;
    
    // If not authenticated, check message count
    if (!currentUser) {
      if (guestMessageCount >= 3) {
        setShowSignInModal(true);
        setMessage('Please sign in to continue the conversation.');
        setTimeout(() => setMessage(''), 5000);
        return;
      }
      // Increment guest message count
      setGuestMessageCount(prev => prev + 1);
    }
    
    const userText = yapInput;
    setYapInput('');
    setYapSendTick((t) => t + 1);
    
    // Keep focus in textarea
    requestAnimationFrame(() => {
      if (yapTextareaRef.current) {
        yapTextareaRef.current.focus();
        const v = yapTextareaRef.current.value || '';
        yapTextareaRef.current.setSelectionRange(v.length, v.length);
      }
    });

    // Add user message and empty AI message
    const userMsgId = generateId();
    const aiMsgId = generateId();
    setYapMessages(prev => ([
      ...prev,
      { id: userMsgId, type: 'user', content: userText },
      { id: aiMsgId, type: 'ai', content: '' }
    ]));

    try {
      setIsYapLoading(true);
      
      // Get auth token (optional for guest users)
      const { data: { session } } = await supabase.auth.getSession();
      const accessToken = session?.access_token;
      
      // Call new backend endpoint
      const backendUrl = import.meta.env.VITE_BACKEND_URL || 'https://your-app.railway.app';
      const headers = {
        'Content-Type': 'application/json'
      };
      
      // Only add auth header if user is authenticated
      if (accessToken) {
        headers['Authorization'] = `Bearer ${accessToken}`;
      }
      
      const response = await fetch(`${backendUrl}/api/converse/stream`, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({
          messages: yapMessages,
          user_input: userText,
          use_rag: false 
        })
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        // If unauthenticated and backend requires auth, show sign-in modal
        if (response.status === 401 && !currentUser) {
          setShowSignInModal(true);
          setYapMessages(prev => prev.filter(msg => msg.id !== aiMsgId));
          setMessage('Please sign in to continue the conversation.');
          setTimeout(() => setMessage(''), 5000);
          return;
        }
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }
      
      // Stream the response
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
      
      // After 3rd message, show sign-in prompt
      if (!currentUser && guestMessageCount >= 2) {
        setTimeout(() => {
          setShowSignInModal(true);
        }, 1000);
      }
    } catch (err) {
      console.error('Yap chat error:', err);
      setYapMessages(prev => {
        // Remove the empty AI message if there was an error
        const filtered = prev.filter(msg => msg.id !== aiMsgId);
        return [...filtered, { id: generateId(), type: 'ai', content: 'Sorry, I ran into an error. Please try again.' }];
      });
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
            Yap Chat 
          </button>
          <button 
            className={`tab-button ${activeTab === 'timeline' ? 'active' : ''}`} 
            onClick={() => setActiveTab('timeline')}>
              Timeline
            </button>
        </div>

        {/* Tab Content */}
        <div className="tab-content">
          {activeTab === 'yap' && (
            <div className="journal-tab">
              <div className="journal-form">
                <div className="textarea-wrapper">
                  <div className="mode-toggle">
                  <button className={`mode-option ${yapMode === 'free' ? 'active' : ''}`} onClick={() => setYapMode('free')}>Traditional</button>
                    <button className={`mode-option ${yapMode === 'guided' ? 'active' : ''}`} onClick={() => setYapMode('guided')}>Conversation</button>
                  </div>
                  {yapMode === 'guided' ? (
                    <>
                      {!currentUser && guestMessageCount > 0 && (
                        <div style={{
                          padding: '8px 12px',
                          marginBottom: '12px',
                          backgroundColor: '#FFF3CD',
                          border: '1px solid #FFC107',
                          borderRadius: '6px',
                          fontSize: '14px',
                          color: '#856404',
                          textAlign: 'center'
                        }}>
                          {guestMessageCount < 3 
                            ? `You have ${3 - guestMessageCount} free message${3 - guestMessageCount === 1 ? '' : 's'} remaining. Sign in to continue.`
                            : 'Please sign in to continue the conversation.'}
                        </div>
                      )}
                      <div className="messages-container">
                        {(yapMessages || []).map((msg, idx) => (
                          <div key={msg.id} className={`chat-message ${msg.type}`}>
                            <div className="message-content">
                              <ReactMarkdown>{msg.content}</ReactMarkdown>
                            </div>
                          </div>
                        ))}
                        <div ref={yapEndRef} />
                      </div>
                    </>
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
                        </button>
                        <div className="chat-input-wrapper">
                          <textarea
                            value={yapInput}
                            onChange={(e) => setYapInput(e.target.value)}
                            placeholder="Type your reply..."
                            className="chat-textarea"
                            rows={1}
                            autoFocus
                            onKeyDown={(e) => {
                              if (e.isComposing) return;
                              if (e.key === 'Enter' && !e.shiftKey) {
                                e.preventDefault();
                                if (yapInput.trim()) handleYapSubmit(e);
                              }
                            }}
                            ref={(el) => {
                              yapTextareaRef.current = el;
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
                          <button type="submit" className="send-inline" disabled={isYapLoading || !yapInput.trim()} title="Send (Enter)" onMouseDown={(e) => e.preventDefault()}><span style={{ fontWeight: 'bold', fontSize: '18px' }}>↑</span></button>
                        </div>
                      </form>
                    ) : (
                      <button
                        type="button"
                        onClick={isRecording ? stopRecording : startRecording}
                        className={`record-button ${isRecording ? 'recording' : ''}`}
                        disabled={isLoading}
                      >
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
                      onClick={async (e) => {
                        e.preventDefault();
                        if (!content.trim()) {
                          setMessage('Content cannot be empty');
                          return;
                        }
                        
                        const savedContent = content;
                        
                        // If not authenticated, show sign-in modal
                        if (!currentUser) {
                          setHasTriedToSave(true);
                          setShowSignInModal(true);
                          return;
                        }
                        
                        // Optimistic UI update - add entry immediately
                        const optimisticId = `temp_${Date.now()}`;
                        setEntries(prev => {
                          const nextNumber = (prev && prev.length > 0)
                            ? ((prev[0].user_entry_id || 0) + 1)
                            : 1;
                          const optimisticEntry = {
                            entry_id: optimisticId,
                            user_entry_id: nextNumber,
                            content: savedContent,
                            created_at: new Date().toISOString(),
                            __optimistic: true
                          };
                          return [optimisticEntry, ...(prev || [])];
                        });
                        
                        // Clear content immediately for snappy feel
                        setContent('');
                        setMessage('Saving...');
                        setIsLoading(true);
                        
                        try {
                          
                          // Get Supabase session for auth token
                          const { data: { session } } = await supabase.auth.getSession();
                          if (!session) {
                            throw new Error('No authentication session found');
                          }

                          const accessToken = session.access_token;
                          const backendUrl = import.meta.env.VITE_BACKEND_URL || 'https://your-app.railway.app';
                          const createUrl = `${backendUrl}/api/entries`;
                          
                          console.log('Creating entry via backend API (Free Hand mode)...');
                          console.log('Backend URL:', createUrl);
                          console.log('Content:', content);
                          
                          const response = await fetch(createUrl, {
                            method: 'POST',
                            headers: {
                              'Content-Type': 'application/json',
                              'Authorization': `Bearer ${accessToken}`
                            },
                            body: JSON.stringify({
                              content: savedContent
                            })
                          });

                          console.log('Create entry response status:', response.status);
                          
                          if (!response.ok) {
                            const errorText = await response.text();
                            console.log('Error response body:', errorText);
                            throw new Error(`HTTP error! status: ${response.status}, body: ${errorText}`);
                          }

                          const data = await response.json();
                          
                          // Replace optimistic entry with real entry
                          setEntries(prev => {
                            const filtered = prev.filter(entry => entry.entry_id !== optimisticId);
                            return [data, ...filtered];
                          });
                          
                          setMessage('Entry saved successfully!');
                          
                          // Clear success message after 3 seconds
                          setTimeout(() => {
                            setMessage('');
                          }, 3000);
                          
                        } catch (error) {
                          console.error('Error saving entry:', error);
                          
                          // Remove optimistic entry on error
                          setEntries(prev => prev.filter(entry => entry.entry_id !== optimisticId));
                          
                          // Restore content so user can try again
                          setContent(savedContent);
                          
                          setMessage('Error saving entry: ' + error.message);
                          
                          // Clear error after 5 seconds
                          setTimeout(() => {
                            setMessage('');
                          }, 5000);
                        } finally {
                          setIsLoading(false);
                        }
                      }}
                      disabled={!content.trim() || isLoading}
                      className="save-button"
                    >
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
                  <h2>Yap Chat</h2>
                </div>
                
                {!currentUser && (
                  <div style={{ padding: '20px', textAlign: 'center', color: '#856404' }}>
                    <p>Please sign in to use the chat feature.</p>
                  </div>
                )}
                
                <div className="messages-container">
                  {(!chatMessages || chatMessages.length === 0) ? (
                    <div className="empty-chat">
                      <h3>Ask about your past Yaps</h3>
                      <p>I can help you reflect on entries, find patterns, or answer questions.</p>
                      {!currentUser && (
                        <p style={{ marginTop: '10px', color: '#856404' }}>Sign in to get started.</p>
                      )}
                    </div>
                  ) : (
                    (chatMessages || []).map((msg, index) => {
                      const isLastMessage = index === chatMessages.length - 1;
                      return (
                        <ChatMessage
                          key={msg.id}
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
                    placeholder={currentUser ? "Ask about your journal entries..." : "Sign in to use chat"}
                    disabled={isChatLoading || !currentUser}
                    className="chat-input"
                  />
                  <button 
                    type="submit" 
                    disabled={isChatLoading || !chatInput.trim() || !currentUser}
                    className="send-button"
                  >
                    <span style={{ fontWeight: 'bold', fontSize: '18px' }}>↑</span>
                  </button>
                </form>
              </div>
            </div>
          )}

          {activeTab === 'timeline' && (
            <div className="timeline-tab">
              <D3Timeline 
                summaries={monthlySummaries} 
                onSummaryClick={setSelectedSummary}
              />
              {selectedSummary && (
                <div className="summary-detail">
                  <div className="detail-header">
                    <h4>{selectedSummary.month_year}</h4>
                    <span className="detail-meta">{selectedSummary.list_of_entries?.length || 0} entries</span>
                  </div>
                  <div className="detail-content">{selectedSummary.summary}</div>
                </div>
              )}
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
            <span className="toggle-icon">📖</span>
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
                key={entry.entry_id ?? `tmp-${entry.created_at}-${Math.random()}`}
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
          <span className="toggle-icon">📖</span>
        </button>
      )}

      {/* Sign-In Modal */}
      {showSignInModal && !currentUser && (
        <div 
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000
          }}
        >
          <div 
            style={{
              backgroundColor: 'white',
              borderRadius: '12px',
              padding: '32px',
              maxWidth: '500px',
              width: '90%',
              boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
            }}
          >
            <h2 style={{ marginTop: 0, marginBottom: '16px', fontSize: '24px' }}>
              Sign in to save your entries
            </h2>
            <p style={{ marginBottom: '24px', color: '#666', lineHeight: '1.5' }}>
              You need to sign in to save your entries. Please create an account or sign in to continue.
            </p>
            <div style={{ display: 'flex', gap: '12px', flexDirection: 'column' }}>
              <button
                onClick={() => navigate('/login')}
                style={{
                  padding: '14px 28px',
                  backgroundColor: '#4B286D',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  fontSize: '16px',
                  fontWeight: '600',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  boxShadow: '0 2px 4px rgba(75, 40, 109, 0.2)',
                  letterSpacing: '0.3px'
                }}
                onMouseEnter={(e) => {
                  e.target.style.backgroundColor = '#3A1F56';
                  e.target.style.boxShadow = '0 4px 8px rgba(75, 40, 109, 0.3)';
                  e.target.style.transform = 'translateY(-1px)';
                }}
                onMouseLeave={(e) => {
                  e.target.style.backgroundColor = '#4B286D';
                  e.target.style.boxShadow = '0 2px 4px rgba(75, 40, 109, 0.2)';
                  e.target.style.transform = 'translateY(0)';
                }}
                onMouseDown={(e) => {
                  e.target.style.transform = 'translateY(0)';
                  e.target.style.boxShadow = '0 1px 2px rgba(75, 40, 109, 0.2)';
                }}
                onMouseUp={(e) => {
                  e.target.style.transform = 'translateY(-1px)';
                  e.target.style.boxShadow = '0 4px 8px rgba(75, 40, 109, 0.3)';
                }}
              >
                Sign In
              </button>
              <button
                onClick={() => navigate('/register')}
                style={{
                  padding: '14px 28px',
                  backgroundColor: 'transparent',
                  color: '#4B286D',
                  border: '2px solid #4B286D',
                  borderRadius: '8px',
                  fontSize: '16px',
                  fontWeight: '600',
                  cursor: 'pointer',
                  transition: 'all 0.2s ease',
                  letterSpacing: '0.3px'
                }}
                onMouseEnter={(e) => {
                  e.target.style.backgroundColor = '#F7F0DD';
                  e.target.style.borderColor = '#3A1F56';
                  e.target.style.color = '#3A1F56';
                  e.target.style.transform = 'translateY(-1px)';
                  e.target.style.boxShadow = '0 2px 4px rgba(75, 40, 109, 0.15)';
                }}
                onMouseLeave={(e) => {
                  e.target.style.backgroundColor = 'transparent';
                  e.target.style.borderColor = '#4B286D';
                  e.target.style.color = '#4B286D';
                  e.target.style.transform = 'translateY(0)';
                  e.target.style.boxShadow = 'none';
                }}
                onMouseDown={(e) => {
                  e.target.style.transform = 'translateY(0)';
                  e.target.style.boxShadow = 'none';
                }}
                onMouseUp={(e) => {
                  e.target.style.transform = 'translateY(-1px)';
                  e.target.style.boxShadow = '0 2px 4px rgba(75, 40, 109, 0.15)';
                }}
              >
                Create Account
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// D3 Timeline Component - Now uses monthly summaries
const D3Timeline = ({ summaries, onSummaryClick }) => {
  const svgRef = useRef(null);
  const containerRef = useRef(null);

  // Parse month_year string (e.g., "April 2025") to Date
  const parseMonthYear = (monthYearStr) => {
    try {
      const [month, year] = monthYearStr.split(' ');
      const monthIndex = new Date(`${month} 1, ${year}`).getMonth();
      return new Date(parseInt(year), monthIndex, 1);
    } catch (e) {
      console.error('Error parsing month_year:', monthYearStr, e);
      return new Date();
    }
  };

  useEffect(() => {
    if (!summaries || summaries.length === 0) return;

    // Sort summaries by date (oldest first)
    const sortedSummaries = [...summaries].sort((a, b) => {
      const dateA = parseMonthYear(a.month_year);
      const dateB = parseMonthYear(b.month_year);
      return dateA - dateB;
    });

    // Clear previous content
    d3.select(svgRef.current).selectAll("*").remove();

    const container = containerRef.current;
    if (!container) return;

    const width = container.clientWidth || 800;
    const height = 300;
    const margin = { top: 60, right: 40, bottom: 60, left: 40 };
    const chartWidth = width - margin.left - margin.right;
    const chartHeight = height - margin.top - margin.bottom;

    // Set up SVG
    const svg = d3.select(svgRef.current)
      .attr("width", width)
      .attr("height", height);

    const g = svg.append("g")
      .attr("transform", `translate(${margin.left},${margin.top})`);

    // Parse dates from month_year strings
    const dates = sortedSummaries.map(summary => parseMonthYear(summary.month_year));
    const minDate = d3.min(dates);
    const maxDate = d3.max(dates);
    
    // Add padding to domain
    const dateRange = maxDate - minDate;
    const padding = dateRange * 0.1;

    // Create scale
    const xScale = d3.scaleTime()
      .domain([new Date(minDate - padding), new Date(maxDate + padding)])
      .range([0, chartWidth]);

    // Draw timeline line
    g.append("line")
      .attr("x1", 0)
      .attr("x2", chartWidth)
      .attr("y1", chartHeight / 2)
      .attr("y2", chartHeight / 2)
      .attr("stroke", "#4B286D")
      .attr("stroke-width", 3);

    // Draw markers and labels
    sortedSummaries.forEach((summary, i) => {
      const date = parseMonthYear(summary.month_year);
      const x = xScale(date);
      const y = chartHeight / 2;

      // Draw circle marker
      const circle = g.append("circle")
        .attr("cx", x)
        .attr("cy", y)
        .attr("r", 10)
        .attr("fill", "#4B286D")
        .attr("stroke", "#F6ECD1")
        .attr("stroke-width", 2)
        .style("cursor", "pointer")
        .on("click", () => onSummaryClick && onSummaryClick(summary))
        .on("mouseover", function() {
          d3.select(this).attr("r", 14);
        })
        .on("mouseout", function() {
          d3.select(this).attr("r", 10);
        });

      // Draw month/year label above
      g.append("text")
        .attr("x", x)
        .attr("y", y - 25)
        .attr("text-anchor", "middle")
        .attr("fill", "#4B286D")
        .attr("font-size", "13px")
        .attr("font-weight", "600")
        .text(summary.month_year);
    });

  }, [summaries, onSummaryClick]);

  if (!summaries || summaries.length === 0) {
    return (
      <div className="empty-timeline">
        <div className="empty-icon">📅</div>
        <h3>No monthly summaries yet</h3>
        <p>Monthly summaries are generated automatically at the beginning of each month</p>
      </div>
    );
  }

  return (
    <div ref={containerRef} className="d3-timeline-container">
      <svg ref={svgRef}></svg>
    </div>
  );
};

export default JournalPage;
