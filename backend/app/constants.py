import enum
import re


class TransactionType(str, enum.Enum):
    """Enumeration for transaction types."""

    BUY = "BUY"
    SELL = "SELL"


# ISIN validation pattern
# Format: 2-letter country code + 9 alphanumeric characters + 1 check digit
ISIN_PATTERN = re.compile(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$")

# Pagination defaults
DEFAULT_PAGE_SIZE = 100
MAX_PAGE_SIZE = 1000
