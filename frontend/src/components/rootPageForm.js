import React, { useState, useRef } from 'react';
import axios from 'axios';
import './rootPageForm.css';  // Make sure to import the CSS

function PageForm() {
  const [content, setContent] = useState('');
  const [message, setMessage] = useState('');
  const [story, setStory] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isLoading, setIsLoading] = useState(false);  // New state for loading
  const [audioBlob, setAudioBlob] = useState(null);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!content.trim()) {
      setMessage('Content cannot be empty');
      return;
    }
    
    setIsLoading(true);  // Start loading
    try {
      const response = await axios.post('http://localhost:5000/api/pages', {
        content: content
      });
      setMessage('Entry saved successfully!');
      if (response.data.story && response.data.story.story) {
        setStory(response.data.story.story);
      }
      setContent('');
    } catch (error) {
      setMessage('Error saving entry: ' + error.message);
    } finally {
      setIsLoading(false);  // Stop loading regardless of outcome
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
      setIsLoading(true);  // Start loading
      const formData = new FormData();
      formData.append('audio', blob, 'recording.wav');

      const response = await axios.post('http://localhost:5000/api/audio', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.data.transcription) {
        setContent(response.data.transcription);
        // Don't call handleSubmit directly, as it creates a new loading state
        // Instead, make the API call here
        const pageResponse = await axios.post('http://localhost:5000/api/pages', {
          content: response.data.transcription
        });
        
        if (pageResponse.data.story && pageResponse.data.story.story) {
          setStory(pageResponse.data.story.story);
        }
        setMessage('Entry saved successfully!');
      }
    } catch (error) {
      console.error('Error:', error);
      setMessage('Error processing audio: ' + error.message);
    } finally {
      setIsLoading(false);  // Stop loading regardless of outcome
    }
  };

  return (
    <div className="page-form-container">
      <div className="input-section">
        <h1>Txtile</h1>
        {message && <div className="message">{message}</div>}
        <form onSubmit={handleSubmit}>
          <div>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Enter your text here..."
              rows="10"
              cols="50"
              required
            />
          </div>
          <div className="button-group">
            <button type="submit" disabled={isLoading}>Save Entry</button>
            <button 
              type="button" 
              onClick={isRecording ? stopRecording : startRecording}
              className={isRecording ? 'recording' : ''}
              disabled={isLoading}
            >
              {isRecording ? 'Stop Recording' : 'Start Recording'}
            </button>
          </div>
        </form>
      </div>
      
      <div className="story-section">
        {isLoading ? (
          <div className="loading-container">
            <div className="loading-spinner"></div>
            <p>Narrative is being constructed...</p>
          </div>
        ) : story ? (
          <>
            <h2>Your Narrative</h2>
            <div className="story-text">
              {story}
            </div>
          </>
        ) : (
          <div className="empty-story">
            <p>Your narrative will appear here...</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default PageForm; 