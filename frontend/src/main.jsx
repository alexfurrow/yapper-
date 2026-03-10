import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { AuthProvider } from './context/AuthContext';
import { BrowserRouter } from 'react-router-dom';
import './index.css';

try {
  const root = ReactDOM.createRoot(document.getElementById('root'));
  
  root.render(
    <React.StrictMode>
      <BrowserRouter>
        <AuthProvider>
          <App />
        </AuthProvider>
      </BrowserRouter>
    </React.StrictMode>
  );
} catch (error) {
  console.error("--- ERROR during React app initialization:", error);
  document.body.innerHTML = `
    <div style="padding: 20px; text-align: center;">
      <h2>Failed to load application</h2>
      <p>Error: ${error.message}</p>
      <button onclick="window.location.reload()">Reload Page</button>
    </div>
  `;
}