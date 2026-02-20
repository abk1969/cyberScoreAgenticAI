import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { API_ROUTES } from '@/lib/constants'

export interface Dispute {
  id: string
  vendor_id: string
  finding_id: string
  status: 'open' | 'in_review' | 'resolved' | 'rejected'
  evidence_url: string | null
  requester_email: string
  admin_notes: string | null
  sla_deadline: string
  created_at: string
  resolved_at: string | null
}

export interface Remediation {
  id: string
  vendor_id: string
  title: string
  description: string
  priority: 'critical' | 'high' | 'medium' | 'low'
  deadline: string
  status: 'pending' | 'in_progress' | 'completed' | 'overdue'
  assigned_to: string | null
  created_at: string
  updated_at: string
}

export function useDisputes(vendorId?: string) {
  const url = vendorId
    ? `${API_ROUTES.vrmDisputes}?vendor_id=${vendorId}`
    : API_ROUTES.vrmDisputes
  return useQuery({
    queryKey: ['disputes', vendorId],
    queryFn: () => api.get<Dispute[]>(url),
  })
}

export function useCreateDispute(vendorId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: { finding_id: string; evidence_url?: string; requester_email: string }) =>
      api.post<Dispute>(API_ROUTES.vrmDisputesByVendor(vendorId), data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['disputes'] })
      queryClient.invalidateQueries({ queryKey: ['disputes', vendorId] })
    },
  })
}

export function useResolveDispute() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ disputeId, data }: { disputeId: string; data: { status: string; admin_notes?: string } }) =>
      api.put<Dispute>(API_ROUTES.vrmDispute(disputeId), data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['disputes'] })
    },
  })
}

export function useRemediations(vendorId: string) {
  return useQuery({
    queryKey: ['remediations', vendorId],
    queryFn: () => api.get<Remediation[]>(API_ROUTES.vrmRemediations(vendorId)),
    enabled: !!vendorId,
  })
}

export function useCreateRemediation(vendorId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: {
      title: string
      description: string
      priority: string
      deadline: string
      assigned_to?: string
    }) => api.post<Remediation>(API_ROUTES.vrmRemediations(vendorId), data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['remediations', vendorId] })
    },
  })
}
