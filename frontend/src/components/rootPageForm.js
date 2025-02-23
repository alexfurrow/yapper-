import React, { useState, useRef } from 'react';
import axios from 'axios';
import './rootPageForm.css';  // Make sure to import the CSS

function PageForm() {
  const [content, setContent] = useState('');
  const [message, setMessage] = useState('');
  const [story, setStory] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState(null);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post('http://localhost:5000/api/pages', {
        content: content
      });
      setMessage('Page created successfully!');
      if (response.data.story && response.data.story.story) {
        setStory(response.data.story.story);
      }
      setContent('');
    } catch (error) {
      setMessage('Error creating page: ' + error.message);
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
      const formData = new FormData();
      formData.append('audio', blob, 'recording.wav');

      const response = await axios.post('http://localhost:5000/api/audio', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      if (response.data.transcription) {
        setContent(response.data.transcription);
      }
    } catch (error) {
      console.error('Error uploading audio:', error);
      setMessage('Error uploading audio');
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
            <button type="submit">Save Entry</button>
            <button 
              type="button" 
              onClick={isRecording ? stopRecording : startRecording}
              className={isRecording ? 'recording' : ''}
            >
              {isRecording ? 'Stop Recording' : 'Start Recording'}
            </button>
          </div>
        </form>
      </div>
      
      <div className="story-section">
        {story ? (
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