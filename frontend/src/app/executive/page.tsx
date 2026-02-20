'use client'

import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { usePortfolioScores } from '@/hooks/useScoring'
import { gradeToColor, scoreToGrade } from '@/lib/scoring-utils'
import { api } from '@/lib/api'
import { BenchmarkRadar } from '@/components/charts/BenchmarkRadar'
import { TrendingUp, AlertTriangle, Shield } from 'lucide-react'

interface ExecutiveData {
  financialRisk: string
  doraCoverage: number
  doraRegistered: number
  doraTotal: number
  totalVendors: number
  tier1Count: number
  belowCCount: number
  topActions: { title: string; description: string; severity: string }[]
  previousScore: number | null
}

export default function ExecutivePage() {
  const { data: portfolio } = usePortfolioScores()
  const { data: executive } = useQuery({
    queryKey: ['executive-summary'],
    queryFn: () => api.get<ExecutiveData>('/api/v1/scoring/executive'),
  })

  const score = portfolio?.averageScore ?? 0
  const grade = scoreToGrade(score)
  const previousScore = executive?.previousScore ?? null
  const scoreDelta = previousScore !== null ? score - previousScore : null

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-bold text-[#1B3A5C]">Dashboard Executif</h1>

      {/* Hero score */}
      <Card className="border-2 border-[#2E75B6]">
        <CardContent className="flex items-center justify-center gap-8 p-8">
          <div className="text-center">
            <p className="text-7xl font-bold" style={{ color: gradeToColor(grade) }}>{score}</p>
            <p className="text-lg text-gray-500">Score Global Portfolio</p>
          </div>
          <div className="text-center">
            <Badge className="px-6 py-3 text-3xl" style={{ backgroundColor: gradeToColor(grade), color: '#fff' }}>
              {grade}
            </Badge>
            {scoreDelta !== null && (
              <div className={`mt-2 flex items-center justify-center gap-1 ${scoreDelta >= 0 ? 'text-[#27AE60]' : 'text-[#C0392B]'}`}>
                <TrendingUp className="h-4 w-4" />
                <span className="text-sm font-medium">{scoreDelta >= 0 ? '+' : ''}{scoreDelta} pts vs M-1</span>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-3 gap-6">
        {/* Financial risk */}
        <Card>
          <CardHeader><CardTitle>Risque Financier Estime</CardTitle></CardHeader>
          <CardContent className="text-center">
            <p className="text-3xl font-bold text-[#E67E22]">{executive?.financialRisk ?? '—'}</p>
            <p className="text-sm text-gray-500">Exposition basee sur scoring x valeur contrats</p>
          </CardContent>
        </Card>

        {/* DORA */}
        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2"><Shield className="h-4 w-4" /> Conformite DORA</CardTitle></CardHeader>
          <CardContent>
            <div className="mb-2 flex justify-between text-sm">
              <span>Couverture registre</span>
              <span className="font-bold">{executive?.doraCoverage ?? 0}%</span>
            </div>
            <div className="h-3 w-full overflow-hidden rounded-full bg-gray-200">
              <div className="h-full rounded-full bg-[#2E75B6]" style={{ width: `${executive?.doraCoverage ?? 0}%` }} />
            </div>
            <p className="mt-2 text-xs text-gray-500">
              {executive?.doraRegistered ?? 0} / {executive?.doraTotal ?? 0} prestataires TIC enregistres
            </p>
          </CardContent>
        </Card>

        {/* Vendors summary */}
        <Card>
          <CardHeader><CardTitle>Portfolio</CardTitle></CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex justify-between"><span>Total fournisseurs</span><span className="font-bold">{executive?.totalVendors ?? portfolio?.totalVendors ?? 0}</span></div>
            <div className="flex justify-between"><span>Tier 1 (critiques)</span><span className="font-bold">{executive?.tier1Count ?? 0}</span></div>
            <div className="flex justify-between"><span>Score &lt; C</span><span className="font-bold text-[#C0392B]">{executive?.belowCCount ?? 0}</span></div>
          </CardContent>
        </Card>
      </div>

      {/* Benchmark Radar */}
      <Card>
        <CardHeader>
          <CardTitle>Benchmark Sectoriel</CardTitle>
        </CardHeader>
        <CardContent>
          <BenchmarkRadar height={350} />
        </CardContent>
      </Card>

      {/* Top actions */}
      {(executive?.topActions ?? []).length > 0 && (
        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2"><AlertTriangle className="h-4 w-4 text-[#E67E22]" /> Top Actions Requises</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            {executive?.topActions.map((action, i) => {
              const bgColors: Record<string, string> = { critical: 'bg-red-50', high: 'bg-orange-50', medium: 'bg-yellow-50' }
              const textColors: Record<string, string> = { critical: 'text-[#C0392B]', high: 'text-[#E67E22]', medium: 'text-[#F39C12]' }
              return (
                <div key={i} className={`rounded-lg p-4 ${bgColors[action.severity] ?? 'bg-gray-50'}`}>
                  <p className={`font-semibold ${textColors[action.severity] ?? 'text-gray-700'}`}>
                    {i + 1}. {action.title}
                  </p>
                  <p className="text-sm text-gray-600">{action.description}</p>
                </div>
              )
            })}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
