import { request } from './client'
import type { User } from '../types'

export const authApi = {
  login: (email: string, password: string) =>
    request<{ access_token: string; token_type: string }>('/auth/login', {
      method: 'POST',
      form: { username: email, password },
    }),
  register: (data: { email: string; full_name: string; password: string }) =>
    request<User>('/auth/register', { method: 'POST', json: data }),
  me: () => request<User>('/auth/me'),
}
