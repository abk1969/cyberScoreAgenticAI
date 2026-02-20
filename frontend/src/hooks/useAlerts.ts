import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { API_ROUTES } from '@/lib/constants'
import type { AlertItem } from '@/types/api'

interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  pages: number
}

export function useAlerts() {
  return useQuery({
    queryKey: ['alerts'],
    queryFn: async () => {
      const res = await api.get<PaginatedResponse<AlertItem>>(API_ROUTES.alerts)
      return res.items
    },
  })
}

export function useMarkAlertRead() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => api.patch(API_ROUTES.alertMarkRead(id), {}),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] })
    },
  })
}
