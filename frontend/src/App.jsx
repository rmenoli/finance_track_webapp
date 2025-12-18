import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import InvestmentDashboard from './pages/InvestmentDashboard';
import Transactions from './pages/Transactions';
import AddTransaction from './pages/AddTransaction';
import './App.css';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<InvestmentDashboard />} />
          <Route path="transactions" element={<Transactions />} />
          <Route path="transactions/add" element={<AddTransaction />} />
          <Route path="transactions/edit/:id" element={<AddTransaction />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
