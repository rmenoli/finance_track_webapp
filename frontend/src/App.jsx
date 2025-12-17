import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Transactions from './pages/Transactions';
import Holdings from './pages/Holdings';
import Analytics from './pages/Analytics';
import AddTransaction from './pages/AddTransaction';
import './App.css';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="transactions" element={<Transactions />} />
          <Route path="transactions/add" element={<AddTransaction />} />
          <Route path="transactions/edit/:id" element={<AddTransaction />} />
          <Route path="holdings" element={<Holdings />} />
          <Route path="analytics" element={<Analytics />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
