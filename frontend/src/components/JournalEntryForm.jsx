import React, { useState, useRef } from 'react';
import axios from 'axios';
import './JournalEntryForm.css';

function JournalEntryForm() {
  const [content, setContent] = useState('');
  const [message, setMessage] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [audioBlob, setAudioBlob] = useState(null);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!content.trim()) {
      setMessage('Content cannot be empty');
      return;
    }
    
    setIsLoading(true);
    try {
      await axios.post('http://localhost:5000/api/entries', {
        content: content
      });
      setMessage('Entry saved successfully!');
      setContent('');
      
      // Call the global refresh function to update the entries list
      if (window.refreshEntries) {
        window.refreshEntries();
      }
      
    } catch (error) {
      setMessage('Error saving entry: ' + error.message);
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
      const formData = new FormData();
      formData.append('audio', blob, 'recording.wav');

      const response = await axios.post('http://localhost:5000/api/audio', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.data.transcription) {
        setContent(response.data.transcription);
        // Make the API call here
        const entryResponse = await axios.post('http://localhost:5000/api/entries', {
          content: response.data.transcription
        });
        
        setMessage('Entry saved successfully!');
        // Notify parent component to refresh entries
        if (window.refreshEntries) {
          window.refreshEntries();
        }
      }
    } catch (error) {
      console.error('Error:', error);
      setMessage('Error processing audio: ' + error.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="journal-form-container">
      <h1></h1>
      {message && <div className="message">{message}</div>}
      <form onSubmit={handleSubmit}>
        <div className="textarea-container">
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Enter your text here..."
            rows="10"
            cols="50"
            disabled={isLoading}
          ></textarea>
        </div>
        <div className="button-row">
          <div className="left-buttons">
            <button
              type="button"
              onClick={isRecording ? stopRecording : startRecording}
              className={isRecording ? 'recording' : ''}
              disabled={isLoading}
            >
              {isRecording ? 'Stop Recording' : 'Start Recording'}
            </button>
          </div>
          
          <button type="submit" disabled={isLoading || !content.trim()}>
            Save Entry
          </button>
        </div>
      </form>
      {isLoading && (
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Processing your entry...</p>
        </div>
      )}
    </div>
  );
}

export default JournalEntryForm; 