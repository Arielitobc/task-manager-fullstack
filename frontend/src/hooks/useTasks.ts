import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { tasksApi, usersApi } from '../api/tasks'
import type { TaskFilters, TaskInput } from '../types'

const TASKS_KEY = ['tasks'] as const

export function useTasks(filters: TaskFilters) {
  return useQuery({
    queryKey: [...TASKS_KEY, filters],
    queryFn: () => tasksApi.list(filters),
    placeholderData: keepPreviousData, // no flicker while paginating / filtering
  })
}

export function useUsers() {
  return useQuery({ queryKey: ['users'], queryFn: usersApi.list, staleTime: 5 * 60_000 })
}

function useInvalidateTasks() {
  const queryClient = useQueryClient()
  return () => queryClient.invalidateQueries({ queryKey: TASKS_KEY })
}

export function useCreateTask() {
  const onSuccess = useInvalidateTasks()
  return useMutation({ mutationFn: (data: TaskInput) => tasksApi.create(data), onSuccess })
}

export function useUpdateTask() {
  const onSuccess = useInvalidateTasks()
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<TaskInput> }) =>
      tasksApi.update(id, data),
    onSuccess,
  })
}

export function useDeleteTask() {
  const onSuccess = useInvalidateTasks()
  return useMutation({ mutationFn: (id: number) => tasksApi.remove(id), onSuccess })
}

export function useCompleteTask() {
  const onSuccess = useInvalidateTasks()
  return useMutation({ mutationFn: (id: number) => tasksApi.complete(id), onSuccess })
}
