'use client'

import { use, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { useDomainScores } from '@/hooks/useScoring'
import { DOMAIN_LABELS } from '@/lib/constants'
import type { ScoringDomain } from '@/types/scoring'

const DOMAINS: ScoringDomain[] = [
  'network_security', 'dns_security', 'web_security', 'email_security',
  'patching_cadence', 'ip_reputation', 'leaks_exposure', 'regulatory_presence',
]

const severityColors: Record<string, string> = {
  critical: '#C0392B', high: '#E67E22', medium: '#F39C12', low: '#2ECC71', info: '#3498DB',
}

export default function ScoringDrilldownPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)
  const { data: domainScores } = useDomainScores(id)
  const [selectedDomain, setSelectedDomain] = useState<ScoringDomain>('web_security')

  const domainScoresList = Array.isArray(domainScores) ? domainScores : []
  const selected = domainScoresList.find((d) => d.domain === selectedDomain)
  const findings = selected?.findings ?? []

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-[#1B3A5C]">Detail du Scoring</h1>

      {/* Domain tabs */}
      <div className="flex flex-wrap gap-2">
        {DOMAINS.map((d) => (
          <button
            key={d}
            onClick={() => setSelectedDomain(d)}
            className={`rounded-lg px-3 py-2 text-xs font-medium transition-colors ${
              selectedDomain === d
                ? 'bg-[#2E75B6] text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {DOMAIN_LABELS[d]}
          </button>
        ))}
      </div>

      {/* Findings table */}
      <Card>
        <CardHeader>
          <CardTitle>{DOMAIN_LABELS[selectedDomain]} — Findings</CardTitle>
        </CardHeader>
        <CardContent>
          {findings.length === 0 ? (
            <p className="py-8 text-center text-gray-400">Aucun finding pour ce domaine</p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-gray-500">
                  <th className="pb-2">Titre</th>
                  <th className="pb-2">Severite</th>
                  <th className="pb-2">CVSS</th>
                  <th className="pb-2">Source</th>
                  <th className="pb-2">Statut</th>
                  <th className="pb-2">Date</th>
                </tr>
              </thead>
              <tbody>
                {findings.map((f) => (
                  <tr key={f.id} className="border-b last:border-0">
                    <td className="py-3 font-medium">{f.title}</td>
                    <td>
                      <Badge style={{ backgroundColor: severityColors[f.severity] ?? '#94A3B8', color: '#fff' }}>
                        {f.severity}
                      </Badge>
                    </td>
                    <td className="font-mono">{f.cvssScore !== null ? f.cvssScore : '—'}</td>
                    <td className="text-gray-500">{f.source}</td>
                    <td><Badge variant="outline">{f.status}</Badge></td>
                    <td className="text-gray-500">{f.detectedAt}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
