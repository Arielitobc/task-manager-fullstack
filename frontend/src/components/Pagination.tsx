import { PAGE_SIZES } from '../hooks/useTaskFilters'

interface Props {
  page: number
  pages: number
  size: number
  total: number
  onPageChange: (page: number) => void
  onSizeChange: (size: number) => void
}

export function Pagination({ page, pages, size, total, onPageChange, onSizeChange }: Props) {
  const from = total === 0 ? 0 : (page - 1) * size + 1
  const to = Math.min(page * size, total)

  return (
    <nav className="pagination" aria-label="Pagination">
      <span className="muted">
        {from}–{to} of {total}
      </span>
      <div className="pagination__controls">
        <button
          type="button"
          className="btn btn--ghost btn--sm"
          disabled={page <= 1}
          onClick={() => onPageChange(page - 1)}
        >
          ← Prev
        </button>
        <span aria-current="page">
          Page {Math.min(page, Math.max(pages, 1))} of {Math.max(pages, 1)}
        </span>
        <button
          type="button"
          className="btn btn--ghost btn--sm"
          disabled={page >= pages}
          onClick={() => onPageChange(page + 1)}
        >
          Next →
        </button>
      </div>
      <label className="pagination__size">
        <span className="muted">Per page</span>
        <select value={size} onChange={(e) => onSizeChange(Number(e.target.value))}>
          {PAGE_SIZES.map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </label>
    </nav>
  )
}
