import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { App } from './App'
import { tokenStorage } from './api/client'
import { mockFetch, renderWithProviders } from './test/utils'
import type { Task } from './types'

const me = { id: 1, email: 'admin@demo.com', full_name: 'Ada Admin' }
const baseTask: Task = {
  id: 1,
  title: 'Prepare demo',
  description: '',
  status: 'pending',
  due_date: null,
  owner_id: 1,
  assignee_id: null,
  completed_at: null,
  created_at: '',
  updated_at: '',
}

function page(items: Task[]) {
  return { items, total: items.length, page: 1, size: 12, pages: items.length ? 1 : 0 }
}

describe('App flows', () => {
  it('redirects to login, signs in and lists tasks', async () => {
    mockFetch({
      'POST /auth/login': () => ({ body: { access_token: 'tok', token_type: 'bearer' } }),
      'GET /auth/me': () => ({ body: me }),
      'GET /users': () => ({ body: [me] }),
      'GET /tasks': () => ({ body: page([baseTask]) }),
    })
    renderWithProviders(<App />)

    await userEvent.click(await screen.findByRole('button', { name: /use demo account/i }))
    await userEvent.click(screen.getByRole('button', { name: /^sign in$/i }))

    expect(await screen.findByText('Prepare demo')).toBeInTheDocument()
    expect(screen.getByText('Ada Admin')).toBeInTheDocument()
    expect(tokenStorage.get()).toBe('tok')
  })

  it('shows the API error on bad credentials', async () => {
    mockFetch({
      'POST /auth/login': () => ({ status: 401, body: { detail: 'Incorrect email or password' } }),
    })
    renderWithProviders(<App />, { route: '/login' })
    await userEvent.type(screen.getByLabelText(/email/i), 'x@x.com')
    await userEvent.type(screen.getByLabelText(/password/i), 'wrongpass')
    await userEvent.click(screen.getByRole('button', { name: /^sign in$/i }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Incorrect email or password')
  })

  it('creates, completes and deletes a task', async () => {
    tokenStorage.set('tok')
    let tasks: Task[] = []
    mockFetch({
      'GET /auth/me': () => ({ body: me }),
      'GET /users': () => ({ body: [me] }),
      'GET /tasks': () => ({ body: page(tasks) }),
      'POST /tasks': (_, init) => {
        const created = { ...baseTask, ...JSON.parse(String(init.body)), id: 7 }
        tasks = [created]
        return { status: 201, body: created }
      },
      'POST /tasks/7/complete': () => {
        tasks = [{ ...tasks[0], status: 'completed' }]
        return { body: tasks[0] }
      },
      'DELETE /tasks/7': () => {
        tasks = []
        return { status: 204 }
      },
    })
    renderWithProviders(<App />)

    expect(await screen.findByText(/no tasks match/i)).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: /new task/i }))
    await userEvent.type(screen.getByLabelText(/title/i), 'Write tests')
    await userEvent.click(screen.getByRole('button', { name: /create task/i }))
    expect(await screen.findByText('Write tests')).toBeInTheDocument()
    expect(screen.getByRole('status')).toHaveTextContent('Task created')

    await userEvent.click(screen.getByRole('button', { name: /complete/i }))
    await waitFor(() =>
      expect(screen.queryByRole('button', { name: /complete/i })).not.toBeInTheDocument(),
    )
    expect(screen.getByRole('status')).toHaveTextContent('Task completed')

    await userEvent.click(screen.getByRole('button', { name: /delete write tests/i }))
    const dialog = screen.getByRole('dialog')
    await userEvent.click(within(dialog).getByRole('button', { name: 'Delete' }))
    expect(await screen.findByText(/no tasks match/i)).toBeInTheDocument()
  })

  it('logs out when the token is rejected', async () => {
    tokenStorage.set('expired')
    mockFetch({ 'GET /auth/me': () => ({ status: 401, body: { detail: 'Invalid or expired token' } }) })
    renderWithProviders(<App />)
    expect(await screen.findByRole('heading', { name: /sign in/i })).toBeInTheDocument()
    expect(tokenStorage.get()).toBeNull()
  })
})
