import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { App } from '../App'
import { tokenStorage } from '../api/client'
import { mockFetch, renderWithProviders } from '../test/utils'
import type { Task } from '../types'

const me = { id: 1, email: 'a@demo.com', full_name: 'Ada' }
const mkTask = (id: number): Task => ({
  id,
  title: `Task ${id}`,
  description: '',
  status: 'pending',
  due_date: null,
  owner_id: 1,
  assignee_id: null,
  completed_at: null,
  created_at: '',
  updated_at: '',
})

describe('TasksPage filters and pagination', () => {
  it('sends filters and page to the API and edits a task', async () => {
    tokenStorage.set('tok')
    const queries: URLSearchParams[] = []
    const fetchSpy = mockFetch({
      'GET /auth/me': () => ({ body: me }),
      'GET /users': () => ({ body: [me] }),
      'GET /tasks': (url) => {
        queries.push(url.searchParams)
        return { body: { items: [mkTask(1)], total: 30, page: Number(url.searchParams.get('page')), size: 12, pages: 3 } }
      },
      'PATCH /tasks/1': (_, init) => ({ body: { ...mkTask(1), ...JSON.parse(String(init.body)) } }),
    })
    renderWithProviders(<App />, { route: '/?status=pending' })

    expect(await screen.findByText('Task 1')).toBeInTheDocument()
    expect(queries.at(-1)?.get('status')).toBe('pending')

    await userEvent.click(screen.getByRole('button', { name: /next/i }))
    await waitFor(() => expect(queries.at(-1)?.get('page')).toBe('2'))

    // Changing a filter goes back to page 1
    await userEvent.selectOptions(screen.getByLabelText('Status', { selector: 'select' }), 'completed')
    await waitFor(() => expect(queries.at(-1)?.get('status')).toBe('completed'))
    expect(queries.at(-1)?.get('page')).toBe('1')

    await userEvent.type(screen.getByLabelText(/search/i), 'demo')
    await waitFor(() => expect(queries.at(-1)?.get('search')).toBe('demo'))

    await userEvent.click(screen.getByRole('button', { name: /clear filters/i }))
    await waitFor(() => expect(queries.at(-1)?.get('status')).toBeNull())

    await userEvent.click(screen.getByRole('button', { name: 'Edit' }))
    const title = screen.getByLabelText(/title/i)
    await userEvent.clear(title)
    await userEvent.type(title, 'Renamed')
    await userEvent.click(screen.getByRole('button', { name: /save changes/i }))
    expect(await screen.findByText('Task updated')).toBeInTheDocument()
    const patch = fetchSpy.mock.calls.find(([, init]) => init?.method === 'PATCH')
    expect(JSON.parse(String(patch?.[1]?.body)).title).toBe('Renamed')
  })

  it('shows an error with retry when the API fails', async () => {
    tokenStorage.set('tok')
    mockFetch({
      'GET /auth/me': () => ({ body: me }),
      'GET /users': () => ({ body: [me] }),
      'GET /tasks': () => ({ status: 500, body: { detail: 'Internal error' } }),
    })
    renderWithProviders(<App />)
    expect(await screen.findByRole('button', { name: /retry/i })).toBeInTheDocument()
  })
})
