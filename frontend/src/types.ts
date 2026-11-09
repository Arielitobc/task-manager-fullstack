export type TaskStatus = 'pending' | 'in_progress' | 'completed'

export const TASK_STATUSES: { value: TaskStatus; label: string }[] = [
  { value: 'pending', label: 'Pending' },
  { value: 'in_progress', label: 'In progress' },
  { value: 'completed', label: 'Completed' },
]

export interface User {
  id: number
  email: string
  full_name: string
}

export interface Task {
  id: number
  title: string
  description: string
  status: TaskStatus
  due_date: string | null
  owner_id: number
  assignee_id: number | null
  completed_at: string | null
  created_at: string
  updated_at: string
}

export interface Page<T> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}

export interface TaskFilters {
  status?: TaskStatus
  due_date_from?: string
  due_date_to?: string
  search?: string
  page: number
  size: number
}

export interface TaskInput {
  title: string
  description: string
  status: TaskStatus
  due_date: string | null
  assignee_id: number | null
}
