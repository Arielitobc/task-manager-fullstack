/** Today as YYYY-MM-DD in the user's local timezone. */
export function todayIso(now: Date = new Date()): string {
  const offset = now.getTimezoneOffset() * 60_000
  return new Date(now.getTime() - offset).toISOString().slice(0, 10)
}

/** Parse a YYYY-MM-DD date without the UTC shift `new Date('2026-01-01')` causes. */
function parseIsoDate(iso: string): Date {
  const [y, m, d] = iso.split('-').map(Number)
  return new Date(y, m - 1, d)
}

export function formatDate(iso: string): string {
  return parseIsoDate(iso).toLocaleDateString(undefined, {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}

export function isOverdue(dueDate: string | null, status: string, today = todayIso()): boolean {
  return Boolean(dueDate) && status !== 'completed' && (dueDate as string) < today
}
