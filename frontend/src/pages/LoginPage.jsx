import { useState } from 'react';
import { useNavigate, Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './LoginPage.css';

function LoginPage() {
  const { isAuthenticated, login, enterDemo } = useAuth();
  const navigate = useNavigate();
  const [apiKey, setApiKey] = useState('');
  const [error, setError] = useState('');

  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  const [loading, setLoading] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    const key = apiKey.trim();
    if (!key) {
      setError('Please enter an API key');
      return;
    }

    setLoading(true);
    try {
      const API_BASE_URL = import.meta.env.VITE_API_URL;
      const response = await fetch(`${API_BASE_URL}/transactions?limit=1`, {
        headers: { 'X-API-Key': key },
      });
      if (response.status === 401) {
        setError('Invalid API key');
        return;
      }
      login(key);
      navigate('/');
    } catch {
      setError('Cannot reach the server');
    } finally {
      setLoading(false);
    }
  }

  function handleDemo() {
    enterDemo();
    navigate('/');
  }

  return (
    <div className="login-container">
      <div className="login-card">
        <h1 className="login-title">ETF Portfolio Tracker</h1>
        <form onSubmit={handleSubmit} className="login-form">
          <div className="login-field">
            <label htmlFor="apiKey">API Key</label>
            <input
              id="apiKey"
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="Enter your API key"
              autoFocus
            />
          </div>
          {error && <p className="login-error">{error}</p>}
          <button type="submit" className="login-button" disabled={loading}>
            {loading ? 'Verifying...' : 'Login'}
          </button>
        </form>
        <div className="login-demo">
          <button type="button" onClick={handleDemo} className="demo-button">
            Try Demo
          </button>
          <p className="demo-hint">Explore the app with sample data — no key required</p>
        </div>
      </div>
    </div>
  );
}

export default LoginPage;
