'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  useGRCControls,
  useGRCMaturity,
  useFrameworkCoverage,
  useGRCHeatmap,
  useUpdateControl,
} from '@/hooks/useInternal'
import { FileCheck, ShieldCheck, BarChart3 } from 'lucide-react'

const FRAMEWORKS = [
  { id: 'iso27001', label: 'ISO 27001' },
  { id: 'dora', label: 'DORA' },
  { id: 'nis2', label: 'NIS2' },
  { id: 'hds', label: 'HDS' },
  { id: 'rgpd', label: 'RGPD' },
]

const STATUS_COLORS: Record<string, string> = {
  implemented: '#27AE60',
  partial: '#F39C12',
  not_implemented: '#C0392B',
}

const STATUS_LABELS: Record<string, string> = {
  implemented: 'Implemente',
  partial: 'Partiel',
  not_implemented: 'Non implemente',
}

const HEATMAP_COLORS: Record<string, string> = {
  good: '#27AE60',
  warning: '#F39C12',
  critical: '#C0392B',
}

export default function GRCPage() {
  const [domainFilter, setDomainFilter] = useState<string>('')
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [frameworkFilter, setFrameworkFilter] = useState<string>('')
  const [selectedFramework, setSelectedFramework] = useState('iso27001')

  const { data: controls } = useGRCControls({
    domain: domainFilter || undefined,
    status: statusFilter || undefined,
    framework: frameworkFilter || undefined,
  })
  const { data: maturity } = useGRCMaturity()
  const { data: coverage } = useFrameworkCoverage(selectedFramework)
  const { data: heatmap } = useGRCHeatmap()
  const updateMutation = useUpdateControl()

  // Extract unique domains from controls
  const domains = [...new Set((controls ?? []).map((c) => c.domain))].sort()

  // Group heatmap data by domain
  const heatmapByDomain: Record<string, Record<string, { coverage_percent: number; status: string }>> = {}
  for (const cell of heatmap ?? []) {
    if (!heatmapByDomain[cell.domain]) heatmapByDomain[cell.domain] = {}
    heatmapByDomain[cell.domain][cell.framework] = cell
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[#1B3A5C]">GRC / PSSI</h1>
        <p className="text-gray-600">Gouvernance, Risques, Conformite et Politique de Securite</p>
      </div>

      {/* Maturity overview */}
      <div className="grid grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Maturite Globale
            </CardTitle>
          </CardHeader>
          <CardContent>
            {maturity ? (
              <div className="space-y-4">
                <div className="text-center">
                  <span className="text-5xl font-bold text-[#1B3A5C]">
                    {maturity.overall_maturity.toFixed(1)}
                  </span>
                  <span className="text-lg text-gray-500"> / 5.0</span>
                </div>
                {maturity.domains && Object.entries(maturity.domains).map(([domain, data]) => (
                  <div key={domain} className="flex items-center justify-between">
                    <span className="text-sm capitalize">{domain.replace(/_/g, ' ')}</span>
                    <div className="flex items-center gap-2">
                      <div className="h-2 w-24 rounded-full bg-gray-200">
                        <div
                          className="h-2 rounded-full"
                          style={{
                            width: `${(data.average_level / 5) * 100}%`,
                            backgroundColor: data.average_level >= 4 ? '#27AE60' : data.average_level >= 2.5 ? '#F39C12' : '#C0392B',
                          }}
                        />
                      </div>
                      <span className="text-sm font-mono w-8 text-right">{data.average_level.toFixed(1)}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-400">Pas de donnees de maturite</p>
            )}
          </CardContent>
        </Card>

        {/* Framework coverage cards */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ShieldCheck className="h-5 w-5" />
              Couverture par Referentiel
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex gap-2 mb-4">
              {FRAMEWORKS.map((fw) => (
                <button
                  key={fw.id}
                  onClick={() => setSelectedFramework(fw.id)}
                  className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors ${
                    selectedFramework === fw.id
                      ? 'bg-[#2E75B6] text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {fw.label}
                </button>
              ))}
            </div>
            {coverage ? (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-500">Couverture</span>
                  <span className="text-2xl font-bold">{coverage.coverage_percent}%</span>
                </div>
                <div className="h-3 rounded-full bg-gray-200">
                  <div
                    className="h-3 rounded-full transition-all"
                    style={{
                      width: `${coverage.coverage_percent}%`,
                      backgroundColor: coverage.coverage_percent >= 75 ? '#27AE60' : coverage.coverage_percent >= 40 ? '#F39C12' : '#C0392B',
                    }}
                  />
                </div>
                <div className="grid grid-cols-3 gap-2 text-center">
                  <div className="rounded-md bg-green-50 p-2">
                    <p className="text-lg font-bold text-green-700">{coverage.implemented}</p>
                    <p className="text-xs text-green-600">Implementes</p>
                  </div>
                  <div className="rounded-md bg-yellow-50 p-2">
                    <p className="text-lg font-bold text-yellow-700">{coverage.partial}</p>
                    <p className="text-xs text-yellow-600">Partiels</p>
                  </div>
                  <div className="rounded-md bg-red-50 p-2">
                    <p className="text-lg font-bold text-red-700">{coverage.not_implemented}</p>
                    <p className="text-xs text-red-600">Non impl.</p>
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-sm text-gray-400">Selectionnez un referentiel</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Heatmap */}
      {heatmap && heatmap.length > 0 && (
        <Card>
          <CardHeader><CardTitle>Heatmap Domaine x Referentiel</CardTitle></CardHeader>
          <CardContent className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr>
                  <th className="pb-2 text-left text-gray-500">Domaine</th>
                  {FRAMEWORKS.map((fw) => (
                    <th key={fw.id} className="pb-2 text-center text-gray-500">{fw.label}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {Object.entries(heatmapByDomain).map(([domain, fwData]) => (
                  <tr key={domain} className="border-t">
                    <td className="py-2 capitalize font-medium">{domain.replace(/_/g, ' ')}</td>
                    {FRAMEWORKS.map((fw) => {
                      const cell = fwData[fw.id]
                      return (
                        <td key={fw.id} className="py-2 text-center">
                          {cell ? (
                            <span
                              className="inline-block rounded px-2 py-1 text-white font-medium"
                              style={{ backgroundColor: HEATMAP_COLORS[cell.status] ?? '#6B7280' }}
                            >
                              {cell.coverage_percent}%
                            </span>
                          ) : (
                            <span className="text-gray-300">-</span>
                          )}
                        </td>
                      )
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>
      )}

      {/* Controls list with filters */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileCheck className="h-5 w-5" />
            Controles de Securite ({controls?.length ?? 0})
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-3 mb-4">
            <select
              value={domainFilter}
              onChange={(e) => setDomainFilter(e.target.value)}
              className="rounded-md border border-gray-300 px-3 py-1.5 text-sm"
            >
              <option value="">Tous les domaines</option>
              {domains.map((d) => (
                <option key={d} value={d}>{d.replace(/_/g, ' ')}</option>
              ))}
            </select>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="rounded-md border border-gray-300 px-3 py-1.5 text-sm"
            >
              <option value="">Tous les statuts</option>
              <option value="implemented">Implemente</option>
              <option value="partial">Partiel</option>
              <option value="not_implemented">Non implemente</option>
            </select>
            <select
              value={frameworkFilter}
              onChange={(e) => setFrameworkFilter(e.target.value)}
              className="rounded-md border border-gray-300 px-3 py-1.5 text-sm"
            >
              <option value="">Tous les referentiels</option>
              {FRAMEWORKS.map((fw) => (
                <option key={fw.id} value={fw.id}>{fw.label}</option>
              ))}
            </select>
          </div>

          {controls && controls.length > 0 ? (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-gray-500">
                  <th className="pb-2">Ref</th>
                  <th className="pb-2">Titre</th>
                  <th className="pb-2">Domaine</th>
                  <th className="pb-2">Statut</th>
                  <th className="pb-2">Proprietaire</th>
                  <th className="pb-2">Referentiels</th>
                </tr>
              </thead>
              <tbody>
                {controls.map((c) => (
                  <tr key={c.id} className="border-b last:border-0">
                    <td className="py-2 font-mono text-xs">{c.reference}</td>
                    <td className="py-2">{c.title}</td>
                    <td className="py-2 capitalize text-xs">{c.domain.replace(/_/g, ' ')}</td>
                    <td className="py-2">
                      <select
                        value={c.status}
                        onChange={(e) =>
                          updateMutation.mutate({
                            controlId: c.id,
                            update: { status: e.target.value },
                          })
                        }
                        className="rounded border px-2 py-0.5 text-xs"
                        style={{ borderColor: STATUS_COLORS[c.status] ?? '#6B7280' }}
                      >
                        {Object.entries(STATUS_LABELS).map(([val, lbl]) => (
                          <option key={val} value={val}>{lbl}</option>
                        ))}
                      </select>
                    </td>
                    <td className="py-2 text-xs text-gray-600">{c.owner ?? '-'}</td>
                    <td className="py-2">
                      <div className="flex gap-1 flex-wrap">
                        {c.frameworks.map((fw) => (
                          <Badge key={fw} variant="outline" className="text-xs">
                            {fw.toUpperCase()}
                          </Badge>
                        ))}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="text-sm text-gray-400">Aucun controle trouve</p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
