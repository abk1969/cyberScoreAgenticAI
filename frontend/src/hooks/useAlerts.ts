import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { API_ROUTES } from '@/lib/constants'
import type { AlertItem } from '@/types/api'

export function useAlerts() {
  return useQuery({
    queryKey: ['alerts'],
    queryFn: () => api.get<AlertItem[]>(API_ROUTES.alerts),
  })
}

export function useMarkAlertRead() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) => api.post(API_ROUTES.alertMarkRead(id)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] })
    },
  })
}
