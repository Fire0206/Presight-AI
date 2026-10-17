import test from 'node:test'
import assert from 'node:assert/strict'
import { formatCurrency, formatPercent, toFiniteNumber } from './format-market-data.mjs'

test('formats currency with two decimal places', () => {
  assert.equal(formatCurrency('1234.5'), '¥1,234.50')
})

test('uses a placeholder for missing or invalid values', () => {
  assert.equal(formatCurrency(null), '--')
  assert.equal(formatPercent('not-a-number'), '--')
  assert.equal(formatPercent(undefined, '暂无数据'), '暂无数据')
})

test('formats signed percentage values', () => {
  assert.equal(formatPercent(1.256), '+1.26%')
  assert.equal(formatPercent(-2), '-2.00%')
  assert.equal(formatPercent(0), '0.00%')
})

test('rejects partial numeric strings and non-finite numbers', () => {
  assert.equal(toFiniteNumber('12abc'), null)
  assert.equal(toFiniteNumber(Infinity, 0), 0)
  assert.equal(toFiniteNumber('  12.5  '), 12.5)
})
