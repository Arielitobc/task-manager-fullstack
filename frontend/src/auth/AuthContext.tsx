import { useQuery, useQueryClient } from '@tanstack/react-query'
import { createContext, useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import { authApi } from '../api/auth'
import { onUnauthorized, tokenStorage } from '../api/client'
import type { User } from '../types'

export interface AuthContextValue {
  user: User | null
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
}

// eslint-disable-next-line react-refresh/only-export-components
export const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()
  const [token, setToken] = useState<string | null>(() => tokenStorage.get())

  const logout = useCallback(() => {
    tokenStorage.clear()
    setToken(null)
    queryClient.clear()
  }, [queryClient])

  useEffect(() => {
    onUnauthorized(logout)
    return () => onUnauthorized(null)
  }, [logout])

  const meQuery = useQuery({
    queryKey: ['me', token],
    queryFn: authApi.me,
    enabled: Boolean(token),
    staleTime: Infinity,
    retry: false,
  })

  const login = useCallback(async (email: string, password: string) => {
    const { access_token } = await authApi.login(email, password)
    tokenStorage.set(access_token)
    setToken(access_token)
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      user: token ? (meQuery.data ?? null) : null,
      isLoading: Boolean(token) && meQuery.isPending,
      login,
      logout,
    }),
    [token, meQuery.data, meQuery.isPending, login, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
