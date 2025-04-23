import React, { createContext, useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

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
        console.log("Initialized auth from localStorage with token:", token.substring(0, 15) + "...");
      } catch (e) {
        console.error("Error parsing user from localStorage:", e);
        localStorage.removeItem('user');
        localStorage.removeItem('token');
      }
    }
    
    setLoading(false);
  }, []);

  // Add request/response interceptors
  useEffect(() => {
    const requestInterceptor = axios.interceptors.request.use(
      config => {
        console.log('Request:', config.url, config.headers);
        return config;
      },
      error => {
        console.error('Request error:', error);
        return Promise.reject(error);
      }
    );
    
    const responseInterceptor = axios.interceptors.response.use(
      response => {
        console.log('Response:', response.status, response.data);
        return response;
      },
      error => {
        console.error('Response error:', error.response?.status, error.response?.data);
        return Promise.reject(error);
      }
    );
    
    return () => {
      axios.interceptors.request.eject(requestInterceptor);
      axios.interceptors.response.eject(responseInterceptor);
    };
  }, []);

  // Login function
  const login = useCallback(async (username, password) => {
    try {
      setError(null);
      const response = await axios.post(`${API_URL}/api/auth/login`, {
        username,
        password
      });
      
      const { token, username: user, user_id } = response.data;
      
      console.log("Login successful, received token:", token.substring(0, 15) + "...");
      
      // Store token and user info
      localStorage.setItem('token', token);
      localStorage.setItem('user', JSON.stringify({ username, id: user_id }));
      
      // Set default Authorization header for all requests
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      console.log("Set default Authorization header");
      
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
      
      if (!response.data.success) {
        throw new Error(response.data.message || 'Registration failed');
      }
      
      // Auto login after registration
      return await login(username, password);
    } catch (err) {
      const errorMsg = err.response?.data?.message || 'Registration failed';
      console.error("Registration error:", errorMsg);
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
    console.log("User logged out");
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