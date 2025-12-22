import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import InvestmentDashboard from './pages/InvestmentDashboard';
import Transactions from './pages/Transactions';
import AddTransaction from './pages/AddTransaction';
import ISINMetadata from './pages/ISINMetadata';
import AddISINMetadata from './pages/AddISINMetadata';
import OtherAssets from './pages/OtherAssets';
import Snapshots from './pages/Snapshots';
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
          <Route path="isin-metadata" element={<ISINMetadata />} />
          <Route path="isin-metadata/add" element={<AddISINMetadata />} />
          <Route path="isin-metadata/edit/:isin" element={<AddISINMetadata />} />
          <Route path="other-assets" element={<OtherAssets />} />
          <Route path="snapshots" element={<Snapshots />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
