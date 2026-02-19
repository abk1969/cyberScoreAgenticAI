'use client'

import { use } from 'react'
import Link from 'next/link'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ScoreGauge } from '@/components/charts/ScoreGauge'
import { RiskRadar } from '@/components/charts/RiskRadar'
import { useVendor } from '@/hooks/useVendors'
import { useVendorScore } from '@/hooks/useScoring'
import { gradeToColor } from '@/lib/scoring-utils'
import { DOMAIN_LABELS } from '@/lib/constants'
import { ArrowLeft, RefreshCw, FileText, Send } from 'lucide-react'
import type { ScoringDomain } from '@/types/scoring'

export default function VendorDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)
  const { data: vendor } = useVendor(id)
  const { data: scoring } = useVendorScore(id)

  if (!vendor) return <div className="p-8">Chargement...</div>

  const domainScores = scoring?.domainScores ?? []
  const domainList = Array.isArray(domainScores) ? domainScores : []

  return (
    <div className="space-y-6">
      <Link href="/vendors" className="inline-flex items-center gap-1 text-sm text-[#2E75B6] hover:underline">
        <ArrowLeft className="h-4 w-4" /> Retour a la liste
      </Link>

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[#1B3A5C]">{vendor.name}</h1>
          <p className="text-gray-500">{vendor.domain} — <Badge variant="outline">Tier {vendor.tier}</Badge></p>
        </div>
        <div className="flex items-center gap-4">
          <ScoreGauge score={vendor.score} size={120} />
          <Badge className="px-4 py-2 text-2xl" style={{ backgroundColor: gradeToColor(vendor.grade), color: '#fff' }}>
            {vendor.grade}
          </Badge>
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-3">
        <button className="inline-flex items-center gap-2 rounded-lg bg-[#2E75B6] px-4 py-2 text-sm font-medium text-white hover:bg-[#1B3A5C]">
          <RefreshCw className="h-4 w-4" /> Lancer un scan
        </button>
        <button className="inline-flex items-center gap-2 rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium hover:bg-gray-50">
          <FileText className="h-4 w-4" /> Generer un rapport
        </button>
        <button className="inline-flex items-center gap-2 rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium hover:bg-gray-50">
          <Send className="h-4 w-4" /> Envoyer un questionnaire
        </button>
      </div>

      {/* Radar chart */}
      {domainList.length > 0 && (
        <Card>
          <CardHeader><CardTitle>Profil de Risque</CardTitle></CardHeader>
          <CardContent className="flex justify-center">
            <RiskRadar
              data={domainList.map((d) => ({
                domain: d.domain,
                label: DOMAIN_LABELS[d.domain] ?? d.domain,
                score: d.score,
              }))}
              height={300}
            />
          </CardContent>
        </Card>
      )}

      {/* Domain scores grid */}
      <div className="grid grid-cols-4 gap-4">
        {domainList.map((d) => (
          <Link key={d.domain} href={`/vendors/${id}/scoring?domain=${d.domain}`}>
            <Card className="cursor-pointer transition-shadow hover:shadow-md">
              <CardContent className="p-4">
                <p className="text-sm font-semibold">{DOMAIN_LABELS[d.domain as ScoringDomain] ?? d.domain}</p>
                <div className="mt-2 flex items-center justify-between">
                  <span className="text-2xl font-bold">{d.score}</span>
                  <Badge style={{ backgroundColor: gradeToColor(d.grade as 'A' | 'B' | 'C' | 'D' | 'F'), color: '#fff' }}>
                    {d.grade}
                  </Badge>
                </div>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  )
}
