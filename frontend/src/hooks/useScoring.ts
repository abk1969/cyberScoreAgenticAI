import { useQuery } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { API_ROUTES } from '@/lib/constants'
import type { VendorScore, DomainScore, ScoreHistoryEntry } from '@/types/scoring'

interface PortfolioScores {
  averageScore: number
  totalVendors: number
  improved: number
  degraded: number
  stable: number
  tier1Coverage: number
}

export function usePortfolioScores() {
  return useQuery({
    queryKey: ['portfolio-scores'],
    queryFn: () => api.get<PortfolioScores>(API_ROUTES.portfolioScores),
  })
}

export function useVendorScore(vendorId: string) {
  return useQuery({
    queryKey: ['vendor-score', vendorId],
    queryFn: () => api.get<VendorScore>(API_ROUTES.vendorScore(vendorId)),
    enabled: !!vendorId,
  })
}

export function useDomainScores(vendorId: string) {
  return useQuery({
    queryKey: ['domain-scores', vendorId],
    queryFn: () => api.get<DomainScore[]>(API_ROUTES.vendorDomainScores(vendorId)),
    enabled: !!vendorId,
  })
}

export function useScoreHistory(vendorId: string) {
  return useQuery({
    queryKey: ['score-history', vendorId],
    queryFn: () => api.get<ScoreHistoryEntry[]>(API_ROUTES.vendorScoreHistory(vendorId)),
    enabled: !!vendorId,
  })
}
