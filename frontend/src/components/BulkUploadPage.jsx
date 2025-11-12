import React, { useState, useRef } from 'react';
import { supabase } from '../context/supabase';
import './BulkUploadPage.css';

const BulkUploadPage = () => {
  const [files, setFiles] = useState([]);
  const [isDragOver, setIsDragOver] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [previewData, setPreviewData] = useState(null);
  const [results, setResults] = useState(null);
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const droppedFiles = Array.from(e.dataTransfer.files);
    const validFiles = droppedFiles.filter(file => 
      file.name.toLowerCase().endsWith('.txt') || 
      file.name.toLowerCase().endsWith('.doc') || 
      file.name.toLowerCase().endsWith('.docx')
    );
    
    setFiles(prev => [...prev, ...validFiles]);
  };

  const handleFileSelect = (e) => {
    const selectedFiles = Array.from(e.target.files);
    const validFiles = selectedFiles.filter(file => 
      file.name.toLowerCase().endsWith('.txt') || 
      file.name.toLowerCase().endsWith('.doc') || 
      file.name.toLowerCase().endsWith('.docx')
    );
    
    setFiles(prev => [...prev, ...validFiles]);
  };

  const removeFile = (index) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handlePreview = async () => {
    if (files.length === 0) return;
    
    setIsProcessing(true);
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) throw new Error('No active session');
      
      const formData = new FormData();
      files.forEach(file => formData.append('files', file));
      
      const backendUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:5002';
      const response = await fetch(`${backendUrl}/api/bulk-upload/preview`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session.access_token}`
        },
        body: formData
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Preview failed');
      }
      
      const data = await response.json();
      setPreviewData(data.preview_data);
      
    } catch (error) {
      console.error('Preview error:', error);
      alert(`Preview failed: ${error.message}`);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleCreateEntries = async () => {
    if (!previewData || previewData.successful.length === 0) return;
    
    setIsProcessing(true);
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) throw new Error('No active session');
      
      const backendUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:5002';
      const response = await fetch(`${backendUrl}/api/bulk-upload/create-entries`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`
        },
        body: JSON.stringify({
          entries: previewData.successful
        })
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Creation failed');
      }
      
      const data = await response.json();
      setResults(data);
      
    } catch (error) {
      console.error('Creation error:', error);
      alert(`Creation failed: ${error.message}`);
    } finally {
      setIsProcessing(false);
    }
  };

  const resetUpload = () => {
    setFiles([]);
    setPreviewData(null);
    setResults(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="bulk-upload-page">
      <div className="bulk-upload-container">
        <div className="bulk-upload-header">
          <h1>Upload Your Past Journal</h1>
          <p>Upload multiple text files to create journal entries in bulk. The system will automatically detect dates from filenames or content.</p>
        </div>

        {!previewData && !results && (
          <div className="upload-section">
            <div 
              className={`drop-zone ${isDragOver ? 'drag-over' : ''}`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              <div className="drop-zone-content">
                <div className="drop-icon">📁</div>
                <h3>Drop files here</h3>
                <p>or</p>
                <button 
                  className="select-files-btn"
                  onClick={() => fileInputRef.current?.click()}
                >
                  Select Files
                </button>
                <p className="supported-formats">Supported: .txt, .doc, .docx</p>
              </div>
            </div>

            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".txt,.doc,.docx"
              onChange={handleFileSelect}
              style={{ display: 'none' }}
            />

            {files.length > 0 && (
              <div className="selected-files">
                <h3>Selected Files ({files.length})</h3>
                <div className="files-list">
                  {files.map((file, index) => (
                    <div key={index} className="file-item">
                      <span className="file-name">{file.name}</span>
                      <span className="file-size">({(file.size / 1024).toFixed(1)} KB)</span>
                      <button 
                        className="remove-file-btn"
                        onClick={() => removeFile(index)}
                      >
                        ✕
                      </button>
                    </div>
                  ))}
                </div>
                <button 
                  className="preview-btn"
                  onClick={handlePreview}
                  disabled={isProcessing}
                >
                  {isProcessing ? 'Processing...' : 'Preview Entries'}
                </button>
              </div>
            )}
          </div>
        )}

        {previewData && !results && (
          <div className="preview-section">
            <h2>Preview Entries</h2>
            <div className="preview-summary">
              <p>Successfully processed: {previewData.successful.length} files</p>
              <p>Failed: {previewData.failed.length} files</p>
            </div>
            
            <div className="preview-entries">
              {previewData.successful.map((entry, index) => (
                <div key={index} className="preview-entry">
                  <div className="entry-header">
                    <h4>Entry #{entry.date_string}</h4>
                    <span className="date-source">Date from: {entry.date_source}</span>
                  </div>
                  <div className="entry-content">
                    <p>{entry.content.substring(0, 200)}...</p>
                  </div>
                  <div className="entry-meta">
                    <span>File: {entry.filename}</span>
                    <span>Length: {entry.content_length} characters</span>
                  </div>
                </div>
              ))}
            </div>

            {previewData.failed.length > 0 && (
              <div className="failed-entries">
                <h3>Failed to Process</h3>
                {previewData.failed.map((entry, index) => (
                  <div key={index} className="failed-entry">
                    <strong>{entry.filename}</strong>: {entry.error}
                  </div>
                ))}
              </div>
            )}

            <div className="preview-actions">
              <button 
                className="create-entries-btn"
                onClick={handleCreateEntries}
                disabled={isProcessing || previewData.successful.length === 0}
              >
                {isProcessing ? 'Creating...' : `Create ${previewData.successful.length} Entries`}
              </button>
              <button 
                className="back-btn"
                onClick={resetUpload}
                disabled={isProcessing}
              >
                Back to Upload
              </button>
            </div>
          </div>
        )}

        {results && (
          <div className="results-section">
            <h2>Upload Complete</h2>
            <div className="results-summary">
              <p>Successfully created: {results.created_count} entries</p>
              <p>Failed: {results.failed_count} entries</p>
            </div>

            {results.created_entries.length > 0 && (
              <div className="created-entries">
                <h3>Created Entries</h3>
                {results.created_entries.map((entry, index) => (
                  <div key={index} className="created-entry">
                    {entry.title_date || entry.date_string || `Entry #${entry.user_entry_id}`} (from {entry.filename})
                  </div>
                ))}
              </div>
            )}

            {results.failed_entries.length > 0 && (
              <div className="failed-entries">
                <h3>Failed Entries</h3>
                {results.failed_entries.map((entry, index) => (
                  <div key={index} className="failed-entry">
                    {entry.filename || 'Unknown'}: {entry.error}
                  </div>
                ))}
              </div>
            )}

            <div className="results-actions">
              <button 
                className="new-upload-btn"
                onClick={resetUpload}
              >
                Upload More Files
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default BulkUploadPage;
