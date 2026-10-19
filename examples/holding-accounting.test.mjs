import assert from 'node:assert/strict'
import test from 'node:test'
import { calculateHoldingSnapshot } from './holding-accounting.mjs'

test('calculates a holding from confirmed snapshot values and a valid estimate', () => {
  const result = calculateHoldingSnapshot({
    snapshotAmount: 10_000,
    accumulatedProfit: 600,
    confirmedNav: 1.25,
    estimatedNav: 1.262,
    estimateIsValid: true,
  })

  assert.equal(result.shares, 8_000)
  assert.equal(result.cost, 9_400)
  assert.equal(result.marketValue, 10_096)
  assert.equal(result.cumulativeProfit, 696)
  assert.ok(Math.abs(result.todayProfit - 96) < 1e-9)
  assert.equal(result.usedEstimate, true)
})

test('falls back to the latest confirmed NAV when the estimate is stale or invalid', () => {
  const stale = calculateHoldingSnapshot({
    snapshotAmount: 10_000,
    accumulatedProfit: -200,
    confirmedNav: 2,
    estimatedNav: 2.1,
    estimateIsValid: false,
  })
  const invalidEstimate = calculateHoldingSnapshot({
    snapshotAmount: 10_000,
    accumulatedProfit: -200,
    confirmedNav: 2,
    estimatedNav: 0,
    estimateIsValid: true,
  })

  for (const result of [stale, invalidEstimate]) {
    assert.equal(result.shares, 5_000)
    assert.equal(result.cost, 10_200)
    assert.equal(result.marketValue, 10_000)
    assert.equal(result.cumulativeProfit, -200)
    assert.equal(result.todayProfit, 0)
    assert.equal(result.usedEstimate, false)
  }
})

test('rejects invalid snapshot inputs', () => {
  assert.throws(() => calculateHoldingSnapshot({ snapshotAmount: 1, accumulatedProfit: 0, confirmedNav: 0 }), RangeError)
  assert.throws(() => calculateHoldingSnapshot({ snapshotAmount: Number.NaN, accumulatedProfit: 0, confirmedNav: 1 }), TypeError)
  assert.throws(() => calculateHoldingSnapshot({ snapshotAmount: -1, accumulatedProfit: 0, confirmedNav: 1 }), RangeError)
})
