import React, { useState } from 'react';
import axios from 'axios';
import './rootPageForm.css';  // Make sure to import the CSS

function PageForm() {
  const [content, setContent] = useState('');
  const [message, setMessage] = useState('');
  const [story, setStory] = useState('');

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
          <button type="submit">Save Entry</button>
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