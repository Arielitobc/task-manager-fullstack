import { Navigate, Outlet, useLocation } from 'react-router'
import { useAuth } from './useAuth'

export function ProtectedRoute() {
  const { user, isLoading } = useAuth()
  const location = useLocation()

  if (isLoading) return <div className="page-center muted">Loading…</div>
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />
  return <Outlet />
}

export function PublicOnlyRoute() {
  const { user, isLoading } = useAuth()
  if (isLoading) return <div className="page-center muted">Loading…</div>
  return user ? <Navigate to="/" replace /> : <Outlet />
}
