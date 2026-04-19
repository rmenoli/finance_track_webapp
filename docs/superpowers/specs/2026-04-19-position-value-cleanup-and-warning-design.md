# Position Value Cleanup + Warning — Design

**Date:** 2026-04-19
**Status:** Draft
**Scope:** Backend (`transaction_service`) + Frontend (`TransactionForm`, `Transactions` page)

## Problem

A user-entered `current_value` can be silently orphaned when a transaction
operation closes a position. Observed flow:

1. User creates a BUY → position appears in the Investment Dashboard with
   `current_value = 0`.
2. User clicks the cell and enters a value → stored in `position_values`.
3. User creates a SELL that zeros out units.
4. Position moves to the Closed Positions table, which is read-only.
5. The `position_value` row stays in the DB because `create_transaction()`
   never calls the cleanup helper (unlike `update`/`delete`). The API masks
   it to `0` in closed-position responses, so the user sees `0` but cannot
   edit.
6. If the user later BUYs the same ISIN, the stale value resurfaces.

Root cause: asymmetry in `backend/app/services/transaction_service.py`.
`update_transaction()` (line 210) and `delete_transaction()` (line 272) call
`_cleanup_position_value_for_closed_position()`. `create_transaction()` does
not.

Secondary problem: even when cleanup works correctly (e.g., deleting a BUY
that closes the position), the user-entered `current_value` is silently
dropped. No warning, no chance to cancel.

## Guiding Invariant

> No shares held → `current_value = 0`, by definition.

The system should enforce this automatically on every transaction write
path, and warn the user before an action silently discards data they entered.

## Design

### Backend — symmetric cleanup

**File:** `backend/app/services/transaction_service.py`

Add a call to `_cleanup_position_value_for_closed_position()` inside
`create_transaction()` after the commit, mirroring the existing pattern in
`update_transaction` and `delete_transaction`:

```python
def create_transaction(db: Session, transaction_data: TransactionCreate) -> Transaction:
    transaction = Transaction(**transaction_data.model_dump())
    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    # AUDIT LOG
    log_with_context(...)

    # Cleanup if this transaction closed the position
    _cleanup_position_value_for_closed_position(db, transaction.isin)

    return transaction
```

**Why here:** symmetry with the other two write paths. After this change,
any transaction operation that leaves `total_units == 0` drops the stored
`position_value` automatically. The invariant is enforced server-side and
no UI flow can bypass it.

### Frontend — warning before destructive action

**Shared helper:** `frontend/src/utils/positionCloseWarning.js`
(new file; adjust to match existing util conventions)

```javascript
// Returns true to proceed, false to abort.
export async function confirmPositionCloseIfNeeded({
  isin,
  transactionType,  // 'BUY' | 'SELL'
  units,            // Decimal string/number
  operation,        // 'CREATE' | 'UPDATE' | 'DELETE'
  currentTransactionId,  // only for UPDATE/DELETE
}) {
  // 1. Fetch portfolio summary + position values (reuse existing endpoints)
  // 2. Compute projected total_units for this ISIN after the operation
  // 3. If projected total_units !== 0 → return true (no warning)
  // 4. If no position_value stored for this ISIN → return true (nothing to lose)
  // 5. Otherwise, window.confirm() with:
  //    "This transaction will close your position for <ISIN>.
  //     The current value you entered (€X,XXX.XX) will be cleared. Continue?"
  //    return confirm result
}
```

**Call sites:**

1. `frontend/src/components/TransactionForm.jsx` — before `onSubmit` calls
   the API, for both CREATE and UPDATE.
2. `frontend/src/pages/Transactions.jsx` `handleDelete` — replace the
   existing generic `window.confirm` with this helper when it applies (if
   no closure, keep the existing generic confirm).

**Data source:** the helper calls `GET /portfolio-summary` (already returns
holdings with `total_units` and `current_value`). No new endpoints.

**Projection logic:**

| Operation          | Projected units for ISIN                             |
|--------------------|------------------------------------------------------|
| CREATE BUY         | current + units                                      |
| CREATE SELL        | current - units                                      |
| UPDATE (same ISIN) | current - old_contribution + new_contribution        |
| UPDATE (ISIN change) | check old ISIN and new ISIN separately             |
| DELETE BUY         | current - units                                      |
| DELETE SELL        | current + units                                      |

For UPDATE, the helper needs the original transaction's values; the form
already has them when editing.

## Tests

### Backend

New test in `backend/tests/test_transaction_service.py`
(or `test_position_value_cleanup.py`, whichever matches existing layout):

- `test_create_sell_closing_position_cleans_up_position_value`
  - Setup: BUY 10 units + store `position_value` = 1000 for the ISIN.
  - Action: `create_transaction(SELL 10)`.
  - Assert: `position_value` for the ISIN is deleted.

Regression check: existing update/delete cleanup tests must still pass.

### Frontend (manual)

- Create SELL that closes a position with stored value → warning shown;
  cancel aborts, confirm proceeds and clears the value.
- Delete BUY that closes a position with stored value → warning shown.
- Edit a BUY so the projected total reaches zero → warning shown.
- Same three actions with no stored value → **no** warning (silent).
- Action that does not close the position → no warning (silent).

## Out of Scope

- Backfilling already-orphaned `position_values` from past SELLs (user
  chose option C over B).
- Allowing edits to `current_value` for closed positions — stays
  read-only; matches the "0 by definition" rule.
- Changes to the Closed Positions table UI.

## Risks

- **Forgotten call sites:** if a future code path creates transactions
  outside `create_transaction()`, the invariant could be bypassed. Mitigation:
  keep all writes funneled through the service layer (already the pattern).
- **Stale portfolio-summary fetch:** the helper reads via API, so race
  conditions with concurrent edits are possible. For a single-user app
  this is acceptable; backend cleanup is still authoritative.
- **Existing orphans:** pre-existing stranded `position_values` rows are
  not cleaned up by this change. Accepted per scope; can be addressed
  later via the already-existing `cleanup_orphaned_position_values()`
  utility if needed.
