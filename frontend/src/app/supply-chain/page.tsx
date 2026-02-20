'use client'

import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { SupplyChainGraph } from '@/components/charts/SupplyChainGraph'
import { api } from '@/lib/api'
import { Network, AlertTriangle, Shield, Activity } from 'lucide-react'
import type { SupplyChainGraphData } from '@/types/chart'

interface ConcentrationRisk {
  provider_name: string
  dependent_count: number
  percentage: number
  risk_level: 'low' | 'medium' | 'high' | 'critical'
}

interface ConcentrationResponse {
  threshold: number
  risks: ConcentrationRisk[]
  total_vendors: number
  total_providers: number
}

const RISK_COLORS: Record<string, string> = {
  critical: 'bg-red-100 text-red-800 border-red-200',
  high: 'bg-orange-100 text-orange-800 border-orange-200',
  medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  low: 'bg-green-100 text-green-800 border-green-200',
}

const RISK_LABELS: Record<string, string> = {
  critical: 'Critique',
  high: 'Eleve',
  medium: 'Moyen',
  low: 'Faible',
}

export default function SupplyChainPage() {
  const { data: graphData } = useQuery({
    queryKey: ['supply-chain-graph'],
    queryFn: () => api.get<SupplyChainGraphData>('/api/v1/supply-chain/graph'),
  })

  const { data: concentration } = useQuery({
    queryKey: ['supply-chain-concentration'],
    queryFn: () => api.get<ConcentrationResponse>('/api/v1/supply-chain/concentration'),
  })

  const highRisks = concentration?.risks.filter(
    (r) => r.risk_level === 'high' || r.risk_level === 'critical'
  ) ?? []

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-[#1B3A5C]">
        <Network className="mr-2 inline h-6 w-6" />
        Cartographie Supply Chain
      </h1>

      {/* Summary cards */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
        <Card>
          <CardContent className="flex items-center gap-3 pt-6">
            <div className="rounded-lg bg-blue-100 p-2">
              <Network className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Fournisseurs</p>
              <p className="text-2xl font-bold text-[#1B3A5C]">
                {concentration?.total_vendors ?? '-'}
              </p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-3 pt-6">
            <div className="rounded-lg bg-purple-100 p-2">
              <Activity className="h-5 w-5 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Providers detectes</p>
              <p className="text-2xl font-bold text-[#1B3A5C]">
                {concentration?.total_providers ?? '-'}
              </p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-3 pt-6">
            <div className="rounded-lg bg-orange-100 p-2">
              <AlertTriangle className="h-5 w-5 text-orange-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Risques concentration</p>
              <p className="text-2xl font-bold text-orange-600">
                {highRisks.length}
              </p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-3 pt-6">
            <div className="rounded-lg bg-green-100 p-2">
              <Shield className="h-5 w-5 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Seuil DORA</p>
              <p className="text-2xl font-bold text-[#1B3A5C]">
                {concentration ? `${(concentration.threshold * 100).toFixed(0)}%` : '-'}
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Concentration risk cards */}
      {concentration && concentration.risks.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Risques de concentration par fournisseur</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
              {concentration.risks.map((risk) => (
                <div
                  key={risk.provider_name}
                  className={`rounded-lg border p-4 ${RISK_COLORS[risk.risk_level] ?? RISK_COLORS.low}`}
                >
                  <div className="flex items-center justify-between">
                    <h4 className="font-semibold">{risk.provider_name}</h4>
                    <span className="rounded-full px-2 py-0.5 text-xs font-medium">
                      {RISK_LABELS[risk.risk_level] ?? risk.risk_level}
                    </span>
                  </div>
                  <div className="mt-2 flex items-baseline gap-2">
                    <span className="text-2xl font-bold">
                      {(risk.percentage * 100).toFixed(0)}%
                    </span>
                    <span className="text-sm">
                      ({risk.dependent_count} fournisseurs)
                    </span>
                  </div>
                  <div className="mt-2 h-2 w-full rounded-full bg-white/50">
                    <div
                      className="h-2 rounded-full bg-current opacity-60"
                      style={{ width: `${Math.min(risk.percentage * 100, 100)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Dependency graph */}
      <Card>
        <CardHeader>
          <CardTitle>Graphe de dependances N-tiers</CardTitle>
        </CardHeader>
        <CardContent>
          {graphData && graphData.nodes.length > 0 ? (
            <SupplyChainGraph data={graphData} width={900} height={600} />
          ) : (
            <div className="flex flex-col items-center justify-center py-20">
              <Network className="mb-4 h-16 w-16 text-gray-300" />
              <h3 className="text-lg font-semibold text-gray-400">
                Aucune donnee de supply chain disponible
              </h3>
              <p className="mt-2 text-sm text-gray-400">
                Lancez un scan Nth-Party pour generer le graphe de dependances.
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
