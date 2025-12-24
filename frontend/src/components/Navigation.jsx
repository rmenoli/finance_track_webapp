import { NavLink } from 'react-router-dom';
import './Navigation.css';

function Navigation() {
  return (
    <nav className="navigation">
      <div className="nav-container">
        <div className="nav-brand">
          <h1>NW Tracker</h1>
        </div>
        <ul className="nav-menu">
          <li>
            <NavLink to="/" className={({ isActive }) => isActive ? 'active' : ''}>
              Investment Dashboard
            </NavLink>
          </li>
          <li>
            <NavLink to="/transactions" className={({ isActive }) => isActive ? 'active' : ''}>
              Transactions
            </NavLink>
          </li>
          <li>
            <NavLink to="/isin-metadata" className={({ isActive }) => isActive ? 'active' : ''}>
              ISIN Metadata
            </NavLink>
          </li>
          <li>
            <NavLink to="/other-assets" className={({ isActive }) => isActive ? 'active' : ''}>
              Other Assets
            </NavLink>
          </li>
          <li>
            <NavLink to="/snapshots" className={({ isActive }) => isActive ? 'active' : ''}>
              Snapshots
            </NavLink>
          </li>
        </ul>
      </div>
    </nav>
  );
}

export default Navigation;
