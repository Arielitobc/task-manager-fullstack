import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router'
import { authApi } from '../api/auth'
import { ApiError } from '../api/client'

const MIN_PASSWORD = 8

export function RegisterPage() {
  const navigate = useNavigate()
  const [form, setForm] = useState({ full_name: '', email: '', password: '', confirm: '' })
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const update = (key: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [key]: e.target.value }))

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)
    if (form.password.length < MIN_PASSWORD) {
      setError(`Password must be at least ${MIN_PASSWORD} characters`)
      return
    }
    if (form.password !== form.confirm) {
      setError('Passwords do not match')
      return
    }
    setSubmitting(true)
    try {
      const user = await authApi.register({
        full_name: form.full_name.trim(),
        email: form.email.trim(),
        password: form.password,
      })
      navigate('/login', { state: { registered: user.email } })
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Unexpected error')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="auth-page">
      <form className="auth-card" onSubmit={handleSubmit}>
        <h1>Create account</h1>
        <label className="field">
          <span>Full name</span>
          <input required maxLength={120} value={form.full_name} onChange={update('full_name')} />
        </label>
        <label className="field">
          <span>Email</span>
          <input type="email" required autoComplete="email" value={form.email} onChange={update('email')} />
        </label>
        <label className="field">
          <span>Password</span>
          <input
            type="password"
            required
            minLength={MIN_PASSWORD}
            autoComplete="new-password"
            value={form.password}
            onChange={update('password')}
          />
        </label>
        <label className="field">
          <span>Confirm password</span>
          <input
            type="password"
            required
            autoComplete="new-password"
            value={form.confirm}
            onChange={update('confirm')}
          />
        </label>

        {error && (
          <p className="alert alert--error" role="alert">
            {error}
          </p>
        )}

        <button type="submit" className="btn btn--primary btn--block" disabled={submitting}>
          {submitting ? 'Creating…' : 'Create account'}
        </button>
        <p className="muted auth-card__footer">
          Already registered? <Link to="/login">Sign in</Link>
        </p>
      </form>
    </div>
  )
}
