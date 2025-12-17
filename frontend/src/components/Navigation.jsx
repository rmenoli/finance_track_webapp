import { NavLink } from 'react-router-dom';
import './Navigation.css';

function Navigation() {
  return (
    <nav className="navigation">
      <div className="nav-container">
        <div className="nav-brand">
          <h1>ETF Portfolio Tracker</h1>
        </div>
        <ul className="nav-menu">
          <li>
            <NavLink to="/" className={({ isActive }) => isActive ? 'active' : ''}>
              Dashboard
            </NavLink>
          </li>
          <li>
            <NavLink to="/transactions" className={({ isActive }) => isActive ? 'active' : ''}>
              Transactions
            </NavLink>
          </li>
          <li>
            <NavLink to="/holdings" className={({ isActive }) => isActive ? 'active' : ''}>
              Holdings
            </NavLink>
          </li>
          <li>
            <NavLink to="/analytics" className={({ isActive }) => isActive ? 'active' : ''}>
              Analytics
            </NavLink>
          </li>
        </ul>
      </div>
    </nav>
  );
}

export default Navigation;
