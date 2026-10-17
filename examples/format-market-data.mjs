const finiteNumber = (value) => {
  if (typeof value === 'number') {
    return Number.isFinite(value) ? value : null
  }

  if (typeof value !== 'string' || value.trim() === '') {
    return null
  }

  const number = Number(value.trim())
  return Number.isFinite(number) ? number : null
}

/** Format a value as Chinese yuan. Invalid or missing values use `emptyValue`. */
export function formatCurrency(value, emptyValue = '--') {
  const number = finiteNumber(value)
  if (number === null) return emptyValue

  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(number)
}

/** Format a percentage whose input is already expressed in percent units. */
export function formatPercent(value, emptyValue = '--') {
  const number = finiteNumber(value)
  if (number === null) return emptyValue

  const sign = number > 0 ? '+' : ''
  return `${sign}${number.toFixed(2)}%`
}

/** Return a finite number, or the supplied fallback when the input is invalid. */
export function toFiniteNumber(value, fallback = null) {
  return finiteNumber(value) ?? fallback
}
