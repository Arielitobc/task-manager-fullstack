import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { TaskForm } from './TaskForm'

const users = [{ id: 2, email: 'jane@demo.com', full_name: 'Jane' }]

describe('TaskForm', () => {
  it('requires a non-blank title', async () => {
    const onSubmit = vi.fn()
    render(<TaskForm users={users} submitting={false} onSubmit={onSubmit} onCancel={vi.fn()} />)
    await userEvent.type(screen.getByLabelText(/title/i), '   ')
    await userEvent.click(screen.getByRole('button', { name: /create task/i }))
    expect(screen.getByText('Title is required')).toBeInTheDocument()
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('submits a normalized payload', async () => {
    const onSubmit = vi.fn()
    render(<TaskForm users={users} submitting={false} onSubmit={onSubmit} onCancel={vi.fn()} />)
    await userEvent.type(screen.getByLabelText(/title/i), '  Ship it  ')
    await userEvent.selectOptions(screen.getByLabelText(/assignee/i), '2')
    await userEvent.selectOptions(screen.getByLabelText(/status/i), 'in_progress')
    await userEvent.click(screen.getByRole('button', { name: /create task/i }))
    expect(onSubmit).toHaveBeenCalledWith({
      title: 'Ship it',
      description: '',
      status: 'in_progress',
      due_date: null,
      assignee_id: 2,
    })
  })

  it('shows server errors', () => {
    render(
      <TaskForm users={users} submitting={false} error="Boom" onSubmit={vi.fn()} onCancel={vi.fn()} />,
    )
    expect(screen.getByRole('alert')).toHaveTextContent('Boom')
  })
})
