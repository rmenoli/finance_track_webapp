import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { isinMetadataAPI } from '../services/api';
import ISINMetadataForm from '../components/ISINMetadataForm';
import './AddISINMetadata.css';

function AddISINMetadata() {
  const { isin } = useParams();
  const navigate = useNavigate();
  const [initialData, setInitialData] = useState(null);
  const [loading, setLoading] = useState(!!isin);
  const [error, setError] = useState(null);

  const isEdit = !!isin;

  useEffect(() => {
    if (isin) {
      loadMetadata();
    }
  }, [isin]);

  const loadMetadata = async () => {
    try {
      const data = await isinMetadataAPI.getByIsin(isin);
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
        // For update, only send name and type (ISIN cannot be changed)
        const updateData = {
          name: data.name,
          type: data.type,
        };
        await isinMetadataAPI.update(isin, updateData);
      } else {
        await isinMetadataAPI.create(data);
      }
      navigate('/isin-metadata');
    } catch (err) {
      throw new Error(err.message);
    }
  };

  if (loading) {
    return <div className="loading">Loading ISIN metadata...</div>;
  }

  if (error) {
    return <div className="error">Error: {error}</div>;
  }

  return (
    <div className="add-isin-metadata-page">
      <h1>{isEdit ? 'Edit ISIN Metadata' : 'Add ISIN Metadata'}</h1>

      <div className="form-card">
        <ISINMetadataForm
          initialData={initialData}
          onSubmit={handleSubmit}
          onCancel={() => navigate('/isin-metadata')}
        />
      </div>
    </div>
  );
}

export default AddISINMetadata;
