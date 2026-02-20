import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'

interface Sector {
  key: string
  label: string
  global_avg: number
  global_p50: number
}

interface DomainComparison {
  code: string
  name: string
  vendor_score?: number
  portfolio_avg?: number
  sector_avg: number
  delta: number
  status: 'above' | 'below'
}

interface VendorBenchmark {
  sector: string
  sector_label: string
  vendor_id: string
  vendor_score: number
  sector_avg: number
  delta: number
  percentile: string
  percentile_label: string
  domain_comparison: DomainComparison[]
}

interface PortfolioBenchmark {
  sector: string
  sector_label: string
  portfolio_avg_score: number
  sector_avg: number
  delta: number
  sector_p25: number
  sector_p50: number
  sector_p75: number
  sector_p90: number
  domain_comparison: DomainComparison[]
}

export function useSectorBenchmark() {
  return useQuery({
    queryKey: ['benchmark-sectors'],
    queryFn: () => api.get<{ sectors: Sector[] }>('/api/v1/benchmark/sectors'),
  })
}

export function useVendorBenchmark(vendorId: string, sector: string) {
  return useQuery({
    queryKey: ['benchmark-vendor', vendorId, sector],
    queryFn: () =>
      api.get<VendorBenchmark>(`/api/v1/benchmark/vendors/${vendorId}?sector=${sector}`),
    enabled: !!vendorId && !!sector,
  })
}

export function usePortfolioBenchmark(sector: string) {
  return useQuery({
    queryKey: ['benchmark-portfolio', sector],
    queryFn: () =>
      api.get<PortfolioBenchmark>(`/api/v1/benchmark/portfolio?sector=${sector}`),
    enabled: !!sector,
  })
}
