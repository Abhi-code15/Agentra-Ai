import React, { createContext, useContext, useEffect, useState } from 'react';
import api, { setAccessToken } from '../api/client';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Silently check if active refresh session exists on mount
  useEffect(() => {
    const initAuth = async () => {
      try {
        const refreshRes = await api.post('/auth/refresh');
        const token = refreshRes.data.data.access_token;
        setAccessToken(token);

        const meRes = await api.get('/auth/me');
        setUser(meRes.data.data);
      } catch (err) {
        setUser(null);
        setAccessToken(null);
      } finally {
        setLoading(false);
      }
    };

    initAuth();

    const handleExpired = () => {
      setUser(null);
      setAccessToken(null);
    };
    window.addEventListener('auth:expired', handleExpired);
    return () => window.removeEventListener('auth:expired', handleExpired);
  }, []);

  const login = async (email, password) => {
    const res = await api.post('/auth/login', { email, password });
    const { access_token, user: userData } = res.data.data;
    setAccessToken(access_token);
    setUser(userData);
    return userData;
  };

  const register = async (email, full_name, password, role = 'USER') => {
    await api.post('/auth/register', { email, full_name, password, role });
    // Immediately log in upon successful registration
    return login(email, password);
  };

  const logout = async () => {
    try {
      await api.post('/auth/logout');
    } finally {
      setAccessToken(null);
      setUser(null);
    }
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
