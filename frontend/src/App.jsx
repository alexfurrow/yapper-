import React, { useEffect, useState, useContext } from 'react';
// import { createHashRouter, RouterProvider } from 'react-router-dom';
import { AuthProvider, AuthContext } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Login from './components/Login';
import Register from './components/Register';
import JournalEntryForm from './components/JournalEntryForm';
import ChatInterface from './components/ChatInterface';
import Header from './components/Header';
import SharedLayout from './components/SharedLayout';
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

// Custom router component with navigation context
export const NavigationContext = React.createContext();

function CustomRouter() {
  const [currentPath, setCurrentPath] = useState(window.location.pathname);
  const { currentUser } = useContext(AuthContext);

  useEffect(() => {
    const handlePopState = () => {
      setCurrentPath(window.location.pathname);
    };

    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const navigate = (path) => {
    window.history.pushState({}, '', path);
    setCurrentPath(path);
  };

  // Route matching logic
  if (currentPath === '/login') {
    return (
      <NavigationContext.Provider value={{ navigate }}>
        <div className="App">
          <Login />
        </div>
      </NavigationContext.Provider>
    );
  }

  if (currentPath === '/register') {
    return (
      <NavigationContext.Provider value={{ navigate }}>
        <div className="App">
          <Register />
        </div>
      </NavigationContext.Provider>
    );
  }

  if (currentPath === '/chat') {
    return (
      <NavigationContext.Provider value={{ navigate }}>
        <div className="App">
          <Header />
          <ProtectedRoute>
            <SharedLayout>
              <ChatInterface />
            </SharedLayout>
          </ProtectedRoute>
        </div>
      </NavigationContext.Provider>
    );
  }

  if (currentPath === '/') {
    return (
      <NavigationContext.Provider value={{ navigate }}>
        <div className="App">
          <Header />
          <ProtectedRoute>
            <SharedLayout>
              <JournalEntryForm />
            </SharedLayout>
          </ProtectedRoute>
        </div>
      </NavigationContext.Provider>
    );
  }

  // 404 page
  return (
    <NavigationContext.Provider value={{ navigate }}>
      <div className="App">
        <h1>404 - Page Not Found</h1>
        <p>Path: {currentPath}</p>
        <button onClick={() => navigate('/')}>Go Home</button>
      </div>
    </NavigationContext.Provider>
  );
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
      <AuthProvider>
        <CustomRouter />
      </AuthProvider>
    </ErrorBoundary>
  );
}

export default App; 