'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { useADScore, useADHistory, useADFindings, useScanAD } from '@/hooks/useInternal'
import { ScoreGauge } from '@/components/charts/ScoreGauge'
import { Server, Users, Shield, Clock, Key, Lock } from 'lucide-react'

const SEVERITY_COLORS: Record<string, string> = {
  critical: '#C0392B',
  high: '#E67E22',
  medium: '#F39C12',
  low: '#3498DB',
  info: '#95A5A6',
}

const CATEGORY_ICONS: Record<string, typeof Users> = {
  privileged_accounts: Users,
  gpo_security: Shield,
  kerberoasting: Key,
  delegations: Lock,
  dormant_accounts: Clock,
  password_policy: Lock,
}

const CATEGORY_LABELS: Record<string, string> = {
  privileged_accounts: 'Comptes Privilegies',
  gpo_security: 'Securite GPO',
  kerberoasting: 'Kerberoasting',
  delegations: 'Delegations',
  dormant_accounts: 'Comptes Dormants',
  password_policy: 'Politique de Mots de Passe',
}

export default function ADRatingPage() {
  const { data: score, isLoading: scoreLoading } = useADScore()
  const { data: history } = useADHistory()
  const { data: findings } = useADFindings()
  const scanMutation = useScanAD()
  const [scanTarget, setScanTarget] = useState('')

  const handleScan = () => {
    if (scanTarget.trim()) {
      scanMutation.mutate({ target: scanTarget })
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[#1B3A5C]">AD Rating</h1>
          <p className="text-gray-600">Evaluation de la securite Active Directory</p>
        </div>
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="Domain Controller..."
            value={scanTarget}
            onChange={(e) => setScanTarget(e.target.value)}
            className="rounded-md border border-gray-300 px-3 py-2 text-sm"
          />
          <button
            onClick={handleScan}
            disabled={scanMutation.isPending || !scanTarget.trim()}
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
            const Icon = CATEGORY_ICONS[key] ?? Shield
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

      {/* History comparison */}
      {history && history.length > 1 && (
        <Card>
          <CardHeader><CardTitle>Historique des Scores</CardTitle></CardHeader>
          <CardContent>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-gray-500">
                  <th className="pb-2">Date</th>
                  <th className="pb-2">Score</th>
                  <th className="pb-2">Grade</th>
                  <th className="pb-2">Findings</th>
                </tr>
              </thead>
              <tbody>
                {history.map((h) => (
                  <tr key={h.id} className="border-b last:border-0">
                    <td className="py-2">{h.created_at ? new Date(h.created_at).toLocaleDateString('fr-FR') : '-'}</td>
                    <td className="py-2 font-mono">{h.score}</td>
                    <td className="py-2">
                      <Badge variant="outline">{h.grade}</Badge>
                    </td>
                    <td className="py-2">{h.findings_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
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
