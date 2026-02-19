'use client'

import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { api } from '@/lib/api'
import { Shield } from 'lucide-react'

interface DORARegisterEntry {
  id: string
  vendor: string
  type: string
  critical: boolean
  lastAudit: string
  score: number
  status: 'conforme' | 'partiel' | 'non-conforme'
}

interface DORAStats {
  coverage: number
  total: number
  registered: number
  criticalCount: number
  evaluatedThisQuarter: number
  register: DORARegisterEntry[]
}

const statusColors: Record<string, string> = {
  conforme: '#27AE60', partiel: '#F39C12', 'non-conforme': '#C0392B',
}

export default function DORACompliancePage() {
  const { data: stats } = useQuery({
    queryKey: ['dora-compliance'],
    queryFn: () => api.get<DORAStats>('/api/v1/compliance/dora'),
  })

  const coverage = stats?.coverage ?? 0
  const total = stats?.total ?? 0
  const registered = stats?.registered ?? 0
  const register = stats?.register ?? []

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-[#1B3A5C]">
        <Shield className="mr-2 inline h-6 w-6" />
        Conformite DORA — Registre Prestataires TIC
      </h1>

      {/* Summary */}
      <div className="grid grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-3xl font-bold text-[#2E75B6]">{coverage}%</p>
            <p className="text-xs text-gray-500">Couverture registre</p>
            <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-gray-200">
              <div className="h-full rounded-full bg-[#2E75B6]" style={{ width: `${coverage}%` }} />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-3xl font-bold">{registered}</p>
            <p className="text-xs text-gray-500">Prestataires enregistres</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-3xl font-bold text-[#C0392B]">{stats?.criticalCount ?? 0}</p>
            <p className="text-xs text-gray-500">Critiques (Tier 1)</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-3xl font-bold text-[#27AE60]">{stats?.evaluatedThisQuarter ?? 0}</p>
            <p className="text-xs text-gray-500">Evalues ce trimestre</p>
          </CardContent>
        </Card>
      </div>

      {/* Register table */}
      <Card>
        <CardHeader><CardTitle>Registre des prestataires TIC (Art. 28 DORA)</CardTitle></CardHeader>
        <CardContent className="p-0">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-gray-50 text-left text-gray-500">
                <th className="px-4 py-3">Prestataire</th>
                <th className="px-4 py-3">Type prestation</th>
                <th className="px-4 py-3">Criticite</th>
                <th className="px-4 py-3">Dernier audit</th>
                <th className="px-4 py-3">Score</th>
                <th className="px-4 py-3">Statut conformite</th>
              </tr>
            </thead>
            <tbody>
              {register.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-12 text-center text-gray-400">
                    Aucune donnee disponible dans le registre DORA.
                  </td>
                </tr>
              ) : (
                register.map((r) => (
                  <tr key={r.id} className="border-b hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium">{r.vendor}</td>
                    <td className="px-4 py-3 text-gray-500">{r.type}</td>
                    <td className="px-4 py-3">
                      {r.critical ? (
                        <Badge className="bg-red-100 text-[#C0392B]">Critique</Badge>
                      ) : (
                        <Badge variant="outline">Standard</Badge>
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-500">{r.lastAudit}</td>
                    <td className="px-4 py-3 font-mono font-bold">{r.score}</td>
                    <td className="px-4 py-3">
                      <Badge style={{ backgroundColor: statusColors[r.status], color: '#fff' }}>
                        {r.status}
                      </Badge>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  )
}
