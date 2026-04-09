# Login Page with Demo Mode — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a login page that gates access to real portfolio data, with a "Try Demo" path that shows realistic fake data so visitors can explore the UI.

**Architecture:** Pure frontend — credentials checked client-side against Vite env vars (`VITE_APP_USERNAME` / `VITE_APP_PASSWORD`). Auth state in `localStorage`. Demo mode intercepts each API method in `api.js` and returns data from a mutable in-memory store in `mockApi.js`. No backend changes needed.

**Tech Stack:** React 18, React Router v6, Vite env vars, localStorage

---

## File Map

| Action | File | Responsibility |
|--------|------|----------------|
| Create | `frontend/src/context/AuthContext.jsx` | Auth state, login, logout, isDemoMode |
| Create | `frontend/src/pages/LoginPage.jsx` | Login form UI |
| Create | `frontend/src/pages/LoginPage.css` | Login form styles |
| Create | `frontend/src/services/mockApi.js` | Mutable in-memory store + all mock API methods |
| Modify | `frontend/src/services/api.js` | Add `isDemoMode()` routing to each API method |
| Modify | `frontend/src/App.jsx` | AuthProvider, RequireAuth wrapper, `/login` route |
| Modify | `frontend/src/components/Layout.jsx` | Demo banner |
| Modify | `frontend/.env.development` | Add empty `VITE_APP_USERNAME` / `VITE_APP_PASSWORD` |
| Modify | `frontend/.env.production` | Add placeholder vars |
| Modify | `.github/workflows/deploy.yml` | Pass new secrets to frontend build step |

---

## Task 1: Create `mockApi.js`

**File:** `frontend/src/services/mockApi.js`

> Note: There is no frontend test setup in this project. Verification is manual (see Task 7).

- [ ] **Step 1: Create the file with seed data and transaction mock methods**

