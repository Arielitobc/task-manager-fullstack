import { describe, expect, it } from 'vitest'
import { formatDate, isOverdue, todayIso } from './dates'

describe('dates', () => {
  it('detects overdue tasks only when not completed', () => {
    expect(isOverdue('2026-01-01', 'pending', '2026-01-02')).toBe(true)
    expect(isOverdue('2026-01-01', 'completed', '2026-01-02')).toBe(false)
    expect(isOverdue('2026-01-02', 'pending', '2026-01-02')).toBe(false)
    expect(isOverdue(null, 'pending', '2026-01-02')).toBe(false)
  })

  it('formats a date without shifting the day because of the timezone', () => {
    expect(formatDate('2026-03-01')).toContain('1')
    expect(formatDate('2026-03-01')).not.toContain('28')
  })

  it('returns today as YYYY-MM-DD', () => {
    expect(todayIso(new Date(2026, 10, 9, 23, 30))).toBe('2026-11-09')
  })
})
