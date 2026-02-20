import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'

interface IntegrationStatus {
  type: string
  enabled: boolean
  configured: boolean
  last_test_success: boolean | null
  last_test_message: string | null
}

interface IntegrationListResponse {
  integrations: IntegrationStatus[]
}

interface IntegrationConfig {
  type: string
  enabled: boolean
  url: string
  token: string
  username: string
  password: string
}

interface IntegrationTestResult {
  type: string
  success: boolean
  message: string
}

export function useIntegrations() {
  return useQuery({
    queryKey: ['integrations'],
    queryFn: () => api.get<IntegrationListResponse>('/api/v1/integrations/'),
  })
}

export function useConfigureIntegration() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ type, config }: { type: string; config: IntegrationConfig }) =>
      api.put<IntegrationStatus>(`/api/v1/integrations/${type}`, config),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['integrations'] })
    },
  })
}

export function useTestIntegration() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (type: string) =>
      api.post<IntegrationTestResult>(`/api/v1/integrations/${type}/test`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['integrations'] })
    },
  })
}
