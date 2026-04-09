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
