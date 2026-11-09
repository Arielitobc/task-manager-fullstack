import { useCallback, useMemo } from 'react'
import { useSearchParams } from 'react-router'
import { TASK_STATUSES, type TaskFilters, type TaskStatus } from '../types'

export const PAGE_SIZES = [6, 12, 24] as const
const DEFAULT_SIZE = 12

function positiveInt(value: string | null, fallback: number): number {
  const n = Number(value)
  return Number.isInteger(n) && n > 0 ? n : fallback
}

/** Filters live in the URL: shareable links, and back/forward navigation just works. */
export function useTaskFilters() {
  const [params, setParams] = useSearchParams()

  const filters = useMemo<TaskFilters>(() => {
    const status = params.get('status')
    const size = positiveInt(params.get('size'), DEFAULT_SIZE)
    return {
      status: TASK_STATUSES.some((s) => s.value === status) ? (status as TaskStatus) : undefined,
      due_date_from: params.get('due_date_from') || undefined,
      due_date_to: params.get('due_date_to') || undefined,
      search: params.get('search') || undefined,
      page: positiveInt(params.get('page'), 1),
      size: (PAGE_SIZES as readonly number[]).includes(size) ? size : DEFAULT_SIZE,
    }
  }, [params])

  const setFilters = useCallback(
    (patch: Partial<TaskFilters>) => {
      setParams(
        (prev) => {
          const next = new URLSearchParams(prev)
          Object.entries(patch).forEach(([key, value]) => {
            if (value === undefined || value === '' || value === null) next.delete(key)
            else next.set(key, String(value))
          })
          // Changing any filter other than the page sends the user back to page 1.
          if (!('page' in patch)) next.delete('page')
          return next
        },
        { replace: true },
      )
    },
    [setParams],
  )

  const clearFilters = useCallback(() => setParams({}, { replace: true }), [setParams])

  return { filters, setFilters, clearFilters }
}
