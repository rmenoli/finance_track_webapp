import { analyticsAPI } from '../services/api';
import { formatNumber } from './numberFormat';

function unitContribution(transactionType, units) {
  return transactionType === 'BUY' ? units : -units;
}

function formatValue(value) {
  const { integer, decimal } = formatNumber(value, 2);
  return `${integer}.${decimal}`;
}

/**
 * Shows a confirmation dialog if the operation would close a position that has
 * a stored current_value.
 *
 * Returns { proceed: boolean, warningShown: boolean }.
 * - proceed=false: user cancelled; abort the operation.
 * - warningShown=true: the closure warning served as the user's confirmation.
 * - warningShown=false: no warning shown (callers may still want a generic confirm).
 *
 * @param {Object} params
 * @param {'CREATE'|'UPDATE'|'DELETE'} params.operation
 * @param {{ isin: string, transactionType: string, units: number }} params.incoming
 * @param {{ isin: string, transactionType: string, units: number }} [params.original]
 */
export async function confirmPositionCloseIfNeeded({ operation, incoming, original }) {
  let summary;
  try {
    summary = await analyticsAPI.getPortfolioSummary();
  } catch {
    // If we can't fetch, proceed without warning
    return { proceed: true, warningShown: false };
  }

  const allHoldings = [...(summary.holdings || []), ...(summary.closed_positions || [])];

  const holdingMap = {};
  for (const h of allHoldings) {
    holdingMap[h.isin] = {
      total_units: parseFloat(h.total_units),
      current_value: h.current_value != null ? parseFloat(h.current_value) : null,
    };
  }

  // Collect ISINs to evaluate and their projected units
  const toCheck = {};

  if (operation === 'CREATE') {
    const isin = incoming.isin.toUpperCase();
    const current = holdingMap[isin]?.total_units ?? 0;
    toCheck[isin] = current + unitContribution(incoming.transactionType, incoming.units);
  } else if (operation === 'UPDATE') {
    const newIsin = incoming.isin.toUpperCase();
    const oldIsin = original.isin.toUpperCase();

    if (newIsin === oldIsin) {
      const current = holdingMap[newIsin]?.total_units ?? 0;
      const oldContrib = unitContribution(original.transactionType, original.units);
      const newContrib = unitContribution(incoming.transactionType, incoming.units);
      toCheck[newIsin] = current - oldContrib + newContrib;
    } else {
      // ISIN changed — check old ISIN (removing original) and new ISIN (adding new)
      const currentOld = holdingMap[oldIsin]?.total_units ?? 0;
      toCheck[oldIsin] = currentOld - unitContribution(original.transactionType, original.units);

      const currentNew = holdingMap[newIsin]?.total_units ?? 0;
      toCheck[newIsin] = currentNew + unitContribution(incoming.transactionType, incoming.units);
    }
  } else if (operation === 'DELETE') {
    const isin = original.isin.toUpperCase();
    const current = holdingMap[isin]?.total_units ?? 0;
    // Deleting a transaction reverses its contribution
    toCheck[isin] = current - unitContribution(original.transactionType, original.units);
  }

  let warningShown = false;

  for (const [isin, projectedUnits] of Object.entries(toCheck)) {
    if (projectedUnits !== 0) continue;

    const stored = holdingMap[isin]?.current_value;
    if (stored == null || stored === 0) continue;

    warningShown = true;
    const confirmed = window.confirm(
      `This transaction will close your position for ${isin}.\n` +
      `The current value you entered (${formatValue(stored)}) will be cleared.\n\n` +
      `Continue?`
    );
    if (!confirmed) return { proceed: false, warningShown: true };
  }

  return { proceed: true, warningShown };
}
