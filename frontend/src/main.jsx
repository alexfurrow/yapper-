import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { AuthProvider } from './context/AuthContext';
import { BrowserRouter } from 'react-router-dom';
import './index.css';

console.log("--- VITE_API_URL in main.jsx:", import.meta.env.VITE_API_URL);
console.log("--- Starting React app initialization...");

try {
  const root = ReactDOM.createRoot(document.getElementById('root'));
  console.log("--- React root created successfully");
  
  root.render(
    <React.StrictMode>
      <BrowserRouter>
        <AuthProvider>
          <App />
        </AuthProvider>
      </BrowserRouter>
    </React.StrictMode>
  );
  console.log("--- React app rendered successfully");
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