```javascript
// Seed data — deep-copied into store on module load, resets on page refresh
const SEED = {
  transactions: [
    { id: 1, isin: 'IE00B4L5Y983', date: '2024-02-10', type: 'BUY', units: '10.0000', price_per_unit: '85.50', fee: '1.50', broker: 'DEGIRO', total_without_fees: '855.00', total_with_fees: '856.50' },
    { id: 2, isin: 'IE00B4L5Y983', date: '2024-04-15', type: 'BUY', units: '5.0000', price_per_unit: '88.20', fee: '1.50', broker: 'DEGIRO', total_without_fees: '441.00', total_with_fees: '442.50' },
    { id: 3, isin: 'IE00B4L5Y983', date: '2024-08-20', type: 'SELL', units: '3.0000', price_per_unit: '92.00', fee: '1.50', broker: 'DEGIRO', total_without_fees: '276.00', total_with_fees: '274.50' },
    { id: 4, isin: 'IE00B4WXJJ64', date: '2024-03-05', type: 'BUY', units: '20.0000', price_per_unit: '22.80', fee: '1.50', broker: 'DEGIRO', total_without_fees: '456.00', total_with_fees: '457.50' },
    { id: 5, isin: 'IE00B4WXJJ64', date: '2024-07-12', type: 'BUY', units: '10.0000', price_per_unit: '23.50', fee: '1.50', broker: 'DEGIRO', total_without_fees: '235.00', total_with_fees: '236.50' },
    { id: 6, isin: 'US0378331005', date: '2024-01-20', type: 'BUY', units: '2.0000', price_per_unit: '182.00', fee: '2.00', broker: 'IBKR', total_without_fees: '364.00', total_with_fees: '366.00' },
    { id: 7, isin: 'US0378331005', date: '2024-06-01', type: 'BUY', units: '1.0000', price_per_unit: '195.00', fee: '2.00', broker: 'IBKR', total_without_fees: '195.00', total_with_fees: '197.00' },
    { id: 8, isin: 'US0378331005', date: '2024-09-15', type: 'SELL', units: '1.0000', price_per_unit: '210.00', fee: '2.00', broker: 'IBKR', total_without_fees: '210.00', total_with_fees: '208.00' },
  ],
  isinMetadata: [
    { isin: 'IE00B4L5Y983', name: 'iShares Core MSCI World UCITS ETF', type: 'STOCK' },
    { isin: 'IE00B4WXJJ64', name: 'iShares Physical Gold ETC', type: 'BOND' },
    { isin: 'US0378331005', name: 'Apple Inc.', type: 'STOCK' },
  ],
  positionValues: [
    { isin: 'IE00B4L5Y983', current_value: '1120.00' },
    { isin: 'IE00B4WXJJ64', current_value: '720.00' },
    { isin: 'US0378331005', current_value: '420.00' },
  ],
  otherAssets: [
    { asset_type: 'CASH', asset_detail: 'ING Savings', currency: 'EUR', value: '5000.00' },
    { asset_type: 'CD', asset_detail: 'Sporitelna 12m', currency: 'CZK', value: '100000.00' },
  ],
  settings: {
    exchange_rate: '25.50',
    expected_return_investment: '7.00',
    expected_return_cd: '4.00',
  },
  snapshots: [
    { snapshot_date: '2024-02-01T10:00:00', asset_type: 'INVESTMENT', asset_detail: 'IE00B4L5Y983', currency: 'EUR', value: '856.50', exchange_rate: '25.20', value_eur: '856.50' },
    { snapshot_date: '2024-03-01T10:00:00', asset_type: 'INVESTMENT', asset_detail: 'IE00B4L5Y983', currency: 'EUR', value: '900.00', exchange_rate: '25.30', value_eur: '900.00' },
    { snapshot_date: '2024-04-01T10:00:00', asset_type: 'INVESTMENT', asset_detail: 'IE00B4L5Y983', currency: 'EUR', value: '1100.00', exchange_rate: '25.40', value_eur: '1100.00' },
    { snapshot_date: '2024-05-01T10:00:00', asset_type: 'INVESTMENT', asset_detail: 'IE00B4L5Y983', currency: 'EUR', value: '1050.00', exchange_rate: '25.50', value_eur: '1050.00' },
    { snapshot_date: '2024-06-01T10:00:00', asset_type: 'INVESTMENT', asset_detail: 'IE00B4L5Y983', currency: 'EUR', value: '1150.00', exchange_rate: '25.45', value_eur: '1150.00' },
    { snapshot_date: '2024-07-01T10:00:00', asset_type: 'INVESTMENT', asset_detail: 'IE00B4L5Y983', currency: 'EUR', value: '1200.00', exchange_rate: '25.50', value_eur: '1200.00' },
  ],
};

// Deep copy so mutations don't affect the seed
let store = JSON.parse(JSON.stringify(SEED));
let nextId = 100;

// --- Transactions ---
export const mockTransactionsAPI = {
  getAll: (_params = {}) => Promise.resolve([...store.transactions]),
  getById: (id) => Promise.resolve(store.transactions.find((t) => t.id === Number(id)) ?? null),
  create: (data) => {
    const created = { id: nextId++, ...data };
    store.transactions.push(created);
    return Promise.resolve(created);
  },
  update: (id, data) => {
    const idx = store.transactions.findIndex((t) => t.id === Number(id));
    if (idx === -1) return Promise.reject(new Error('Not found'));
    store.transactions[idx] = { ...store.transactions[idx], ...data };
    return Promise.resolve(store.transactions[idx]);
  },
  delete: (id) => {
    store.transactions = store.transactions.filter((t) => t.id !== Number(id));
    return Promise.resolve(null);
  },
  importCSV: (_file) =>
    Promise.resolve({ imported: 3, errors: [], message: 'Demo mode: 3 rows imported (not persisted)' }),
};
```

