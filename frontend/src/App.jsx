import React, { useEffect } from 'react';
// import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
// import { AuthProvider } from './context/AuthContext';
// import ProtectedRoute from './components/ProtectedRoute';
// import Login from './components/Login';
// import Register from './components/Register';
// import JournalEntryForm from './components/JournalEntryForm';
// import ChatInterface from './components/ChatInterface';
// import Header from './components/Header';
// import SharedLayout from './components/SharedLayout';
import './App.css';

// Simple error boundary component
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error caught by boundary:', error);
    console.error('Error info:', errorInfo);
    console.error('Component stack:', errorInfo.componentStack);
    console.error('Error name:', error.name);
    console.error('Error message:', error.message);
    console.error('Error stack:', error.stack);
    this.setState({ errorInfo });
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '20px', textAlign: 'center', fontFamily: 'Arial, sans-serif' }}>
          <h2>Something went wrong.</h2>
          <p><strong>Error:</strong> {this.state.error?.message || 'Unknown error'}</p>
          <p><strong>Error Name:</strong> {this.state.error?.name || 'Unknown'}</p>
          {this.state.errorInfo && (
            <details style={{ marginTop: '20px', textAlign: 'left' }}>
              <summary>Component Stack Trace</summary>
              <pre style={{ 
                background: '#f5f5f5', 
                padding: '10px', 
                overflow: 'auto', 
                fontSize: '12px',
                whiteSpace: 'pre-wrap'
              }}>
                {this.state.errorInfo.componentStack}
              </pre>
            </details>
          )}
          {this.state.error?.stack && (
            <details style={{ marginTop: '20px', textAlign: 'left' }}>
              <summary>Error Stack Trace</summary>
              <pre style={{ 
                background: '#f5f5f5', 
                padding: '10px', 
                overflow: 'auto', 
                fontSize: '12px',
                whiteSpace: 'pre-wrap'
              }}>
                {this.state.error.stack}
              </pre>
            </details>
          )}
          <button 
            onClick={() => window.location.reload()} 
            style={{
              marginTop: '20px',
              padding: '10px 20px',
              backgroundColor: '#007bff',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Reload Page
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

function App() {
  useEffect(() => {
    const token = localStorage.getItem('token');
    console.log("App.jsx - Stored token:", token);
    console.log("App.jsx - VITE_API_URL:", import.meta.env.VITE_API_URL);
    console.log("App.jsx - Environment:", import.meta.env.MODE);
  }, []);

  console.log("App.jsx - About to render components");

  return (
    <ErrorBoundary>
      <div className="App">
        <h1>Minimal React App</h1>
        <p>If you can see this, React is working without any external dependencies.</p>
        <p>Environment: {import.meta.env.MODE}</p>
        <p>API URL: {import.meta.env.VITE_API_URL}</p>
      </div>
    </ErrorBoundary>
  );
}

export default App; 