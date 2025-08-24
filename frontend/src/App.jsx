import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Login from './components/Login';
import Register from './components/Register';
import JournalEntryForm from './components/JournalEntryForm';
import ChatInterface from './components/ChatInterface';
import Header from './components/Header';
import SharedLayout from './components/SharedLayout';
import './App.css';

function App() {
  useEffect(() => {
    const token = localStorage.getItem('token');
    console.log("App.jsx - Stored token:", token);
    console.log("App.jsx - VITE_API_URL:", import.meta.env.VITE_API_URL);
    console.log("App.jsx - Environment:", import.meta.env.MODE);
  }, []);

  return (
    <AuthProvider>
      <Router>
        <div className="App">
          <Header />
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/" element={
              <ProtectedRoute>
                <SharedLayout>
                  <JournalEntryForm />
                </SharedLayout>
              </ProtectedRoute>
            } />
            <Route path="/chat" element={
              <ProtectedRoute>
                <SharedLayout>
                  <ChatInterface />
                </SharedLayout>
              </ProtectedRoute>
            } />
            <Route path="*" element={<Navigate to="/" />} />
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App; 