- [ ] **Step 2: Add remaining mock API methods to the same file**

Append to `frontend/src/services/mockApi.js`:

```javascript
// --- Analytics ---
// Static — does not recompute when transactions mutate in demo mode
export const mockAnalyticsAPI = {
  getPortfolioSummary: () =>
    Promise.resolve({
      holdings: [
        {
          isin: 'IE00B4L5Y983',
          name: 'iShares Core MSCI World UCITS ETF',
          type: 'STOCK',
          total_units: '12.0000',
          total_cost_with_fees: '1024.50',
          average_cost: '85.38',
          current_value: '1120.00',
          absolute_pl: '95.50',
          percentage_pl: '9.32',
          net_buy_in_cost: '1024.50',
          net_buy_in_cost_per_unit: '85.38',
          current_price_per_unit: '93.33',
        },
        {
          isin: 'IE00B4WXJJ64',
          name: 'iShares Physical Gold ETC',
          type: 'BOND',
          total_units: '30.0000',
          total_cost_with_fees: '694.00',
          average_cost: '23.13',
          current_value: '720.00',
          absolute_pl: '26.00',
          percentage_pl: '3.75',
          net_buy_in_cost: '694.00',
          net_buy_in_cost_per_unit: '23.13',
          current_price_per_unit: '24.00',
        },
        {
          isin: 'US0378331005',
          name: 'Apple Inc.',
          type: 'STOCK',
          total_units: '2.0000',
          total_cost_with_fees: '563.00',
          average_cost: '281.50',
          current_value: '420.00',
          absolute_pl: '-143.00',
          percentage_pl: '-25.40',
          net_buy_in_cost: '563.00',
          net_buy_in_cost_per_unit: '281.50',
          current_price_per_unit: '210.00',
        },
      ],
      total_invested: '2281.50',
      total_fees: '13.50',
    }),
};

// --- Position Values ---
export const mockPositionValuesAPI = {
  getAll: () => Promise.resolve([...store.positionValues]),
  upsert: (isin, currentValue) => {
    const idx = store.positionValues.findIndex((p) => p.isin === isin);
    const entry = { isin, current_value: currentValue.toString() };
    if (idx === -1) store.positionValues.push(entry);
    else store.positionValues[idx] = entry;
    return Promise.resolve(entry);
  },
};

// --- ISIN Metadata ---
export const mockIsinMetadataAPI = {
  getAll: (_params = {}) => Promise.resolve([...store.isinMetadata]),
  getByIsin: (isin) =>
    Promise.resolve(store.isinMetadata.find((m) => m.isin === isin) ?? null),
  create: (data) => {
    const created = { ...data };
    store.isinMetadata.push(created);
    return Promise.resolve(created);
  },
  update: (isin, data) => {
    const idx = store.isinMetadata.findIndex((m) => m.isin === isin);
    if (idx === -1) return Promise.reject(new Error('Not found'));
    store.isinMetadata[idx] = { ...store.isinMetadata[idx], ...data };
    return Promise.resolve(store.isinMetadata[idx]);
  },
  delete: (isin) => {
    store.isinMetadata = store.isinMetadata.filter((m) => m.isin !== isin);
    return Promise.resolve(null);
  },
};

// --- Other Assets ---
export const mockOtherAssetsAPI = {
  getAll: (_includeInvestments = true) => Promise.resolve([...store.otherAssets]),
  upsert: (assetType, assetDetail, currency, value) => {
    const idx = store.otherAssets.findIndex(
      (a) => a.asset_type === assetType && a.asset_detail === assetDetail
    );
    const entry = { asset_type: assetType, asset_detail: assetDetail, currency, value: value.toString() };
    if (idx === -1) store.otherAssets.push(entry);
    else store.otherAssets[idx] = entry;
    return Promise.resolve(entry);
  },
};

// --- Settings ---
export const mockSettingsAPI = {
  getExchangeRate: () => Promise.resolve({ exchange_rate: store.settings.exchange_rate }),
  updateExchangeRate: (rate) => {
    store.settings.exchange_rate = rate.toString();
    return Promise.resolve({ exchange_rate: store.settings.exchange_rate });
  },
  getExpectedReturnInvestment: () =>
    Promise.resolve({ expected_return: store.settings.expected_return_investment }),
  updateExpectedReturnInvestment: (percentage) => {
    store.settings.expected_return_investment = percentage.toString();
    return Promise.resolve({ expected_return: store.settings.expected_return_investment });
  },
  getExpectedReturnCD: () =>
    Promise.resolve({ expected_return: store.settings.expected_return_cd }),
  updateExpectedReturnCD: (percentage) => {
    store.settings.expected_return_cd = percentage.toString();
    return Promise.resolve({ expected_return: store.settings.expected_return_cd });
  },
};

// --- Snapshots ---
export const mockSnapshotsAPI = {
  create: () => {
    const now = new Date().toISOString();
    const newSnap = { snapshot_date: now, asset_type: 'INVESTMENT', asset_detail: 'Demo', currency: 'EUR', value: '2260.00', exchange_rate: '25.50', value_eur: '2260.00' };
    store.snapshots.push(newSnap);
    return Promise.resolve(newSnap);
  },
  getSummary: (_startDate = null, _endDate = null) =>
    Promise.resolve({
      snapshots: [...store.snapshots],
      growth: { absolute: '343.50', percentage: '40.12', avg_monthly_increment: '68.70' },
    }),
  deleteByDate: (snapshotDate) => {
    store.snapshots = store.snapshots.filter((s) => s.snapshot_date !== snapshotDate);
    return Promise.resolve(null);
  },
  importCSV: (_file) =>
    Promise.resolve({ imported: 6, errors: [], message: 'Demo mode: 6 rows imported (not persisted)' }),
};
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/services/mockApi.js
git commit -m "feat: add mock API with in-memory store for demo mode"
```

