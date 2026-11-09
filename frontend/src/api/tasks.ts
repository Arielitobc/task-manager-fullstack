import { request } from './client'
import type { Page, Task, TaskFilters, TaskInput, User } from '../types'

export const tasksApi = {
  list: (filters: TaskFilters) =>
    request<Page<Task>>('/tasks', { query: { ...filters } }),
  create: (data: TaskInput) => request<Task>('/tasks', { method: 'POST', json: data }),
  update: (id: number, data: Partial<TaskInput>) =>
    request<Task>(`/tasks/${id}`, { method: 'PATCH', json: data }),
  remove: (id: number) => request<void>(`/tasks/${id}`, { method: 'DELETE' }),
  complete: (id: number) => request<Task>(`/tasks/${id}/complete`, { method: 'POST' }),
}

export const usersApi = {
  list: () => request<User[]>('/users'),
}
