'use client'

import { useQuery } from '@tanstack/react-query'
import { ScoreGauge } from '@/components/charts/ScoreGauge'
import { GradeDistribution } from '@/components/charts/GradeDistribution'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { usePortfolioScores } from '@/hooks/useScoring'
import { useVendors } from '@/hooks/useVendors'
import { useAlerts } from '@/hooks/useAlerts'
import { gradeToColor } from '@/lib/scoring-utils'
import { api } from '@/lib/api'
import { ArrowDown, ArrowUp, TrendingUp, Users, ShieldAlert, Target } from 'lucide-react'
import type { Grade } from '@/types/scoring'

interface GradeDistData {
  grade: Grade
  current: number
  previous: number
}

export default function DashboardPage() {
  const { data: portfolio } = usePortfolioScores()
  const { data: vendors } = useVendors()
  const { data: alerts } = useAlerts()
  const { data: gradeDist } = useQuery({
    queryKey: ['grade-distribution'],
    queryFn: () => api.get<GradeDistData[]>('/api/v1/scoring/grade-distribution'),
  })

  const topRisk = [...(vendors ?? [])].sort((a, b) => a.score - b.score).slice(0, 10)
  const recentAlerts = (alerts ?? []).slice(0, 5)

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-[#1B3A5C]">Dashboard RSSI</h1>

      {/* KPIs */}
      <div className="grid grid-cols-5 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <TrendingUp className="mx-auto mb-2 h-5 w-5 text-[#2E75B6]" />
            <p className="text-2xl font-bold">{portfolio?.averageScore ?? '—'}</p>
            <p className="text-xs text-gray-500">Score moyen</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <Users className="mx-auto mb-2 h-5 w-5 text-[#2E75B6]" />
            <p className="text-2xl font-bold">{portfolio?.totalVendors ?? 0}</p>
            <p className="text-xs text-gray-500">Fournisseurs</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <ArrowUp className="mx-auto mb-2 h-5 w-5 text-[#27AE60]" />
            <p className="text-2xl font-bold text-[#27AE60]">{portfolio?.improved ?? 0}</p>
            <p className="text-xs text-gray-500">Ameliores</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <ArrowDown className="mx-auto mb-2 h-5 w-5 text-[#C0392B]" />
            <p className="text-2xl font-bold text-[#C0392B]">{portfolio?.degraded ?? 0}</p>
            <p className="text-xs text-gray-500">Degrades</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <Target className="mx-auto mb-2 h-5 w-5 text-[#2E75B6]" />
            <p className="text-2xl font-bold">{portfolio?.tier1Coverage ?? 0}%</p>
            <p className="text-xs text-gray-500">Couverture Tier 1</p>
          </CardContent>
        </Card>
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-2 gap-6">
        <Card>
          <CardHeader><CardTitle>Score Global Portfolio</CardTitle></CardHeader>
          <CardContent className="flex justify-center">
            <ScoreGauge score={portfolio?.averageScore ?? 0} size={200} />
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Distribution des Grades</CardTitle></CardHeader>
          <CardContent>
            <GradeDistribution data={gradeDist ?? []} />
          </CardContent>
        </Card>
      </div>

      {/* Top risk + alerts */}
      <div className="grid grid-cols-3 gap-6">
        <Card className="col-span-2">
          <CardHeader><CardTitle>Top 10 Fournisseurs a Risque</CardTitle></CardHeader>
          <CardContent>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-gray-500">
                  <th className="pb-2">Fournisseur</th>
                  <th className="pb-2">Tier</th>
                  <th className="pb-2">Score</th>
                  <th className="pb-2">Grade</th>
                </tr>
              </thead>
              <tbody>
                {topRisk.map((v) => (
                  <tr key={v.id} className="border-b last:border-0">
                    <td className="py-2 font-medium">{v.name}</td>
                    <td><Badge variant="outline">Tier {v.tier}</Badge></td>
                    <td className="font-mono">{v.score}</td>
                    <td>
                      <Badge style={{ backgroundColor: gradeToColor(v.grade), color: '#fff' }}>
                        {v.grade}
                      </Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2"><ShieldAlert className="h-4 w-4" /> Alertes Recentes</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {recentAlerts.map((a) => (
              <div key={a.id} className="rounded-lg border-l-4 p-2 text-xs" style={{ borderColor: a.severity === 'critical' ? '#C0392B' : a.severity === 'high' ? '#E67E22' : '#F39C12' }}>
                <p className="font-semibold">{a.title}</p>
                <p className="text-gray-500">{a.vendorName}</p>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