---

## Task 2: Create `AuthContext.jsx`

**File:** `frontend/src/context/AuthContext.jsx`

- [ ] **Step 1: Create the file**

```jsx
import { createContext, useContext, useState } from 'react';

const AuthContext = createContext(null);

const USERNAME = import.meta.env.VITE_APP_USERNAME;
const PASSWORD = import.meta.env.VITE_APP_PASSWORD;

export function AuthProvider({ children }) {
  const [authState, setAuthState] = useState(() => localStorage.getItem('auth_state'));

  // If no password configured (local dev), skip auth entirely
  const devSkip = !PASSWORD;
  const isAuthenticated = devSkip || authState !== null;
  const isDemoMode = authState === 'demo';

  function login(username, password) {
    if (username === USERNAME && password === PASSWORD) {
      localStorage.setItem('auth_state', 'real');
      setAuthState('real');
      return true;
    }
    return false;
  }

  function enterDemo() {
    localStorage.setItem('auth_state', 'demo');
    setAuthState('demo');
  }

  function logout() {
    localStorage.removeItem('auth_state');
    setAuthState(null);
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
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/context/AuthContext.jsx
git commit -m "feat: add AuthContext with login, demo mode, and logout"
```

---

## Task 3: Create `LoginPage.jsx` and `LoginPage.css`

**Files:** `frontend/src/pages/LoginPage.jsx`, `frontend/src/pages/LoginPage.css`

- [ ] **Step 1: Create `LoginPage.jsx`**

