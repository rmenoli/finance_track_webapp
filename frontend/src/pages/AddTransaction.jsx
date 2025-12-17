import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { transactionsAPI } from '../services/api';
import TransactionForm from '../components/TransactionForm';
import './AddTransaction.css';

function AddTransaction() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [initialData, setInitialData] = useState(null);
  const [loading, setLoading] = useState(!!id);
  const [error, setError] = useState(null);

  const isEdit = !!id;

  useEffect(() => {
    if (id) {
      loadTransaction();
    }
  }, [id]);

  const loadTransaction = async () => {
    try {
      const data = await transactionsAPI.getById(id);
      setInitialData(data);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (data) => {
    try {
      if (isEdit) {
        await transactionsAPI.update(id, data);
      } else {
        await transactionsAPI.create(data);
      }
      navigate('/transactions');
    } catch (err) {
      throw new Error(err.message);
    }
  };

  if (loading) {
    return <div className="loading">Loading transaction...</div>;
  }

  if (error) {
    return <div className="error">Error: {error}</div>;
  }

  return (
    <div className="add-transaction-page">
      <h1>{isEdit ? 'Edit Transaction' : 'Add Transaction'}</h1>

      <div className="form-card">
        <TransactionForm
          initialData={initialData}
          onSubmit={handleSubmit}
          onCancel={() => navigate('/transactions')}
        />
      </div>
    </div>
  );
}

export default AddTransaction;
