import React, { useState } from 'react';
import axios from 'axios';

function PageForm() {
  const [content, setContent] = useState('');
  const [message, setMessage] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post('http://localhost:5000/api/pages', {
        content: content
      });
      setMessage('Page created successfully!');
      setContent('');
    } catch (error) {
      setMessage('Error creating page: ' + error.message);
    }
  };

  return (
    <div className="page-form">
      <h1>Text Entry System</h1>
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
  );
}

export default PageForm; 