```jsx
import { useState } from 'react';
import { useNavigate, Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './LoginPage.css';

function LoginPage() {
  const { isAuthenticated, login, enterDemo } = useAuth();
  const navigate = useNavigate();

  // Already authenticated → go straight to dashboard
  if (isAuthenticated) {
    return <Navigate to="/" replace />;
  }

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  function handleSubmit(e) {
    e.preventDefault();
    setError('');
    if (login(username, password)) {
      navigate('/');
    } else {
      setError('Invalid username or password');
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
            <label htmlFor="username">Username</label>
            <input
              id="username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
              autoFocus
            />
          </div>
          <div className="login-field">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
            />
          </div>
          {error && <p className="login-error">{error}</p>}
          <button type="submit" className="login-button">Login</button>
        </form>
        <div className="login-demo">
          <button type="button" onClick={handleDemo} className="demo-button">
            Try Demo
          </button>
          <p className="demo-hint">Explore the app with sample data — no login required</p>
        </div>
      </div>
    </div>
  );
}

export default LoginPage;
```

- [ ] **Step 2: Create `LoginPage.css`**

```css
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #f5f5f5;
}

.login-card {
  background: white;
  border-radius: 8px;
  padding: 2.5rem;
  width: 100%;
  max-width: 380px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.login-title {
  font-size: 1.4rem;
  font-weight: 600;
  margin: 0 0 1.8rem;
  text-align: center;
  color: #1a1a1a;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.login-field {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.login-field label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #444;
}

.login-field input {
  padding: 0.6rem 0.75rem;
  border: 1px solid #d0d0d0;
  border-radius: 4px;
  font-size: 1rem;
}

.login-field input:focus {
  outline: none;
  border-color: #4a90e2;
  box-shadow: 0 0 0 2px rgba(74, 144, 226, 0.2);
}

.login-error {
  color: #d32f2f;
  font-size: 0.875rem;
  margin: 0;
}

.login-button {
  padding: 0.7rem;
  background-color: #4a90e2;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  margin-top: 0.5rem;
}

.login-button:hover {
  background-color: #357abd;
}

.login-demo {
  margin-top: 1.8rem;
  text-align: center;
  border-top: 1px solid #eee;
  padding-top: 1.5rem;
}

.demo-button {
  background: none;
  border: 1px solid #4a90e2;
  color: #4a90e2;
  padding: 0.5rem 1.2rem;
  border-radius: 4px;
  font-size: 0.9rem;
  cursor: pointer;
}

.demo-button:hover {
  background-color: #f0f6ff;
}

.demo-hint {
  margin: 0.6rem 0 0;
  font-size: 0.8rem;
  color: #888;
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/LoginPage.jsx frontend/src/pages/LoginPage.css
git commit -m "feat: add login page with Try Demo option"
```

---

## Task 4: Modify `api.js` — add demo mode routing

**File:** `frontend/src/services/api.js`

- [ ] **Step 1: Add `isDemoMode` helper and import mock API at the top of the file**

After line 8 (`const API_KEY = ...`), insert:

```javascript
import {
  mockTransactionsAPI,
  mockAnalyticsAPI,
  mockPositionValuesAPI,
  mockIsinMetadataAPI,
  mockOtherAssetsAPI,
  mockSettingsAPI,
  mockSnapshotsAPI,
} from './mockApi.js';

const isDemoMode = () => localStorage.getItem('auth_state') === 'demo';
```

- [ ] **Step 2: Add demo routing to each API method**

At the top of each method body, add a demo check **before** any fetch call:

