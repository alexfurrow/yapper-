import React, { createContext, useState, useEffect, useCallback } from 'react';
import { supabase } from './supabase.js';

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

  // Initialize auth state from Supabase session
  useEffect(() => {
    const getInitialSession = async () => {
      try {
        const { data: { session } } = await supabase.auth.getSession();
        if (session) {
          setCurrentUser({
            id: session.user.id,
            email: session.user.email,
            username: session.user.user_metadata?.username || session.user.email
          });
        }
      } catch (error) {
        console.error('Error getting initial session:', error);
      } finally {
        setLoading(false);
      }
    };

    getInitialSession();

    // Listen for auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        if (session) {
          setCurrentUser({
            id: session.user.id,
            email: session.user.email,
            username: session.user.user_metadata?.username || session.user.email
          });
        } else {
          setCurrentUser(null);
        }
        setLoading(false);
      }
    );

    return () => subscription.unsubscribe();
  }, []);

  // Login function
  const login = useCallback(async (email, password) => {
    try {
      setError(null);
      console.log('Starting login with:', { email, password: '***' });
      
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password
      });
      
      console.log('Supabase login response:', { data, error });
      
      if (error) {
        console.error('Supabase login error:', error);
        setError(error.message);
        return false;
      }
      
      if (data.user) {
        console.log('Login successful, setting user:', data.user);
        setCurrentUser({
          id: data.user.id,
          email: data.user.email,
          username: data.user.user_metadata?.username || data.user.email
        });
        return true;
      }
      
      return false;
    } catch (err) {
      const errorMsg = err.message || 'Login failed';
      console.error("Login error:", errorMsg);
      setError(errorMsg);
      return false;
    }
  }, []);

  // Register function
  const register = useCallback(async (username, email, password) => {
    try {
      setError(null);
      console.log('Starting registration with:', { username, email, password: '***' });
      
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: {
            username: username
          }
        }
      });
      
      console.log('Supabase response:', { data, error });
      
      if (error) {
        console.error('Supabase registration error:', error);
        setError(error.message);
        return false;
      }
      
      if (data.user) {
        console.log('Registration successful, attempting auto-login...');
        // Auto login after successful registration
        return await login(email, password);
      }
      
      return false;
    } catch (err) {
      const errorMsg = err.message || 'Registration failed';
      console.error("Registration error:", errorMsg);
      setError(errorMsg);
      return false;
    }
  }, [login]);

  // Logout function
  const logout = useCallback(async () => {
    try {
      const { error } = await supabase.auth.signOut();
      if (error) {
        console.error('Logout error:', error);
      }
    } catch (err) {
      console.error('Logout error:', err);
    } finally {
      setCurrentUser(null);
    }
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