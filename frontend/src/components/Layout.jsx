import { Outlet } from 'react-router-dom';
import Navigation from './Navigation';
import './Layout.css';

function Layout() {
  return (
    <div className="layout">
      <Navigation />
      <main className="main-content">
        <Outlet />
      </main>
    </div>
  );
}

export default Layout;