| Method | Line to add |
|--------|-------------|
| `transactionsAPI.getAll` | `if (isDemoMode()) return mockTransactionsAPI.getAll(params);` |
| `transactionsAPI.getById` | `if (isDemoMode()) return mockTransactionsAPI.getById(id);` |
| `transactionsAPI.create` | `if (isDemoMode()) return mockTransactionsAPI.create(data);` |
| `transactionsAPI.update` | `if (isDemoMode()) return mockTransactionsAPI.update(id, data);` |
| `transactionsAPI.delete` | `if (isDemoMode()) return mockTransactionsAPI.delete(id);` |
| `transactionsAPI.importCSV` | `if (isDemoMode()) return mockTransactionsAPI.importCSV(file);` |
| `analyticsAPI.getPortfolioSummary` | `if (isDemoMode()) return mockAnalyticsAPI.getPortfolioSummary();` |
| `positionValuesAPI.upsert` | `if (isDemoMode()) return mockPositionValuesAPI.upsert(isin, currentValue);` |
| `positionValuesAPI.getAll` | `if (isDemoMode()) return mockPositionValuesAPI.getAll();` |
| `isinMetadataAPI.getAll` | `if (isDemoMode()) return mockIsinMetadataAPI.getAll(params);` |
| `isinMetadataAPI.getByIsin` | `if (isDemoMode()) return mockIsinMetadataAPI.getByIsin(isin);` |
| `isinMetadataAPI.create` | `if (isDemoMode()) return mockIsinMetadataAPI.create(data);` |
| `isinMetadataAPI.update` | `if (isDemoMode()) return mockIsinMetadataAPI.update(isin, data);` |
| `isinMetadataAPI.delete` | `if (isDemoMode()) return mockIsinMetadataAPI.delete(isin);` |
| `otherAssetsAPI.upsert` | `if (isDemoMode()) return mockOtherAssetsAPI.upsert(assetType, assetDetail, currency, value);` |
| `otherAssetsAPI.getAll` | `if (isDemoMode()) return mockOtherAssetsAPI.getAll(includeInvestments);` |
| `settingsAPI.getExchangeRate` | `if (isDemoMode()) return mockSettingsAPI.getExchangeRate();` |
| `settingsAPI.updateExchangeRate` | `if (isDemoMode()) return mockSettingsAPI.updateExchangeRate(rate);` |
| `settingsAPI.getExpectedReturnInvestment` | `if (isDemoMode()) return mockSettingsAPI.getExpectedReturnInvestment();` |
| `settingsAPI.updateExpectedReturnInvestment` | `if (isDemoMode()) return mockSettingsAPI.updateExpectedReturnInvestment(percentage);` |
| `settingsAPI.getExpectedReturnCD` | `if (isDemoMode()) return mockSettingsAPI.getExpectedReturnCD();` |
| `settingsAPI.updateExpectedReturnCD` | `if (isDemoMode()) return mockSettingsAPI.updateExpectedReturnCD(percentage);` |
| `snapshotsAPI.create` | `if (isDemoMode()) return mockSnapshotsAPI.create();` |
| `snapshotsAPI.getSummary` | `if (isDemoMode()) return mockSnapshotsAPI.getSummary(startDate, endDate);` |
| `snapshotsAPI.deleteByDate` | `if (isDemoMode()) return mockSnapshotsAPI.deleteByDate(snapshotDate);` |
| `snapshotsAPI.importCSV` | `if (isDemoMode()) return mockSnapshotsAPI.importCSV(file);` |

- [ ] **Step 3: Commit**

```bash
git add frontend/src/services/api.js
git commit -m "feat: route all API methods to mock store in demo mode"
```

---

## Task 5: Modify `App.jsx` and `Layout.jsx`

**Files:** `frontend/src/App.jsx`, `frontend/src/components/Layout.jsx`

- [ ] **Step 1: Replace `frontend/src/App.jsx` entirely**

```jsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Layout from './components/Layout';
import LoginPage from './pages/LoginPage';
import InvestmentDashboard from './pages/InvestmentDashboard';
import Transactions from './pages/Transactions';
import AddTransaction from './pages/AddTransaction';
import ISINMetadata from './pages/ISINMetadata';
import AddISINMetadata from './pages/AddISINMetadata';
import OtherAssets from './pages/OtherAssets';
import Snapshots from './pages/Snapshots';
import './App.css';

function RequireAuth({ children }) {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/"
            element={
              <RequireAuth>
                <Layout />
              </RequireAuth>
            }
          >
            <Route index element={<InvestmentDashboard />} />
            <Route path="transactions" element={<Transactions />} />
            <Route path="transactions/add" element={<AddTransaction />} />
            <Route path="transactions/edit/:id" element={<AddTransaction />} />
            <Route path="isin-metadata" element={<ISINMetadata />} />
            <Route path="isin-metadata/add" element={<AddISINMetadata />} />
            <Route path="isin-metadata/edit/:isin" element={<AddISINMetadata />} />
            <Route path="other-assets" element={<OtherAssets />} />
            <Route path="snapshots" element={<Snapshots />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
```

