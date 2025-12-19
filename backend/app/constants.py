import enum
import re


class TransactionType(str, enum.Enum):
    """Enumeration for transaction types."""

    BUY = "BUY"
    SELL = "SELL"


class ISINType(str, enum.Enum):
    """Enumeration for ISIN asset types."""

    STOCK = "STOCK"
    BOND = "BOND"
    REAL_ASSET = "REAL_ASSET"


class AssetType(str, enum.Enum):
    """Enumeration for other asset types."""

    INVESTMENTS = "investments"
    CRYPTO = "crypto"
    CASH_EUR = "cash_eur"
    CASH_CZK = "cash_czk"
    CD_ACCOUNT = "cd_account"
    PENSION_FUND = "pension_fund"


class Currency(str, enum.Enum):
    """Enumeration for currencies."""

    EUR = "EUR"
    CZK = "CZK"


# Valid account names for cash assets
VALID_ACCOUNT_NAMES = {"CSOB", "RAIF", "Revolut", "Wise", "Degiro"}

# ISIN validation pattern
# Format: 2-letter country code + 9 alphanumeric characters + 1 check digit
ISIN_PATTERN = re.compile(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$")

# Pagination defaults
DEFAULT_PAGE_SIZE = 100
MAX_PAGE_SIZE = 1000
