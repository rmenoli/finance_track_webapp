import { useState, useEffect } from 'react';
import './TransactionForm.css';

function TransactionForm({ initialData, onSubmit, onCancel }) {
  const [formData, setFormData] = useState({
    date: '',
    isin: '',
    broker: '',
    price_per_unit: '',
    units: '',
    fee: '0',
    transaction_type: 'BUY',
  });
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (initialData) {
      setFormData({
        date: initialData.date,
        isin: initialData.isin,
        broker: initialData.broker,
        price_per_unit: initialData.price_per_unit,
        units: initialData.units,
        fee: initialData.fee || '0',
        transaction_type: initialData.transaction_type,
      });
    }
  }, [initialData]);

  const validateForm = () => {
    const newErrors = {};

    // Date validation
    if (!formData.date) {
      newErrors.date = 'Date is required';
    } else {
      const selectedDate = new Date(formData.date);
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      if (selectedDate > today) {
        newErrors.date = 'Transaction date cannot be in the future';
      }
    }

    // ISIN validation
    if (!formData.isin) {
      newErrors.isin = 'ISIN is required';
    } else if (!/^[A-Z]{2}[A-Z0-9]{9}[0-9]$/.test(formData.isin.toUpperCase())) {
      newErrors.isin = 'ISIN must be 12 characters: 2 letters + 9 alphanumeric + 1 digit';
    }

    // Broker validation
    if (!formData.broker || formData.broker.trim().length === 0) {
      newErrors.broker = 'Broker is required';
    }

    // Price validation
    if (!formData.price_per_unit || parseFloat(formData.price_per_unit) <= 0) {
      newErrors.price_per_unit = 'Price per unit must be greater than 0';
    }

    // Units validation
    if (!formData.units || parseFloat(formData.units) <= 0) {
      newErrors.units = 'Units must be greater than 0';
    }

    // Fee validation
    if (formData.fee && parseFloat(formData.fee) < 0) {
      newErrors.fee = 'Fee cannot be negative';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    // Clear error for this field
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: undefined }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setSubmitting(true);

    try {
      await onSubmit({
        ...formData,
        isin: formData.isin.toUpperCase(),
        price_per_unit: parseFloat(formData.price_per_unit),
        units: parseFloat(formData.units),
        fee: parseFloat(formData.fee) || 0,
      });
    } catch (err) {
      alert('Error: ' + err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="transaction-form">
      <div className="form-row">
        <div className="form-group">
          <label htmlFor="date">Date *</label>
          <input
            type="date"
            id="date"
            name="date"
            value={formData.date}
            onChange={handleChange}
            className={`input ${errors.date ? 'input-error' : ''}`}
            max={new Date().toISOString().split('T')[0]}
          />
          {errors.date && <span className="error-message">{errors.date}</span>}
        </div>

        <div className="form-group">
          <label htmlFor="transaction_type">Type *</label>
          <select
            id="transaction_type"
            name="transaction_type"
            value={formData.transaction_type}
            onChange={handleChange}
            className="input"
          >
            <option value="BUY">BUY</option>
            <option value="SELL">SELL</option>
          </select>
        </div>
      </div>

      <div className="form-group">
        <label htmlFor="isin">ISIN *</label>
        <input
          type="text"
          id="isin"
          name="isin"
          value={formData.isin}
          onChange={handleChange}
          className={`input ${errors.isin ? 'input-error' : ''}`}
          placeholder="IE00B4L5Y983"
          maxLength="12"
        />
        {errors.isin && <span className="error-message">{errors.isin}</span>}
      </div>

      <div className="form-group">
        <label htmlFor="broker">Broker *</label>
        <input
          type="text"
          id="broker"
          name="broker"
          value={formData.broker}
          onChange={handleChange}
          className={`input ${errors.broker ? 'input-error' : ''}`}
          placeholder="Interactive Brokers"
        />
        {errors.broker && <span className="error-message">{errors.broker}</span>}
      </div>

      <div className="form-row">
        <div className="form-group">
          <label htmlFor="units">Units *</label>
          <input
            type="number"
            id="units"
            name="units"
            value={formData.units}
            onChange={handleChange}
            className={`input ${errors.units ? 'input-error' : ''}`}
            step="0.0001"
            min="0.0001"
            placeholder="10.0"
          />
          {errors.units && <span className="error-message">{errors.units}</span>}
        </div>

        <div className="form-group">
          <label htmlFor="price_per_unit">Price per Unit *</label>
          <input
            type="number"
            id="price_per_unit"
            name="price_per_unit"
            value={formData.price_per_unit}
            onChange={handleChange}
            className={`input ${errors.price_per_unit ? 'input-error' : ''}`}
            step="0.01"
            min="0.01"
            placeholder="450.25"
          />
          {errors.price_per_unit && <span className="error-message">{errors.price_per_unit}</span>}
        </div>

        <div className="form-group">
          <label htmlFor="fee">Fee</label>
          <input
            type="number"
            id="fee"
            name="fee"
            value={formData.fee}
            onChange={handleChange}
            className={`input ${errors.fee ? 'input-error' : ''}`}
            step="0.01"
            min="0"
            placeholder="1.50"
          />
          {errors.fee && <span className="error-message">{errors.fee}</span>}
        </div>
      </div>

      <div className="form-actions">
        <button
          type="button"
          onClick={onCancel}
          className="btn btn-secondary"
          disabled={submitting}
        >
          Cancel
        </button>
        <button
          type="submit"
          className="btn btn-primary"
          disabled={submitting}
        >
          {submitting ? 'Saving...' : initialData ? 'Update Transaction' : 'Add Transaction'}
        </button>
      </div>
    </form>
  );
}

export default TransactionForm;
