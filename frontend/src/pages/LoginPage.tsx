import { useState, type FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router'
import { ApiError } from '../api/client'
import { useAuth } from '../auth/useAuth'

const DEMO = { email: 'admin@demo.com', password: 'Demo1234!' }

export function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const registeredEmail = (location.state as { registered?: string } | null)?.registered
  const [email, setEmail] = useState(registeredEmail ?? '')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await login(email.trim(), password)
      const from = (location.state as { from?: string } | null)?.from ?? '/'
      navigate(from, { replace: true })
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Unexpected error')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="auth-page">
      <form className="auth-card" onSubmit={handleSubmit}>
        <h1>Sign in</h1>
        <p className="muted">Manage and share your tasks.</p>

        {registeredEmail && (
          <p className="alert alert--success" role="status">
            Account created. You can sign in now.
          </p>
        )}

        <label className="field">
          <span>Email</span>
          <input
            type="email"
            autoComplete="username"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </label>
        <label className="field">
          <span>Password</span>
          <input
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>

        {error && (
          <p className="alert alert--error" role="alert">
            {error}
          </p>
        )}

        <button type="submit" className="btn btn--primary btn--block" disabled={submitting}>
          {submitting ? 'Signing in…' : 'Sign in'}
        </button>

        <div className="demo-hint">
          <span className="muted">
            Demo: <code>{DEMO.email}</code> / <code>{DEMO.password}</code>
          </span>
          <button
            type="button"
            className="btn btn--ghost btn--sm"
            onClick={() => {
              setEmail(DEMO.email)
              setPassword(DEMO.password)
            }}
          >
            Use demo account
          </button>
        </div>

        <p className="muted auth-card__footer">
          No account? <Link to="/register">Create one</Link>
        </p>
      </form>
    </div>
  )
}
