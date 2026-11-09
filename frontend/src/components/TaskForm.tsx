import { useState, type FormEvent } from 'react'
import { TASK_STATUSES, type Task, type TaskInput, type TaskStatus, type User } from '../types'

interface TaskFormProps {
  initial?: Task
  users: User[]
  submitting: boolean
  error?: string | null
  onSubmit: (data: TaskInput) => void
  onCancel: () => void
}

const TITLE_MAX = 200

export function TaskForm({ initial, users, submitting, error, onSubmit, onCancel }: TaskFormProps) {
  const [title, setTitle] = useState(initial?.title ?? '')
  const [description, setDescription] = useState(initial?.description ?? '')
  const [status, setStatus] = useState<TaskStatus>(initial?.status ?? 'pending')
  const [dueDate, setDueDate] = useState(initial?.due_date ?? '')
  const [assigneeId, setAssigneeId] = useState(initial?.assignee_id?.toString() ?? '')
  const [titleError, setTitleError] = useState<string | null>(null)

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    const trimmed = title.trim()
    if (!trimmed) {
      setTitleError('Title is required')
      return
    }
    onSubmit({
      title: trimmed,
      description: description.trim(),
      status,
      due_date: dueDate || null,
      assignee_id: assigneeId ? Number(assigneeId) : null,
    })
  }

  return (
    <form className="form" onSubmit={handleSubmit} noValidate>
      <label className="field">
        <span>Title *</span>
        <input
          value={title}
          maxLength={TITLE_MAX}
          onChange={(e) => {
            setTitle(e.target.value)
            setTitleError(null)
          }}
          aria-invalid={Boolean(titleError)}
          aria-describedby={titleError ? 'title-error' : undefined}
          placeholder="What needs to be done?"
        />
        {titleError && (
          <small id="title-error" className="field__error">
            {titleError}
          </small>
        )}
      </label>

      <label className="field">
        <span>Description</span>
        <textarea
          rows={3}
          maxLength={5000}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />
      </label>

      <div className="form__row">
        <label className="field">
          <span>Status</span>
          <select value={status} onChange={(e) => setStatus(e.target.value as TaskStatus)}>
            {TASK_STATUSES.map((s) => (
              <option key={s.value} value={s.value}>
                {s.label}
              </option>
            ))}
          </select>
        </label>
        <label className="field">
          <span>Due date</span>
          <input type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)} />
        </label>
      </div>

      <label className="field">
        <span>Assignee</span>
        <select value={assigneeId} onChange={(e) => setAssigneeId(e.target.value)}>
          <option value="">Unassigned</option>
          {users.map((u) => (
            <option key={u.id} value={u.id}>
              {u.full_name} ({u.email})
            </option>
          ))}
        </select>
      </label>

      {error && (
        <p className="alert alert--error" role="alert">
          {error}
        </p>
      )}

      <div className="form__actions">
        <button type="button" className="btn btn--ghost" onClick={onCancel}>
          Cancel
        </button>
        <button type="submit" className="btn btn--primary" disabled={submitting}>
          {submitting ? 'Saving…' : initial ? 'Save changes' : 'Create task'}
        </button>
      </div>
    </form>
  )
}
