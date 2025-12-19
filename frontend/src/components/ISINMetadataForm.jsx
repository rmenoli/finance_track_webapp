import { useState, useEffect } from 'react';
import './ISINMetadataForm.css';

function ISINMetadataForm({ initialData, onSubmit, onCancel }) {
  const [formData, setFormData] = useState({
    isin: '',
    name: '',
    type: 'STOCK',
  });
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (initialData) {
      setFormData({
        isin: initialData.isin || '',
        name: initialData.name || '',
        type: initialData.type || 'STOCK',
      });
    }
  }, [initialData]);

  const validateForm = () => {
    const newErrors = {};

    // ISIN validation
    if (!formData.isin) {
      newErrors.isin = 'ISIN is required';
    } else if (!/^[A-Z]{2}[A-Z0-9]{9}[0-9]$/.test(formData.isin.toUpperCase())) {
      newErrors.isin = 'ISIN must be 12 characters: 2 letters + 9 alphanumeric + 1 digit';
    }

    // Name validation
    if (!formData.name || formData.name.trim().length === 0) {
      newErrors.name = 'Name is required';
    } else if (formData.name.trim().length > 255) {
      newErrors.name = 'Name must be less than 255 characters';
    }

    // Type validation
    if (!formData.type) {
      newErrors.type = 'Type is required';
    } else if (!['STOCK', 'BOND', 'REAL_ASSET'].includes(formData.type)) {
      newErrors.type = 'Type must be STOCK, BOND, or REAL_ASSET';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    // Clear error for this field
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setSubmitting(true);
    try {
      // Prepare data with uppercase ISIN and trimmed name
      const submitData = {
        isin: formData.isin.toUpperCase(),
        name: formData.name.trim(),
        type: formData.type,
      };

      await onSubmit(submitData);
    } catch (error) {
      console.error('Form submission error:', error);
      setErrors({ submit: error.message || 'Failed to submit form' });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="isin-metadata-form">
      <div className="form-group">
        <label htmlFor="isin">
          ISIN <span className="required">*</span>
        </label>
        <input
          type="text"
          id="isin"
          name="isin"
          value={formData.isin}
          onChange={handleChange}
          placeholder="IE00B4L5Y983"
          maxLength="12"
          disabled={!!initialData} // Disable ISIN editing when updating
          className={errors.isin ? 'error' : ''}
        />
        {errors.isin && <span className="error-message">{errors.isin}</span>}
        <small>Format: 2 letters + 9 alphanumeric + 1 digit</small>
      </div>

      <div className="form-group">
        <label htmlFor="name">
          Name <span className="required">*</span>
        </label>
        <input
          type="text"
          id="name"
          name="name"
          value={formData.name}
          onChange={handleChange}
          placeholder="iShares Core MSCI Emerging Markets ETF"
          maxLength="255"
          className={errors.name ? 'error' : ''}
        />
        {errors.name && <span className="error-message">{errors.name}</span>}
      </div>

      <div className="form-group">
        <label htmlFor="type">
          Type <span className="required">*</span>
        </label>
        <select
          id="type"
          name="type"
          value={formData.type}
          onChange={handleChange}
          className={errors.type ? 'error' : ''}
        >
          <option value="STOCK">Stock</option>
          <option value="BOND">Bond</option>
          <option value="REAL_ASSET">Real Asset</option>
        </select>
        {errors.type && <span className="error-message">{errors.type}</span>}
      </div>

      {errors.submit && (
        <div className="form-error">
          {errors.submit}
        </div>
      )}

      <div className="form-actions">
        <button type="submit" className="btn btn-primary" disabled={submitting}>
          {submitting ? 'Saving...' : (initialData ? 'Update' : 'Create')}
        </button>
        {onCancel && (
          <button type="button" className="btn btn-secondary" onClick={onCancel}>
            Cancel
          </button>
        )}
      </div>
    </form>
  );
}

export default ISINMetadataForm;
