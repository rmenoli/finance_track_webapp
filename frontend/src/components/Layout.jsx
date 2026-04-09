import { Outlet, Link } from 'react-router-dom';
import Navigation from './Navigation';
import { useAuth } from '../context/AuthContext';
import './Layout.css';

function Layout() {
  const { isDemoMode, logout } = useAuth();

  return (
    <div className="layout">
      {isDemoMode && (
        <div className="demo-banner">
          Demo mode — data is not real.{' '}
          <Link to="/login" onClick={logout} className="demo-banner-link">
            Login
          </Link>{' '}
          to use your real portfolio.
        </div>
      )}
      <Navigation />
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}

export default Layout;
