import { createContext, useContext, useState } from 'react';

const AuthContext = createContext(null);

const DEMO_API_KEY = import.meta.env.VITE_DEMO_API_KEY;

export function AuthProvider({ children }) {
  const [apiKey, setApiKey] = useState(() => localStorage.getItem('api_key'));

  const isAuthenticated = apiKey !== null;
  const isDemoMode = apiKey === DEMO_API_KEY;

  function login(key) {
    localStorage.setItem('api_key', key);
    setApiKey(key);
  }

  function enterDemo() {
    localStorage.setItem('api_key', DEMO_API_KEY);
    setApiKey(DEMO_API_KEY);
  }

  function logout() {
    localStorage.removeItem('api_key');
    setApiKey(null);
  }

  return (
    <AuthContext.Provider value={{ isAuthenticated, isDemoMode, login, enterDemo, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
