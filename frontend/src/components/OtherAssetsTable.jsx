import { useState } from 'react';
import { otherAssetsAPI } from '../services/api';
import FormattedNumber from './FormattedNumber';
import './OtherAssetsTable.css';

// Asset type configurations
const ASSET_TYPES = {
  investments: {
    label: 'Investimenti',
    hasAccounts: false,
    readOnly: true,
    currency: 'EUR',
  },
  crypto: {
    label: 'Crypto',
    hasAccounts: false,
    readOnly: false,
    currency: 'EUR',
  },
  cash_eur: {
    label: 'Cash EUR',
    hasAccounts: true,
    readOnly: false,
    currency: 'EUR',
  },
  cash_czk: {
    label: 'Cash CZK',
    hasAccounts: true,
    readOnly: false,
    currency: 'CZK',
  },
  cd_account: {
    label: 'CD svincolabile',
    hasAccounts: false,
    readOnly: false,
    currency: 'CZK',
  },
  pension_fund: {
    label: 'Fondo Pensione',
    hasAccounts: false,
    readOnly: false,
    currency: 'CZK',
  },
};

const ACCOUNTS = ['CSOB', 'RAIF', 'Revolut', 'Wise', 'Degiro'];

function OtherAssetsTable({ assets, exchangeRate, onDataChange }) {
  const [editingCell, setEditingCell] = useState(null); // { assetType, account }
  const [editingValue, setEditingValue] = useState('');
  const [savingCell, setSavingCell] = useState(null);
  const [error, setError] = useState(null);

  // Transform assets array to map: { assetType: { account: { value, currency, value_eur } } }
  const assetsMap = {};
  assets.forEach((asset) => {
    if (!assetsMap[asset.asset_type]) {
      assetsMap[asset.asset_type] = {};
    }

    const key = asset.asset_detail || 'default';
    assetsMap[asset.asset_type][key] = {
      value: parseFloat(asset.value) || 0,
      currency: asset.currency,
      value_eur: parseFloat(asset.value_eur) || 0, // EUR value from backend
    };
  });

  const startEditing = (assetType, account = null) => {
    const config = ASSET_TYPES[assetType];
    if (config.readOnly) return;

    const key = account || 'default';
    const currentValue = assetsMap[assetType]?.[key]?.value || 0;

    setEditingCell({ assetType, account });
    setEditingValue(currentValue.toString());
  };

  const saveValue = async (assetType, account = null) => {
    const numValue = parseFloat(editingValue);
    if (isNaN(numValue) || numValue < 0) {
      setError('Please enter a valid value (>= 0)');
      setEditingCell(null);
      setEditingValue('');
      return;
    }

    try {
      setSavingCell({ assetType, account });
      setError(null);

      const config = ASSET_TYPES[assetType];
      const assetDetail = account; // For cash: account name, for others: null

      await otherAssetsAPI.upsert(
        assetType,
        assetDetail,
        config.currency,
        numValue
      );

      // Notify parent to refresh data
      if (onDataChange) {
        onDataChange();
      }

      setEditingCell(null);
      setEditingValue('');
    } catch (err) {
      console.error('Failed to save value:', err);
      setError(`Failed to save value. ${err.message}`);
    } finally {
      setSavingCell(null);
    }
  };

  const handleBlur = (assetType, account) => {
    if (editingValue !== '') {
      saveValue(assetType, account);
    } else {
      setEditingCell(null);
      setEditingValue('');
    }
  };

  const handleKeyDown = (e, assetType, account) => {
    if (e.key === 'Enter') {
      if (editingValue !== '') {
        saveValue(assetType, account);
      } else {
        setEditingCell(null);
        setEditingValue('');
      }
    } else if (e.key === 'Escape') {
      setEditingCell(null);
      setEditingValue('');
    }
  };

  const isEditing = (assetType, account = null) => {
    if (!editingCell) return false;
    return (
      editingCell.assetType === assetType &&
      editingCell.account === account
    );
  };

  const isSaving = (assetType, account = null) => {
    if (!savingCell) return false;
    return (
      savingCell.assetType === assetType &&
      savingCell.account === account
    );
  };

  // Calculate totals for a row (using backend-calculated EUR values)
  const calculateRowTotals = (assetType, config) => {
    let totalInNative = 0;
    let totalInEur = 0;

    if (config.hasAccounts) {
      // Sum all accounts
      ACCOUNTS.forEach((account) => {
        totalInNative += assetsMap[assetType]?.[account]?.value || 0;
        totalInEur += assetsMap[assetType]?.[account]?.value_eur || 0;
      });
    } else {
      // Single value
      totalInNative = assetsMap[assetType]?.default?.value || 0;
      totalInEur = assetsMap[assetType]?.default?.value_eur || 0;
    }

    return { totalInNative, totalInEur };
  };

  // Calculate grand total across all rows
  const calculateGrandTotal = () => {
    let grandTotalEur = 0;

    Object.entries(ASSET_TYPES).forEach(([assetType, config]) => {
      const { totalInEur } = calculateRowTotals(assetType, config);
      grandTotalEur += totalInEur;
    });

    return grandTotalEur;
  };

  const renderCell = (assetType, account = null) => {
    const config = ASSET_TYPES[assetType];
    const key = account || 'default';
    const value = assetsMap[assetType]?.[key]?.value || 0;
    const editing = isEditing(assetType, account);
    const saving = isSaving(assetType, account);
    const currencySymbol = config.currency === 'EUR' ? '€' : 'CZK';

    if (config.readOnly) {
      return (
        <td className="value-cell read-only">
          <FormattedNumber value={value} currency={false} />
          <span className="currency-symbol"> {currencySymbol}</span>
        </td>
      );
    }

    if (editing) {
      return (
        <td className="value-cell editing">
          <input
            type="number"
            step="0.01"
            min="0"
            value={editingValue}
            onChange={(e) => setEditingValue(e.target.value)}
            onBlur={() => handleBlur(assetType, account)}
            onKeyDown={(e) => handleKeyDown(e, assetType, account)}
            autoFocus
            placeholder="0.00"
          />
        </td>
      );
    }

    return (
      <td
        className="value-cell editable"
        onClick={() => startEditing(assetType, account)}
        title="Click to edit"
      >
        <FormattedNumber value={value} currency={false} />
        <span className="currency-symbol"> {currencySymbol}</span>
        {saving && <span className="saving-indicator">💾</span>}
      </td>
    );
  };

  const grandTotal = calculateGrandTotal();

  return (
    <div className="other-assets-table-container">
      {error && (
        <div className="error-message" style={{ marginBottom: '16px' }}>
          {error}
        </div>
      )}

      <table className="other-assets-table">
        <thead>
          <tr>
            <th>Asset Type</th>
            {ACCOUNTS.map((account) => (
              <th key={account}>{account}</th>
            ))}
            <th>Quanto in valuta</th>
            <th>Quanto in Euro</th>
          </tr>
        </thead>
        <tbody>
          {Object.entries(ASSET_TYPES).map(([assetType, config]) => {
            const { totalInNative, totalInEur } = calculateRowTotals(
              assetType,
              config
            );

            return (
              <tr key={assetType} className={config.readOnly ? 'read-only-row' : ''}>
                <td className="asset-type-cell">{config.label}</td>

                {config.hasAccounts ? (
                  // Render individual account columns for cash assets
                  <>
                    {ACCOUNTS.map((account) => renderCell(assetType, account))}
                  </>
                ) : (
                  // For non-account assets, render single value in first column, empty cells for rest
                  <>
                    {renderCell(assetType, null)}
                    {ACCOUNTS.slice(1).map((account) => (
                      <td key={account} className="empty-cell"></td>
                    ))}
                  </>
                )}

                {/* Computed columns */}
                <td className="computed-cell">
                  <FormattedNumber value={totalInNative} currency={false} />
                  <span className="currency-label"> {config.currency}</span>
                </td>
                <td className="computed-cell">
                  <FormattedNumber value={totalInEur} currency={false} />
                  <span className="currency-label"> EUR</span>
                </td>
              </tr>
            );
          })}

          {/* Grand Total Row */}
          <tr className="grand-total-row">
            <td colSpan={ACCOUNTS.length + 1}>
              <strong>Grand Total</strong>
            </td>
            <td className="computed-cell" colSpan={2}>
              <strong>
                <FormattedNumber value={grandTotal} currency={false} />
                <span className="currency-label"> EUR</span>
              </strong>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}

export default OtherAssetsTable;
