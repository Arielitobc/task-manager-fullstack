import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import type { Task, User } from '../types'
import { TaskCard } from './TaskCard'

const users = new Map<number, User>([
  [1, { id: 1, email: 'a@x.com', full_name: 'Ada' }],
  [2, { id: 2, email: 'j@x.com', full_name: 'John' }],
])

const task: Task = {
  id: 10,
  title: 'Fix bug',
  description: 'Details',
  status: 'pending',
  due_date: '2000-01-01',
  owner_id: 1,
  assignee_id: 2,
  completed_at: null,
  created_at: '',
  updated_at: '',
}

function renderCard(currentUserId: number, overrides: Partial<Task> = {}) {
  const handlers = { onEdit: vi.fn(), onDelete: vi.fn(), onComplete: vi.fn() }
  render(
    <TaskCard
      task={{ ...task, ...overrides }}
      currentUserId={currentUserId}
      usersById={users}
      busy={false}
      {...handlers}
    />,
  )
  return handlers
}

describe('TaskCard', () => {
  it('owner can edit, delete and complete; overdue is highlighted', async () => {
    const h = renderCard(1)
    expect(screen.getByText(/overdue/)).toBeInTheDocument()
    expect(screen.getByText('John')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Edit' }))
    await userEvent.click(screen.getByRole('button', { name: /delete fix bug/i }))
    await userEvent.click(screen.getByRole('button', { name: /complete/i }))
    expect(h.onEdit).toHaveBeenCalled()
    expect(h.onDelete).toHaveBeenCalled()
    expect(h.onComplete).toHaveBeenCalled()
  })

  it('assignee can only complete and sees the owner', () => {
    renderCard(2)
    expect(screen.queryByRole('button', { name: 'Edit' })).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: /complete/i })).toBeInTheDocument()
    expect(screen.getByText('Ada')).toBeInTheDocument()
    expect(screen.getByText('You')).toBeInTheDocument()
  })

  it('completed tasks hide the complete button and are not overdue', () => {
    renderCard(1, { status: 'completed' })
    expect(screen.queryByRole('button', { name: /complete/i })).not.toBeInTheDocument()
    expect(screen.queryByText(/overdue/)).not.toBeInTheDocument()
  })
})
