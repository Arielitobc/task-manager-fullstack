import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import { App } from '../App'
import { mockFetch, renderWithProviders } from '../test/utils'

async function fill(password: string, confirm = password) {
  await userEvent.type(screen.getByLabelText(/full name/i), 'New User')
  await userEvent.type(screen.getByLabelText(/^email/i), 'new@demo.com')
  await userEvent.type(screen.getByLabelText(/^password/i), password)
  await userEvent.type(screen.getByLabelText(/confirm/i), confirm)
  await userEvent.click(screen.getByRole('button', { name: /create account/i }))
}

describe('RegisterPage', () => {
  it('validates passwords on the client', async () => {
    renderWithProviders(<App />, { route: '/register' })
    await fill('short')
    expect(screen.getByRole('alert')).toHaveTextContent(/at least 8/)
  })

  it('validates the confirmation', async () => {
    renderWithProviders(<App />, { route: '/register' })
    await fill('Secret123!', 'Different1!')
    expect(screen.getByRole('alert')).toHaveTextContent(/do not match/)
  })

  it('registers and redirects to login with the email prefilled', async () => {
    mockFetch({
      'POST /auth/register': () => ({
        status: 201,
        body: { id: 9, email: 'new@demo.com', full_name: 'New User' },
      }),
    })
    renderWithProviders(<App />, { route: '/register' })
    await fill('Secret123!')
    expect(await screen.findByText(/account created/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/email/i)).toHaveValue('new@demo.com')
  })

  it('shows a conflict error from the API', async () => {
    mockFetch({
      'POST /auth/register': () => ({
        status: 409,
        body: { detail: 'A user with this email already exists' },
      }),
    })
    renderWithProviders(<App />, { route: '/register' })
    await fill('Secret123!')
    expect(await screen.findByRole('alert')).toHaveTextContent(/already exists/)
  })
})
