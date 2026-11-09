import type { Task, User } from '../types'
import { formatDate, isOverdue } from '../utils/dates'
import { StatusBadge } from './StatusBadge'

interface TaskCardProps {
  task: Task
  currentUserId: number
  usersById: Map<number, User>
  busy: boolean
  onEdit: (task: Task) => void
  onDelete: (task: Task) => void
  onComplete: (task: Task) => void
}

export function TaskCard({
  task,
  currentUserId,
  usersById,
  busy,
  onEdit,
  onDelete,
  onComplete,
}: TaskCardProps) {
  const isOwner = task.owner_id === currentUserId
  const overdue = isOverdue(task.due_date, task.status)
  const assignee = task.assignee_id ? usersById.get(task.assignee_id) : undefined
  const owner = usersById.get(task.owner_id)

  return (
    <article className={`card ${task.status === 'completed' ? 'card--done' : ''}`}>
      <header className="card__header">
        <h3 className="card__title">{task.title}</h3>
        <StatusBadge status={task.status} />
      </header>

      {task.description && <p className="card__description">{task.description}</p>}

      <dl className="card__meta">
        <div>
          <dt>Due</dt>
          <dd className={overdue ? 'text-danger' : undefined}>
            {task.due_date ? formatDate(task.due_date) : '—'}
            {overdue && ' · overdue'}
          </dd>
        </div>
        <div>
          <dt>Assignee</dt>
          <dd>{assignee ? (assignee.id === currentUserId ? 'You' : assignee.full_name) : '—'}</dd>
        </div>
        {!isOwner && (
          <div>
            <dt>Owner</dt>
            <dd>{owner?.full_name ?? `User #${task.owner_id}`}</dd>
          </div>
        )}
      </dl>

      <footer className="card__actions">
        {task.status !== 'completed' && (
          <button
            type="button"
            className="btn btn--success btn--sm"
            disabled={busy}
            onClick={() => onComplete(task)}
          >
            ✓ Complete
          </button>
        )}
        {isOwner && (
          <>
            <button
              type="button"
              className="btn btn--ghost btn--sm"
              disabled={busy}
              onClick={() => onEdit(task)}
            >
              Edit
            </button>
            <button
              type="button"
              className="btn btn--danger-ghost btn--sm"
              disabled={busy}
              onClick={() => onDelete(task)}
              aria-label={`Delete ${task.title}`}
            >
              Delete
            </button>
          </>
        )}
      </footer>
    </article>
  )
}
