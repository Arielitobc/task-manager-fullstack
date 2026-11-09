import { Outlet } from 'react-router'
import { useAuth } from '../auth/useAuth'

export function Layout() {
  const { user, logout } = useAuth()
  return (
    <div className="app">
      <header className="topbar">
        <div className="topbar__inner">
          <span className="brand">
            <span className="brand__mark" aria-hidden="true">
              ✓
            </span>
            Task Manager
          </span>
          {user && (
            <div className="topbar__user">
              <span className="topbar__name" title={user.email}>
                {user.full_name}
              </span>
              <button type="button" className="btn btn--ghost btn--sm" onClick={logout}>
                Log out
              </button>
            </div>
          )}
        </div>
      </header>
      <main className="container">
        <Outlet />
      </main>
    </div>
  )
}
