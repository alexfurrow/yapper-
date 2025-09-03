import React, { createContext, useState, useEffect, useCallback } from 'react';
import { supabase } from './supabase.js';
import { useNavigate } from 'react-router-dom';

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
  const navigate = useNavigate();

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
  const register = async (username, email, password) => {
    try {
      setLoading(true);
      setError(null);
      
      console.log('Starting registration with:', { username, email, password: '***' });
      
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: { username }
        }
      });

      if (error) {
        console.error('Supabase registration error:', error);
        console.log('Error message:', error.message);
        console.log('Full error object:', error);
        
        // Handle specific error cases with user-friendly messages
        if (error.message.includes('already registered') || 
            error.message.includes('already exists') ||
            error.message.includes('duplicate') ||
            error.message.includes('User already registered') ||
            error.message.includes('already been registered') ||
            error.message.includes('already associated')) {
          setError('There already is an account associated with this email address');
        } else if (error.message.includes('Invalid email')) {
          setError('Please enter a valid email address.');
        } else if (error.message.includes('Password')) {
          setError('Password does not meet requirements. Please ensure it has at least 8 characters.');
        } else {
          setError(error.message);
        }
        return;
      }

      if (data.user) {
        console.log('Registration successful, user data:', data.user);
        
        // Check if email is confirmed
        if (data.user.email_confirmed_at) {
          // Email is confirmed, proceed with auto-login
          setCurrentUser(data.user);
          setLoading(false);
          navigate('/');
        } else {
          // Email not confirmed, show message to user
          setError('Registration successful! Please check your email and click the verification link to confirm your account before logging in.');
          setLoading(false);
        }
      }
    } catch (error) {
      console.error('Registration error:', error);
      setError('Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

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