// Asset type configurations for Other Assets feature
export const ASSET_TYPES = {
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

// Account names for assets that support account-level tracking
export const ACCOUNTS = ['CSOB', 'RAIF', 'Revolut', 'Wise', 'Degiro'];
