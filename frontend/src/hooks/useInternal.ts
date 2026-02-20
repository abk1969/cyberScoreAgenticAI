import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'

// ── Types ──────────────────────────────────────────────────────────────

interface InternalScore {
  id: string
  score: number
  grade: string
  findings_count: number
  category_scores: Record<string, number>
  created_at: string
}

interface InternalFinding {
  id: string
  scan_id: string
  category: string
  title: string
  description: string | null
  severity: string
  recommendation: string | null
  status: string
  detected_at: string
}

interface InternalScanResponse {
  id: string
  scan_type: string
  target: string
  score: number
  grade: string
  findings_count: number
  scan_data: Record<string, unknown>
  created_at: string
}

interface SecurityControl {
  id: string
  reference: string
  title: string
  description: string | null
  domain: string
  status: string
  owner: string | null
  evidence_url: string | null
  last_assessed: string | null
  frameworks: string[]
}

interface MaturityScore {
  overall_maturity: number
  domains: Record<string, { average_level: number; assessment_count: number }>
  domain_count: number
}

interface FrameworkCoverage {
  framework: string
  total_controls: number
  implemented: number
  partial: number
  not_implemented: number
  coverage_percent: number
}

interface HeatmapCell {
  domain: string
  framework: string
  coverage_percent: number
  status: string
}

// ── AD Rating ──────────────────────────────────────────────────────────

export function useADScore() {
  return useQuery({
    queryKey: ['internal', 'ad', 'score'],
    queryFn: () => api.get<InternalScore>('/api/v1/internal/ad/score'),
  })
}

export function useADHistory(limit = 30) {
  return useQuery({
    queryKey: ['internal', 'ad', 'history', limit],
    queryFn: () => api.get<InternalScore[]>(`/api/v1/internal/ad/history?limit=${limit}`),
  })
}

export function useADFindings(severity?: string) {
  const params = severity ? `?severity=${severity}` : ''
  return useQuery({
    queryKey: ['internal', 'ad', 'findings', severity],
    queryFn: () => api.get<InternalFinding[]>(`/api/v1/internal/ad/findings${params}`),
  })
}

export function useScanAD() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (config: { target: string; config?: Record<string, unknown> }) =>
      api.post<InternalScanResponse>('/api/v1/internal/ad/scan', {
        scan_type: 'ad',
        ...config,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['internal', 'ad'] })
    },
  })
}

// ── M365 Rating ────────────────────────────────────────────────────────

export function useM365Score() {
  return useQuery({
    queryKey: ['internal', 'm365', 'score'],
    queryFn: () => api.get<InternalScore>('/api/v1/internal/m365/score'),
  })
}

export function useM365Findings(severity?: string) {
  const params = severity ? `?severity=${severity}` : ''
  return useQuery({
    queryKey: ['internal', 'm365', 'findings', severity],
    queryFn: () => api.get<InternalFinding[]>(`/api/v1/internal/m365/findings${params}`),
  })
}

export function useScanM365() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (config: { target: string; config?: Record<string, unknown> }) =>
      api.post<InternalScanResponse>('/api/v1/internal/m365/scan', {
        scan_type: 'm365',
        ...config,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['internal', 'm365'] })
    },
  })
}

// ── GRC / PSSI ─────────────────────────────────────────────────────────

export function useGRCControls(filters?: {
  domain?: string
  status?: string
  framework?: string
}) {
  const params = new URLSearchParams()
  if (filters?.domain) params.set('domain', filters.domain)
  if (filters?.status) params.set('status', filters.status)
  if (filters?.framework) params.set('framework', filters.framework)
  const qs = params.toString()

  return useQuery({
    queryKey: ['internal', 'grc', 'controls', filters],
    queryFn: () =>
      api.get<SecurityControl[]>(`/api/v1/internal/grc/controls${qs ? `?${qs}` : ''}`),
  })
}

export function useGRCMaturity() {
  return useQuery({
    queryKey: ['internal', 'grc', 'maturity'],
    queryFn: () => api.get<MaturityScore>('/api/v1/internal/grc/maturity'),
  })
}

export function useFrameworkCoverage(framework: string) {
  return useQuery({
    queryKey: ['internal', 'grc', 'coverage', framework],
    queryFn: () =>
      api.get<FrameworkCoverage>(`/api/v1/internal/grc/coverage/${framework}`),
    enabled: !!framework,
  })
}

export function useGRCHeatmap() {
  return useQuery({
    queryKey: ['internal', 'grc', 'heatmap'],
    queryFn: () => api.get<HeatmapCell[]>('/api/v1/internal/grc/heatmap'),
  })
}

export function useUpdateControl() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      controlId,
      update,
    }: {
      controlId: string
      update: { status?: string; owner?: string; evidence_url?: string }
    }) => api.put<SecurityControl>(`/api/v1/internal/grc/controls/${controlId}`, update),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['internal', 'grc'] })
    },
  })
}
