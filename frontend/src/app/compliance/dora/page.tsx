'use client'

import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { api } from '@/lib/api'
import { Shield, Download, AlertTriangle } from 'lucide-react'

interface DORARegisterEntry {
  id: string
  vendor_id: string
  vendor_name: string
  service_type: string
  critical: boolean
  tier: number
  contract_start: string | null
  contract_end: string | null
  last_audit: string | null
  score: number
  grade: string
  compliance_status: string
  notes: string
}

interface DORAcoverage {
  total_vendors: number
  registered: number
  coverage_pct: number
  critical_count: number
  tier1_count: number
  tier2_count: number
  tier3_count: number
  evaluated_this_quarter: number
  last_updated: string | null
}

interface DORAGap {
  id: string
  vendor_id: string
  vendor_name: string
  gap_type: string
  description: string
  severity: string
  recommendation: string
}

const statusColors: Record<string, string> = {
  conforme: '#27AE60',
  partiel: '#F39C12',
  'non-conforme': '#C0392B',
}

const gapSeverityColors: Record<string, string> = {
  critical: '#C0392B',
  high: '#E67E22',
  medium: '#F39C12',
  low: '#27AE60',
}

export default function DORACompliancePage() {
  const { data: register } = useQuery({
    queryKey: ['dora-register'],
    queryFn: () => api.get<DORARegisterEntry[]>('/api/v1/compliance/dora/register'),
  })

  const { data: coverage } = useQuery({
    queryKey: ['dora-coverage'],
    queryFn: () => api.get<DORAcoverage>('/api/v1/compliance/dora/coverage'),
  })

  const { data: gaps } = useQuery({
    queryKey: ['dora-gaps'],
    queryFn: () => api.get<DORAGap[]>('/api/v1/compliance/dora/gaps'),
  })

  const entries = register ?? []
  const coveragePct = coverage?.coverage_pct ?? 0

  const handleExport = () => {
    const url = `${process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'}/api/v1/compliance/dora/export`
    window.open(url, '_blank')
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-[#1B3A5C]">
          <Shield className="mr-2 inline h-6 w-6" />
          Conformite DORA — Registre Prestataires TIC
        </h1>
        <button
          onClick={handleExport}
          className="flex items-center gap-1 rounded bg-[#2E75B6] px-4 py-2 text-sm font-medium text-white hover:bg-[#1B3A5C]"
        >
          <Download className="h-4 w-4" />
          Exporter Excel
        </button>
      </div>

      {/* Summary stats */}
      <div className="grid grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-3xl font-bold text-[#2E75B6]">{coveragePct}%</p>
            <p className="text-xs text-gray-500">Couverture registre</p>
            <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-gray-200">
              <div className="h-full rounded-full bg-[#2E75B6]" style={{ width: `${coveragePct}%` }} />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-3xl font-bold">{coverage?.registered ?? 0}</p>
            <p className="text-xs text-gray-500">Prestataires enregistres</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-3xl font-bold text-[#C0392B]">{coverage?.critical_count ?? 0}</p>
            <p className="text-xs text-gray-500">Critiques (Tier 1)</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <p className="text-3xl font-bold text-[#27AE60]">{coverage?.evaluated_this_quarter ?? 0}</p>
            <p className="text-xs text-gray-500">Evalues ce trimestre</p>
          </CardContent>
        </Card>
      </div>

      {/* Tier breakdown */}
      {coverage && (
        <div className="grid grid-cols-3 gap-4">
          <Card>
            <CardContent className="p-3 text-center">
              <p className="text-lg font-bold text-[#C0392B]">{coverage.tier1_count}</p>
              <p className="text-xs text-gray-500">Tier 1 — Critique</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-3 text-center">
              <p className="text-lg font-bold text-[#F39C12]">{coverage.tier2_count}</p>
              <p className="text-xs text-gray-500">Tier 2 — Important</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-3 text-center">
              <p className="text-lg font-bold text-[#2E75B6]">{coverage.tier3_count}</p>
              <p className="text-xs text-gray-500">Tier 3 — Standard</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Register table */}
      <Card>
        <CardHeader>
          <CardTitle>Registre des prestataires TIC (Art. 28 DORA)</CardTitle>
        </CardHeader>
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
              {entries.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-12 text-center text-gray-400">
                    Aucune donnee disponible dans le registre DORA.
                  </td>
                </tr>
              ) : (
                entries.map((r) => (
                  <tr key={r.id} className="border-b hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium">{r.vendor_name}</td>
                    <td className="px-4 py-3 text-gray-500">{r.service_type}</td>
                    <td className="px-4 py-3">
                      {r.critical ? (
                        <Badge className="bg-red-100 text-[#C0392B]">Critique</Badge>
                      ) : (
                        <Badge variant="outline">Standard</Badge>
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-500">
                      {r.last_audit ? new Date(r.last_audit).toLocaleDateString('fr-FR') : 'Jamais'}
                    </td>
                    <td className="px-4 py-3 font-mono font-bold">{r.score}</td>
                    <td className="px-4 py-3">
                      <Badge style={{ backgroundColor: statusColors[r.compliance_status] ?? '#888', color: '#fff' }}>
                        {r.compliance_status}
                      </Badge>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </CardContent>
      </Card>

      {/* Gaps analysis */}
      {gaps && gaps.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>
              <AlertTriangle className="mr-2 inline h-5 w-5 text-[#F39C12]" />
              Analyse des ecarts DORA
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-gray-50 text-left text-gray-500">
                  <th className="px-4 py-3">Prestataire</th>
                  <th className="px-4 py-3">Type ecart</th>
                  <th className="px-4 py-3">Description</th>
                  <th className="px-4 py-3">Severite</th>
                  <th className="px-4 py-3">Recommandation</th>
                </tr>
              </thead>
              <tbody>
                {gaps.map((g) => (
                  <tr key={g.id} className="border-b hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium">{g.vendor_name}</td>
                    <td className="px-4 py-3 text-gray-500">{g.gap_type.replace(/_/g, ' ')}</td>
                    <td className="px-4 py-3">{g.description}</td>
                    <td className="px-4 py-3">
                      <Badge style={{ backgroundColor: gapSeverityColors[g.severity] ?? '#888', color: '#fff' }}>
                        {g.severity}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-xs text-gray-600">{g.recommendation}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
