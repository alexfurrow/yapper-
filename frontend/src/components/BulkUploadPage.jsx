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
  
  // Excel + Audio upload state
  const [excelFile, setExcelFile] = useState(null);
  const [audioFiles, setAudioFiles] = useState([]);
  const [isExcelDragOver, setIsExcelDragOver] = useState(false);
  const [isAudioDragOver, setIsAudioDragOver] = useState(false);
  const excelInputRef = useRef(null);
  const audioInputRef = useRef(null);
  const [uploadMode, setUploadMode] = useState('standard'); // 'standard' or 'excel-audio'

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
      file.name.toLowerCase().endsWith('.docx') ||
      file.name.toLowerCase().endsWith('.m4a')
    );
    
    setFiles(prev => [...prev, ...validFiles]);
  };

  const handleFileSelect = (e) => {
    const selectedFiles = Array.from(e.target.files);
    const validFiles = selectedFiles.filter(file => 
      file.name.toLowerCase().endsWith('.txt') || 
      file.name.toLowerCase().endsWith('.doc') || 
      file.name.toLowerCase().endsWith('.docx') ||
      file.name.toLowerCase().endsWith('.m4a')
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
      const previewUrl = `${backendUrl}/api/bulk-upload/preview`;
      
      console.log('Preview request:', {
        url: previewUrl,
        fileCount: files.length,
        fileNames: files.map(f => f.name)
      });
      
      // Don't set Content-Type - browser will set it with boundary for FormData
      const response = await fetch(previewUrl, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session.access_token}`
        },
        body: formData
      });
      
      console.log('Preview response status:', response.status);
      
      if (!response.ok) {
        let errorMessage = 'Preview failed';
        try {
          const errorData = await response.json();
          errorMessage = errorData.error || errorMessage;
        } catch (e) {
          errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        }
        throw new Error(errorMessage);
      }
      
      const data = await response.json();
      console.log('Preview data received:', data);
      setPreviewData(data.preview_data);
      
    } catch (error) {
      console.error('Preview error:', error);
      console.error('Error details:', {
        message: error.message,
        stack: error.stack,
        name: error.name
      });
      alert(`Preview failed: ${error.message}`);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleCreateEntries = async () => {
    if (!files || files.length === 0) return;
    
    setIsProcessing(true);
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) throw new Error('No active session');
      
      // Send files directly (not preview data) so backend can transcribe audio files
      const formData = new FormData();
      files.forEach(file => {
        formData.append('files', file);
      });
      
      const backendUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:5002';
      // Don't set Content-Type - let browser set it with boundary for FormData
      const response = await fetch(`${backendUrl}/api/bulk-upload/create-entries`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session.access_token}`
        },
        body: formData
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
    setExcelFile(null);
    setAudioFiles([]);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
    if (excelInputRef.current) {
      excelInputRef.current.value = '';
    }
    if (audioInputRef.current) {
      audioInputRef.current.value = '';
    }
  };

  // Excel + Audio upload handlers
  const handleExcelSelect = (e) => {
    const file = e.target.files[0];
    if (file && (file.name.toLowerCase().endsWith('.xlsx') || file.name.toLowerCase().endsWith('.xls') || file.name.toLowerCase().endsWith('.csv'))) {
      setExcelFile(file);
    } else {
      alert('Please select a valid spreadsheet file (.xlsx, .xls, or .csv)');
    }
  };

  const handleExcelDrop = (e) => {
    e.preventDefault();
    setIsExcelDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file && (file.name.toLowerCase().endsWith('.xlsx') || file.name.toLowerCase().endsWith('.xls') || file.name.toLowerCase().endsWith('.csv'))) {
      setExcelFile(file);
    }
  };

  const handleAudioDrop = (e) => {
    e.preventDefault();
    setIsAudioDragOver(false);
    const droppedFiles = Array.from(e.dataTransfer.files);
    const validFiles = droppedFiles.filter(file => {
      const name = file.name.toLowerCase();
      return name.endsWith('.m4a') || name.endsWith('.txt') || name.endsWith('.doc') || name.endsWith('.docx');
    });
    setAudioFiles(prev => [...prev, ...validFiles]);
  };

  const handleAudioSelect = (e) => {
    const selectedFiles = Array.from(e.target.files);
    const validFiles = selectedFiles.filter(file => {
      const name = file.name.toLowerCase();
      return name.endsWith('.m4a') || name.endsWith('.txt') || name.endsWith('.doc') || name.endsWith('.docx');
    });
    setAudioFiles(prev => [...prev, ...validFiles]);
  };

  const removeAudioFile = (index) => {
    setAudioFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleExcelAudioUpload = async () => {
    if (!excelFile) {
      alert('Please upload an Excel spreadsheet');
      return;
    }
    if (audioFiles.length === 0) {
      alert('Please upload at least one file');
      return;
    }
    
    setIsProcessing(true);
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) throw new Error('No active session');
      
      const formData = new FormData();
      formData.append('spreadsheet', excelFile);
      audioFiles.forEach(file => {
        formData.append('files', file);
      });
      
      const backendUrl = import.meta.env.VITE_BACKEND_URL || 'http://localhost:5002';
      const response = await fetch(`${backendUrl}/api/bulk-upload/excel-files`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session.access_token}`
        },
        body: formData
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Upload failed');
      }
      
      const data = await response.json();
      setResults(data);
      
    } catch (error) {
      console.error('Excel-files upload error:', error);
      console.error('Error details:', {
        message: error.message,
        stack: error.stack,
        name: error.name
      });
      alert(`Upload failed: ${error.message}`);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="bulk-upload-page">
      <div className="bulk-upload-container">
        <div className="bulk-upload-header">
          <h1>Upload Your Past Journal</h1>
          <p>Upload multiple text or audio files to create journal entries in bulk. The system will automatically detect dates from filenames, metadata, or content. Audio files (.m4a) will be transcribed automatically.</p>
          
          <div style={{ marginTop: '20px', display: 'flex', gap: '10px' }}>
            <button 
              onClick={() => setUploadMode('standard')}
              style={{ 
                padding: '8px 16px', 
                backgroundColor: uploadMode === 'standard' ? '#007bff' : '#6c757d',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              Standard Upload
            </button>
            <button 
              onClick={() => setUploadMode('excel-audio')}
              style={{ 
                padding: '8px 16px', 
                backgroundColor: uploadMode === 'excel-audio' ? '#007bff' : '#6c757d',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              Excel + Files Upload
            </button>
          </div>
        </div>

        {!previewData && !results && uploadMode === 'standard' && (
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
                <p className="supported-formats">Supported: .txt, .doc, .docx, .m4a</p>
              </div>
            </div>

            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept=".txt,.doc,.docx,.m4a"
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

        {!previewData && !results && uploadMode === 'excel-audio' && (
          <div className="upload-section">
            <div style={{ marginBottom: '30px' }}>
              <h3>Step 1: Upload Spreadsheet</h3>
              <p style={{ fontSize: '14px', color: '#666', marginBottom: '10px' }}>
                Upload a spreadsheet file (.xlsx, .xls, or .csv) with two columns:
                <br />Column 1: File names (e.g., "New Recording 23")
                <br />Column 2: Date Created (e.g., "Jun 4 2024" or "June 4 2024")
              </p>
              <div 
                className={`drop-zone ${isExcelDragOver ? 'drag-over' : ''}`}
                onDragOver={(e) => { e.preventDefault(); setIsExcelDragOver(true); }}
                onDragLeave={(e) => { e.preventDefault(); setIsExcelDragOver(false); }}
                onDrop={handleExcelDrop}
                style={{ minHeight: '150px' }}
              >
                <div className="drop-zone-content">
                  <div className="drop-icon">📊</div>
                  <h3>Drop Excel file here</h3>
                  <p>or</p>
                  <button 
                    className="select-files-btn"
                    onClick={() => excelInputRef.current?.click()}
                  >
                    Select Excel File
                  </button>
                  <p className="supported-formats">Supported: .xlsx, .xls, .csv</p>
                </div>
              </div>
              <input
                ref={excelInputRef}
                type="file"
                accept=".xlsx,.xls,.csv"
                onChange={handleExcelSelect}
                style={{ display: 'none' }}
              />
              {excelFile && (
                <div style={{ marginTop: '10px', padding: '10px', backgroundColor: '#f0f0f0', borderRadius: '4px' }}>
                  <strong>Selected:</strong> {excelFile.name}
                  <button 
                    onClick={() => setExcelFile(null)}
                    style={{ marginLeft: '10px', padding: '4px 8px', backgroundColor: '#dc3545', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
                  >
                    Remove
                  </button>
                </div>
              )}
            </div>

            <div style={{ marginBottom: '30px' }}>
              <h3>Step 2: Upload Files</h3>
              <p style={{ fontSize: '14px', color: '#666', marginBottom: '10px' }}>
                Upload files (.m4a, .txt, .doc, .docx) that match the filenames in your spreadsheet.
                The number of files must match the number of rows in your spreadsheet.
                Audio files (.m4a) will be transcribed automatically.
              </p>
              <div 
                className={`drop-zone ${isAudioDragOver ? 'drag-over' : ''}`}
                onDragOver={(e) => { e.preventDefault(); setIsAudioDragOver(true); }}
                onDragLeave={(e) => { e.preventDefault(); setIsAudioDragOver(false); }}
                onDrop={handleAudioDrop}
                style={{ minHeight: '150px' }}
              >
                <div className="drop-zone-content">
                  <div className="drop-icon">📄</div>
                  <h3>Drop files here</h3>
                  <p>or</p>
                  <button 
                    className="select-files-btn"
                    onClick={() => audioInputRef.current?.click()}
                  >
                    Select Files
                  </button>
                  <p className="supported-formats">Supported: .m4a, .txt, .doc, .docx</p>
                </div>
              </div>
              <input
                ref={audioInputRef}
                type="file"
                multiple
                accept=".m4a,.txt,.doc,.docx"
                onChange={handleAudioSelect}
                style={{ display: 'none' }}
              />
              {audioFiles.length > 0 && (
                <div style={{ marginTop: '10px' }}>
                  <h4>Selected Files ({audioFiles.length})</h4>
                  <div className="files-list">
                    {audioFiles.map((file, index) => (
                      <div key={index} className="file-item">
                        <span className="file-name">{file.name}</span>
                        <span className="file-size">({(file.size / 1024).toFixed(1)} KB)</span>
                        <button 
                          className="remove-file-btn"
                          onClick={() => removeAudioFile(index)}
                        >
                          ✕
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div style={{ textAlign: 'center', marginTop: '30px' }}>
              <button 
                className="create-entries-btn"
                onClick={handleExcelAudioUpload}
                disabled={isProcessing || !excelFile || audioFiles.length === 0}
                style={{ 
                  padding: '12px 24px', 
                  fontSize: '16px',
                  backgroundColor: (!excelFile || audioFiles.length === 0) ? '#ccc' : '#28a745',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: (!excelFile || audioFiles.length === 0) ? 'not-allowed' : 'pointer'
                }}
              >
                {isProcessing ? 'Processing...' : `Upload ${audioFiles.length} Files with Excel Mapping`}
              </button>
            </div>
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
                    <h4>{entry.title || `Entry #${index + 1}`}</h4>
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
                    {entry.title || `Entry #${entry.user_entry_id || index + 1}`} (from {entry.filename})
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
