/**
 * A small, pure calculator for a confirmed holding snapshot plus an optional
 * current-day estimate. It does not resolve trading calendars or pending trades.
 */

function requireFinite(name, value) {
  if (typeof value !== 'number' || !Number.isFinite(value)) {
    throw new TypeError(`${name} must be a finite number`)
  }
}

export function calculateHoldingSnapshot({
  snapshotAmount,
  accumulatedProfit,
  confirmedNav,
  estimatedNav = null,
  estimateIsValid = false,
}) {
  requireFinite('snapshotAmount', snapshotAmount)
  requireFinite('accumulatedProfit', accumulatedProfit)
  requireFinite('confirmedNav', confirmedNav)
  if (snapshotAmount < 0) throw new RangeError('snapshotAmount must be >= 0')
  if (confirmedNav <= 0) throw new RangeError('confirmedNav must be > 0')

  const useEstimate = estimateIsValid && typeof estimatedNav === 'number' && Number.isFinite(estimatedNav) && estimatedNav > 0
  const valuationNav = useEstimate ? estimatedNav : confirmedNav
  const shares = snapshotAmount / confirmedNav
  const cost = snapshotAmount - accumulatedProfit
  const marketValue = shares * valuationNav

  return {
    shares,
    cost,
    marketValue,
    cumulativeProfit: marketValue - cost,
    todayProfit: useEstimate ? shares * (estimatedNav - confirmedNav) : 0,
    valuationNav,
    usedEstimate: useEstimate,
  }
}
