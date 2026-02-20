'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { useM365Score, useM365Findings, useScanM365 } from '@/hooks/useInternal'
import { ScoreGauge } from '@/components/charts/ScoreGauge'
import { Cloud, ShieldCheck, Mail, Share2, MessageCircle, Lock } from 'lucide-react'

const SEVERITY_COLORS: Record<string, string> = {
  critical: '#C0392B',
  high: '#E67E22',
  medium: '#F39C12',
  low: '#3498DB',
  info: '#95A5A6',
}

const CATEGORY_ICONS: Record<string, typeof Cloud> = {
  mfa_coverage: ShieldCheck,
  conditional_access: Lock,
  exchange_protection: Mail,
  sharepoint_permissions: Share2,
  teams_settings: MessageCircle,
  defender_config: ShieldCheck,
}

const CATEGORY_LABELS: Record<string, string> = {
  mfa_coverage: 'Couverture MFA',
  conditional_access: 'Conditional Access',
  exchange_protection: 'Protection Exchange',
  sharepoint_permissions: 'Permissions SharePoint',
  teams_settings: 'Parametres Teams',
  defender_config: 'Configuration Defender',
}

export default function M365RatingPage() {
  const { data: score, isLoading: scoreLoading } = useM365Score()
  const { data: findings } = useM365Findings()
  const scanMutation = useScanM365()
  const [tenantId, setTenantId] = useState('')

  const handleScan = () => {
    if (tenantId.trim()) {
      scanMutation.mutate({ target: tenantId })
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[#1B3A5C]">M365 Rating</h1>
          <p className="text-gray-600">Evaluation de la securite Microsoft 365</p>
        </div>
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="Tenant ID..."
            value={tenantId}
            onChange={(e) => setTenantId(e.target.value)}
            className="rounded-md border border-gray-300 px-3 py-2 text-sm"
          />
          <button
            onClick={handleScan}
            disabled={scanMutation.isPending || !tenantId.trim()}
            className="rounded-md bg-[#2E75B6] px-4 py-2 text-sm font-medium text-white hover:bg-[#1B3A5C] disabled:opacity-50"
          >
            {scanMutation.isPending ? 'Scan en cours...' : 'Lancer le Scan'}
          </button>
        </div>
      </div>

      {/* Score gauge + category cards */}
      <div className="grid grid-cols-4 gap-6">
        <Card className="col-span-1">
          <CardHeader><CardTitle>Score Global</CardTitle></CardHeader>
          <CardContent className="flex justify-center">
            {scoreLoading ? (
              <div className="animate-pulse h-[200px] w-[200px] rounded-full bg-gray-200" />
            ) : (
              <ScoreGauge score={score?.score ?? 0} size={200} />
            )}
          </CardContent>
        </Card>

        <div className="col-span-3 grid grid-cols-3 gap-4">
          {Object.entries(CATEGORY_LABELS).map(([key, label]) => {
            const Icon = CATEGORY_ICONS[key] ?? Cloud
            const catScore = score?.category_scores?.[key]
            return (
              <Card key={key}>
                <CardContent className="p-4">
                  <div className="flex items-center gap-2 mb-2">
                    <Icon className="h-4 w-4 text-[#2E75B6]" />
                    <span className="text-sm font-medium">{label}</span>
                  </div>
                  {catScore !== undefined ? (
                    <div className="flex items-center gap-2">
                      <div className="h-2 flex-1 rounded-full bg-gray-200">
                        <div
                          className="h-2 rounded-full transition-all"
                          style={{
                            width: `${Math.min(100, catScore)}%`,
                            backgroundColor: catScore >= 80 ? '#27AE60' : catScore >= 50 ? '#F39C12' : '#C0392B',
                          }}
                        />
                      </div>
                      <span className="text-sm font-mono">{catScore.toFixed(0)}</span>
                    </div>
                  ) : (
                    <span className="text-xs text-gray-400">N/A</span>
                  )}
                </CardContent>
              </Card>
            )
          })}
        </div>
      </div>

      {/* MFA gauge card */}
      {score?.category_scores?.mfa_coverage !== undefined && (
        <Card>
          <CardHeader><CardTitle>Couverture MFA</CardTitle></CardHeader>
          <CardContent>
            <div className="flex items-center gap-6">
              <div className="relative h-32 w-32">
                <svg viewBox="0 0 100 100" className="h-full w-full -rotate-90">
                  <circle cx="50" cy="50" r="40" fill="none" stroke="#E5E7EB" strokeWidth="12" />
                  <circle
                    cx="50" cy="50" r="40" fill="none"
                    stroke={score.category_scores.mfa_coverage >= 80 ? '#27AE60' : score.category_scores.mfa_coverage >= 50 ? '#F39C12' : '#C0392B'}
                    strokeWidth="12"
                    strokeDasharray={`${score.category_scores.mfa_coverage * 2.51} 251`}
                    strokeLinecap="round"
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-xl font-bold">{score.category_scores.mfa_coverage.toFixed(0)}%</span>
                </div>
              </div>
              <div className="text-sm text-gray-600">
                <p>Score de couverture MFA</p>
                <p className="mt-1">Objectif : 100% des utilisateurs avec MFA active</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Findings table */}
      <Card>
        <CardHeader>
          <CardTitle>Findings ({findings?.length ?? 0})</CardTitle>
        </CardHeader>
        <CardContent>
          {findings && findings.length > 0 ? (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-gray-500">
                  <th className="pb-2">Severite</th>
                  <th className="pb-2">Categorie</th>
                  <th className="pb-2">Titre</th>
                  <th className="pb-2">Recommandation</th>
                  <th className="pb-2">Statut</th>
                </tr>
              </thead>
              <tbody>
                {findings.map((f) => (
                  <tr key={f.id} className="border-b last:border-0">
                    <td className="py-2">
                      <Badge style={{ backgroundColor: SEVERITY_COLORS[f.severity] ?? '#6B7280', color: '#fff' }}>
                        {f.severity}
                      </Badge>
                    </td>
                    <td className="py-2 capitalize">{f.category.replace(/_/g, ' ')}</td>
                    <td className="py-2">{f.title}</td>
                    <td className="py-2 text-gray-600 max-w-xs truncate">{f.recommendation ?? '-'}</td>
                    <td className="py-2">
                      <Badge variant="outline">{f.status}</Badge>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="text-sm text-gray-400">Aucun finding disponible</p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
