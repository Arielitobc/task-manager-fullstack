import { useEffect, useMemo, useState } from 'react'
import { ApiError } from '../api/client'
import { useAuth } from '../auth/useAuth'
import { Modal } from '../components/Modal'
import { Pagination } from '../components/Pagination'
import { TaskCard } from '../components/TaskCard'
import { TaskFiltersBar } from '../components/TaskFiltersBar'
import { TaskForm } from '../components/TaskForm'
import {
  useCompleteTask,
  useCreateTask,
  useDeleteTask,
  useTasks,
  useUpdateTask,
  useUsers,
} from '../hooks/useTasks'
import { useTaskFilters } from '../hooks/useTaskFilters'
import type { Task, TaskInput } from '../types'

type EditorState = { mode: 'create' } | { mode: 'edit'; task: Task } | null

const errorMessage = (err: unknown) =>
  err instanceof ApiError ? err.message : err ? 'Unexpected error' : null

export function TasksPage() {
  const { user } = useAuth()
  const { filters, setFilters, clearFilters } = useTaskFilters()
  const tasksQuery = useTasks(filters)
  const usersQuery = useUsers()

  const createTask = useCreateTask()
  const updateTask = useUpdateTask()
  const deleteTask = useDeleteTask()
  const completeTask = useCompleteTask()

  const [editor, setEditor] = useState<EditorState>(null)
  const [toDelete, setToDelete] = useState<Task | null>(null)
  const [notice, setNotice] = useState<string | null>(null)

  const usersById = useMemo(
    () => new Map((usersQuery.data ?? []).map((u) => [u.id, u])),
    [usersQuery.data],
  )

  const data = tasksQuery.data

  // After deleting the last task of the last page, step back to a page that exists.
  useEffect(() => {
    if (data && data.pages > 0 && filters.page > data.pages) setFilters({ page: data.pages })
  }, [data, filters.page, setFilters])

  useEffect(() => {
    if (!notice) return
    const id = setTimeout(() => setNotice(null), 3000)
    return () => clearTimeout(id)
  }, [notice])

  if (!user) return null

  const closeEditor = () => {
    setEditor(null)
    createTask.reset()
    updateTask.reset()
  }

  const handleSubmit = (input: TaskInput) => {
    if (editor?.mode === 'edit') {
      updateTask.mutate(
        { id: editor.task.id, data: input },
        { onSuccess: () => (closeEditor(), setNotice('Task updated')) },
      )
    } else {
      createTask.mutate(input, { onSuccess: () => (closeEditor(), setNotice('Task created')) })
    }
  }

  const handleDelete = () => {
    if (!toDelete) return
    deleteTask.mutate(toDelete.id, {
      onSuccess: () => {
        setToDelete(null)
        setNotice('Task deleted')
      },
    })
  }

  const actionError = errorMessage(completeTask.error)
  const busyId = completeTask.isPending ? completeTask.variables : undefined

  return (
    <>
      <div className="page-header">
        <div>
          <h1>My tasks</h1>
          <p className="muted">Tasks you created or that are assigned to you.</p>
        </div>
        <button type="button" className="btn btn--primary" onClick={() => setEditor({ mode: 'create' })}>
          + New task
        </button>
      </div>

      <TaskFiltersBar filters={filters} onChange={setFilters} onClear={clearFilters} />

      {notice && (
        <p className="alert alert--success" role="status">
          {notice}
        </p>
      )}
      {actionError && (
        <p className="alert alert--error" role="alert">
          {actionError}
        </p>
      )}

      {tasksQuery.isPending ? (
        <p className="muted page-center">Loading tasks…</p>
      ) : tasksQuery.isError ? (
        <div className="alert alert--error" role="alert">
          {errorMessage(tasksQuery.error)}{' '}
          <button type="button" className="btn btn--ghost btn--sm" onClick={() => tasksQuery.refetch()}>
            Retry
          </button>
        </div>
      ) : data && data.items.length === 0 ? (
        <div className="empty">
          <p>No tasks match these filters.</p>
          <button type="button" className="btn btn--ghost" onClick={() => setEditor({ mode: 'create' })}>
            Create a task
          </button>
        </div>
      ) : (
        data && (
          <>
            <div className={`grid ${tasksQuery.isFetching ? 'grid--loading' : ''}`}>
              {data.items.map((task) => (
                <TaskCard
                  key={task.id}
                  task={task}
                  currentUserId={user.id}
                  usersById={usersById}
                  busy={busyId === task.id}
                  onEdit={(t) => setEditor({ mode: 'edit', task: t })}
                  onDelete={setToDelete}
                  onComplete={(t) =>
                    completeTask.mutate(t.id, { onSuccess: () => setNotice('Task completed') })
                  }
                />
              ))}
            </div>
            <Pagination
              page={data.page}
              pages={data.pages}
              size={data.size}
              total={data.total}
              onPageChange={(page) => setFilters({ page })}
              onSizeChange={(size) => setFilters({ size })}
            />
          </>
        )
      )}

      {editor && (
        <Modal title={editor.mode === 'edit' ? 'Edit task' : 'New task'} onClose={closeEditor}>
          <TaskForm
            initial={editor.mode === 'edit' ? editor.task : undefined}
            users={usersQuery.data ?? []}
            submitting={createTask.isPending || updateTask.isPending}
            error={errorMessage(createTask.error ?? updateTask.error)}
            onSubmit={handleSubmit}
            onCancel={closeEditor}
          />
        </Modal>
      )}

      {toDelete && (
        <Modal title="Delete task" onClose={() => (setToDelete(null), deleteTask.reset())}>
          <p>
            Delete <strong>{toDelete.title}</strong>? This cannot be undone.
          </p>
          {deleteTask.error && (
            <p className="alert alert--error" role="alert">
              {errorMessage(deleteTask.error)}
            </p>
          )}
          <div className="form__actions">
            <button type="button" className="btn btn--ghost" onClick={() => setToDelete(null)}>
              Cancel
            </button>
            <button
              type="button"
              className="btn btn--danger"
              disabled={deleteTask.isPending}
              onClick={handleDelete}
            >
              {deleteTask.isPending ? 'Deleting…' : 'Delete'}
            </button>
          </div>
        </Modal>
      )}
    </>
  )
}
