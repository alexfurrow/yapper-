import React, { createContext, useState, useEffect, useCallback } from 'react';
import axios from 'axios';

// This correctly reads the Vercel environment variable in production builds
let API_URL = import.meta.env.VITE_API_URL;

// Ensure API_URL has proper protocol
if (API_URL && !API_URL.startsWith('http://') && !API_URL.startsWith('https://')) {
  API_URL = `https://${API_URL}`;
}

// Check if API_URL is set in production
if (!API_URL && import.meta.env.MODE === 'production') {
  console.error("CRITICAL ERROR: VITE_API_URL is not set in production environment!");
}

// Ensure axios calls use this base URL or prepend it
// Option 1: Set Axios base URL (Good practice)
if (API_URL) {
  axios.defaults.baseURL = API_URL;
} else {
  console.warn("API_URL not set, axios requests may fail");
}

// Create the context with a default value
const AuthContext = createContext({
  currentUser: null,
  login: async () => false,
  register: async () => false,
  logout: () => {},
  loading: true,
  error: null
});

// Separate named export for the provider component
function AuthProvider({ children }) {
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Initialize auth state from localStorage
  useEffect(() => {
    const token = localStorage.getItem('token');
    const user = localStorage.getItem('user');
    
    if (token && user) {
      try {
        setCurrentUser(JSON.parse(user));
        // Set default Authorization header for all requests
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      } catch (e) {
        console.error("Error parsing user from localStorage:", e);
        localStorage.removeItem('user');
        localStorage.removeItem('token');
      }
    }
    
    setLoading(false);
  }, []);

  // Login function
  const login = useCallback(async (username, password) => {
    try {
      setError(null);
      
      if (!API_URL) {
        const errorMsg = 'API URL not configured. Please check environment variables.';
        console.error(errorMsg);
        setError(errorMsg);
        return false;
      }
      
      const response = await axios.post('/api/auth/login', {
        username,
        password
      });
      
      const { token, username: user, user_id } = response.data;
      
      // Store token and user info
      localStorage.setItem('token', token);
      localStorage.setItem('user', JSON.stringify({ username, id: user_id }));
      
      // Set default Authorization header for all requests
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      
      setCurrentUser({ username, id: user_id });
      return true;
    } catch (err) {
      const errorMsg = err.response?.data?.message || 'Login failed';
      console.error("Login error:", errorMsg);
      setError(errorMsg);
      return false;
    }
  }, []);

  // Register function
  const register = useCallback(async (username, password) => {
    try {
      setError(null);
      const response = await axios.post('/api/auth/register', {
        username,
        password
      });

      // Check if backend indicated success (adjust if needed)
      // Assuming 201 means success for registration API itself
      if (response.status !== 201) {
         throw new Error(response.data.message || 'Registration API call failed');
      }

      // Auto login after registration - THIS PART IS FAILING
      return await login(username, password);
    } catch (err) {
      // This catch block is triggered because the login() call fails
      const errorMsg = err.response?.data?.message || 'Registration failed (likely during auto-login)';
      console.error("Registration error:", errorMsg, err); // Log the actual error
      setError(errorMsg);
      return false;
    }
  }, [login]);

  // Logout function
  const logout = useCallback(() => {
    // Remove token and user info
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    
    // Remove Authorization header
    delete axios.defaults.headers.common['Authorization'];
    
    setCurrentUser(null);
  }, []);

  // Create the context value object
  const contextValue = {
    currentUser,
    login,
    register,
    logout,
    loading,
    error
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
}

// Export both the context and provider
export { AuthContext, AuthProvider }; 