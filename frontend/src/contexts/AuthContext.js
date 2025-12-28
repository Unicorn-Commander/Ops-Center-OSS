import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext();

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Fetch user info from API
  const fetchUserInfo = async () => {
    try {
      const response = await fetch('/api/v1/auth/me', {
        credentials: 'include'
      });

      if (response.ok) {
        const userData = await response.json();

        // Store in both state and localStorage for Layout component
        setUser(userData);
        localStorage.setItem('userInfo', JSON.stringify(userData));

        return userData;
      } else {
        // Not authenticated
        setUser(null);
        localStorage.removeItem('userInfo');
        return null;
      }
    } catch (error) {
      console.error('Failed to fetch user info:', error);
      setUser(null);
      localStorage.removeItem('userInfo');
      return null;
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Fetch user info on mount
    fetchUserInfo();
  }, []);

  const login = async (token) => {
    // After login, fetch user info
    const userData = await fetchUserInfo();
    if (token) {
      localStorage.setItem('adminToken', token);
    }
    return userData;
  };

  const logout = () => {
    localStorage.removeItem('adminToken');
    localStorage.removeItem('userInfo');
    setUser(null);
    window.location.href = '/auth/logout';
  };

  const value = {
    user,
    loading,
    login,
    logout,
    fetchUserInfo
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};