> `RequireAuth` is defined in this file because it is only used here.

- [ ] **Step 2: Replace `frontend/src/components/Layout.jsx` entirely**

```jsx
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
```

- [ ] **Step 3: Append demo banner styles to `frontend/src/components/Layout.css`**

Read the file first, then append:

```css
.demo-banner {
  background-color: #fff3cd;
  border-bottom: 1px solid #ffc107;
  color: #856404;
  text-align: center;
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
}

.demo-banner-link {
  color: #856404;
  font-weight: 600;
  text-decoration: underline;
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/App.jsx frontend/src/components/Layout.jsx frontend/src/components/Layout.css
git commit -m "feat: add RequireAuth guard and demo banner to layout"
```

---

## Task 6: Update env files and CI/CD

- [ ] **Step 1: Append to `frontend/.env.development`**

```
VITE_APP_USERNAME=
VITE_APP_PASSWORD=
```

- [ ] **Step 2: Append to `frontend/.env.production`**

```
VITE_APP_USERNAME=
VITE_APP_PASSWORD=
```

- [ ] **Step 3: Update `.github/workflows/deploy.yml` — Build frontend step (currently lines 100–107)**

Change:
```yaml
      - name: Build frontend
        env:
          VITE_API_URL: /api/v1
          VITE_API_KEY: ${{ secrets.API_KEY }}
```

To:
```yaml
      - name: Build frontend
        env:
          VITE_API_URL: /api/v1
          VITE_API_KEY: ${{ secrets.API_KEY }}
          VITE_APP_USERNAME: ${{ secrets.APP_USERNAME }}
          VITE_APP_PASSWORD: ${{ secrets.APP_PASSWORD }}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/.env.development frontend/.env.production .github/workflows/deploy.yml
git commit -m "feat: add APP_USERNAME and APP_PASSWORD env vars and CI/CD secrets"
```

---

## Task 7: Manual Verification

Run: `cd frontend && npm run dev`

- [ ] **1. Dev skip:** Open http://localhost:3000 → goes directly to dashboard, no login shown.

- [ ] **2. Simulate credentials:** Restart with `VITE_APP_USERNAME=admin VITE_APP_PASSWORD=secret npm run dev`. Open http://localhost:3000 → redirected to `/login`.

- [ ] **3. Correct credentials:** Enter `admin` / `secret` → dashboard loads, no banner.

- [ ] **4. Wrong credentials:** Enter wrong details → inline error shown, stays on `/login`.

- [ ] **5. Try Demo:** Click "Try Demo" → dashboard loads, yellow banner visible on all pages.

- [ ] **6. Stateful demo:** In demo mode, add a transaction → appears in list.

- [ ] **7. Refresh reset:** Hard-refresh (Cmd+Shift+R) → demo data resets to seed (new transaction gone).

- [ ] **8. Login link in banner:** Click "Login" → `localStorage` cleared, redirected to `/login`.

- [ ] **9. Already logged in guard:** While authenticated, navigate to http://localhost:3000/login → redirected to dashboard.

---

## GitHub Secrets — REQUIRED before production deploy

Add in GitHub → Settings → Secrets and variables → Actions → New repository secret:

| Secret | Value |
|--------|-------|
| `APP_USERNAME` | Your chosen username |
| `APP_PASSWORD` | Your chosen password |

If missing, CI/CD injects empty strings and the login page is skipped in production.
