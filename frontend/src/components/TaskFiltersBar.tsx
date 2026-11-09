import { useEffect, useState } from 'react'
import { useDebouncedValue } from '../hooks/useDebouncedValue'
import { TASK_STATUSES, type TaskFilters, type TaskStatus } from '../types'

interface Props {
  filters: TaskFilters
  onChange: (patch: Partial<TaskFilters>) => void
  onClear: () => void
}

export function TaskFiltersBar({ filters, onChange, onClear }: Props) {
  const [search, setSearch] = useState(filters.search ?? '')
  const debouncedSearch = useDebouncedValue(search)

  useEffect(() => {
    if ((debouncedSearch || undefined) !== filters.search) onChange({ search: debouncedSearch })
    // Only react to the user typing, not to filters.search changing from the URL.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debouncedSearch])

  const hasFilters = Boolean(
    filters.status || filters.due_date_from || filters.due_date_to || filters.search,
  )

  return (
    <section className="filters" aria-label="Filters">
      <label className="field field--grow">
        <span>Search</span>
        <input
          type="search"
          placeholder="Title or description"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </label>
      <label className="field">
        <span>Status</span>
        <select
          value={filters.status ?? ''}
          onChange={(e) => onChange({ status: (e.target.value || undefined) as TaskStatus })}
        >
          <option value="">All</option>
          {TASK_STATUSES.map((s) => (
            <option key={s.value} value={s.value}>
              {s.label}
            </option>
          ))}
        </select>
      </label>
      <label className="field">
        <span>Due from</span>
        <input
          type="date"
          value={filters.due_date_from ?? ''}
          max={filters.due_date_to}
          onChange={(e) => onChange({ due_date_from: e.target.value })}
        />
      </label>
      <label className="field">
        <span>Due to</span>
        <input
          type="date"
          value={filters.due_date_to ?? ''}
          min={filters.due_date_from}
          onChange={(e) => onChange({ due_date_to: e.target.value })}
        />
      </label>
      {hasFilters && (
        <button
          type="button"
          className="btn btn--ghost filters__clear"
          onClick={() => {
            setSearch('')
            onClear()
          }}
        >
          Clear filters
        </button>
      )}
    </section>
  )
}
