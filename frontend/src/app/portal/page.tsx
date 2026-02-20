'use client'

import { useState, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ScoreGauge } from '@/components/charts/ScoreGauge'
import { api } from '@/lib/api'
import { gradeToColor } from '@/lib/scoring-utils'
import { Globe, Upload, MessageSquare, FileText, Send, X, CheckCircle } from 'lucide-react'

interface PortalScorecard {
  vendor_id: string
  vendor_name: string
  domain: string
  score: number
  grade: string
  domain_scores: Record<string, number>
  last_scan: string | null
}

interface PortalFinding {
  id: string
  title: string
  severity: string
  domain: string
  status: string
  description: string
  detected_at: string | null
}

interface PortalQuestionnaire {
  id: string
  title: string
  status: string
  due_date: string | null
  question_count: number
}

interface PortalDispute {
  id: string
  finding_id: string
  reason: string
  status: string
  created_at: string | null
  evidence_urls: string[]
}

export default function PortalPage() {
  const queryClient = useQueryClient()
  const [disputeFindingId, setDisputeFindingId] = useState<string | null>(null)
  const [disputeReason, setDisputeReason] = useState('')
  const [uploadDisputeId, setUploadDisputeId] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const { data: scorecard } = useQuery({
    queryKey: ['portal-scorecard'],
    queryFn: () => api.get<PortalScorecard>('/api/v1/portal/scorecard'),
  })

  const { data: findings } = useQuery({
    queryKey: ['portal-findings'],
    queryFn: () => api.get<PortalFinding[]>('/api/v1/portal/findings'),
  })

  const { data: questionnaires } = useQuery({
    queryKey: ['portal-questionnaires'],
    queryFn: () => api.get<PortalQuestionnaire[]>('/api/v1/portal/questionnaires'),
  })

  const disputeMutation = useMutation({
    mutationFn: (body: { finding_id: string; reason: string }) =>
      api.post<PortalDispute>('/api/v1/portal/disputes', body),
    onSuccess: (dispute) => {
      setDisputeFindingId(null)
      setDisputeReason('')
      setUploadDisputeId(dispute.id)
      queryClient.invalidateQueries({ queryKey: ['portal-findings'] })
    },
  })

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!uploadDisputeId || !e.target.files?.length) return
    const file = e.target.files[0]
    const formData = new FormData()
    formData.append('file', file)

    await fetch(
      `${process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'}/api/v1/portal/disputes/${uploadDisputeId}/evidence`,
      { method: 'POST', body: formData },
    )
    setUploadDisputeId(null)
  }

  const pendingQuestionnaires = questionnaires?.filter((q) => q.status === 'pending').length ?? 0

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-[#1B3A5C]">
        <Globe className="mr-2 inline h-6 w-6" />
        Portail Fournisseur
      </h1>

      {!scorecard ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Globe className="mx-auto mb-4 h-12 w-12 text-gray-300" />
            <p className="text-gray-500">
              Connectez-vous avec vos identifiants fournisseur pour acceder a votre scorecard.
            </p>
          </CardContent>
        </Card>
      ) : (
        <>
          {/* Score overview */}
          <Card className="border-2 border-[#2E75B6]">
            <CardContent className="flex items-center justify-between p-6">
              <div>
                <h2 className="text-xl font-bold text-[#1B3A5C]">{scorecard.vendor_name}</h2>
                <p className="text-gray-500">{scorecard.domain}</p>
                {scorecard.last_scan && (
                  <p className="mt-1 text-xs text-gray-400">
                    Dernier scan: {new Date(scorecard.last_scan).toLocaleDateString('fr-FR')}
                  </p>
                )}
              </div>
              <div className="flex items-center gap-6">
                <ScoreGauge score={scorecard.score} size={140} />
                <Badge
                  className="px-4 py-2 text-2xl"
                  style={{ backgroundColor: gradeToColor(scorecard.grade as 'A' | 'B' | 'C' | 'D' | 'F'), color: '#fff' }}
                >
                  {scorecard.grade}
                </Badge>
              </div>
            </CardContent>
          </Card>

          {/* Domain scores */}
          {Object.keys(scorecard.domain_scores).length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Scores par domaine</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                  {Object.entries(scorecard.domain_scores).map(([domain, score]) => (
                    <div key={domain} className="rounded-lg border p-3 text-center">
                      <p className="text-xs text-gray-500">{domain.replace(/_/g, ' ')}</p>
                      <p className="text-2xl font-bold text-[#1B3A5C]">{score}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Action cards */}
          <div className="grid grid-cols-3 gap-4">
            <Card className="cursor-pointer transition-shadow hover:shadow-md">
              <CardContent className="flex flex-col items-center p-6">
                <MessageSquare className="mb-2 h-8 w-8 text-[#2E75B6]" />
                <p className="font-semibold text-[#1B3A5C]">Contester un finding</p>
                <p className="mt-1 text-xs text-gray-500">
                  Selectionnez un finding ci-dessous
                </p>
              </CardContent>
            </Card>

            <Card
              className="cursor-pointer transition-shadow hover:shadow-md"
              onClick={() => fileInputRef.current?.click()}
            >
              <CardContent className="flex flex-col items-center p-6">
                <Upload className="mb-2 h-8 w-8 text-[#2E75B6]" />
                <p className="font-semibold text-[#1B3A5C]">Uploader des preuves</p>
                <p className="mt-1 text-xs text-gray-500">Documents justificatifs</p>
              </CardContent>
            </Card>

            <Card className="cursor-pointer transition-shadow hover:shadow-md">
              <CardContent className="flex flex-col items-center p-6">
                <FileText className="mb-2 h-8 w-8 text-[#2E75B6]" />
                <p className="font-semibold text-[#1B3A5C]">Questionnaires</p>
                <p className="mt-1 text-xs text-gray-500">
                  {pendingQuestionnaires} questionnaire(s) a remplir
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Dispute modal inline */}
          {disputeFindingId && (
            <Card className="border-2 border-[#2E75B6]">
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>Contester le finding</CardTitle>
                <button onClick={() => setDisputeFindingId(null)}>
                  <X className="h-5 w-5 text-gray-400 hover:text-gray-600" />
                </button>
              </CardHeader>
              <CardContent className="space-y-3">
                <p className="text-sm text-gray-600">
                  Finding ID: <span className="font-mono">{disputeFindingId}</span>
                </p>
                <textarea
                  value={disputeReason}
                  onChange={(e) => setDisputeReason(e.target.value)}
                  placeholder="Decrivez la raison de votre contestation (min. 10 caracteres)..."
                  className="w-full rounded border p-3 text-sm focus:border-[#2E75B6] focus:outline-none"
                  rows={4}
                />
                <button
                  onClick={() =>
                    disputeMutation.mutate({
                      finding_id: disputeFindingId,
                      reason: disputeReason,
                    })
                  }
                  disabled={disputeReason.length < 10 || disputeMutation.isPending}
                  className="rounded bg-[#2E75B6] px-4 py-2 text-sm font-medium text-white hover:bg-[#1B3A5C] disabled:opacity-50"
                >
                  <Send className="mr-1 inline h-4 w-4" />
                  Soumettre la contestation
                </button>
              </CardContent>
            </Card>
          )}

          {/* Evidence upload success */}
          {uploadDisputeId && (
            <Card className="border-2 border-green-300 bg-green-50">
              <CardContent className="flex items-center gap-3 p-4">
                <CheckCircle className="h-5 w-5 text-green-600" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-green-800">
                    Contestation soumise. Vous pouvez ajouter des preuves.
                  </p>
                </div>
                <label className="cursor-pointer rounded bg-green-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-green-700">
                  <Upload className="mr-1 inline h-3 w-3" />
                  Upload evidence
                  <input
                    type="file"
                    className="hidden"
                    onChange={handleFileUpload}
                  />
                </label>
                <button
                  onClick={() => setUploadDisputeId(null)}
                  className="text-xs text-gray-500 hover:text-gray-700"
                >
                  Fermer
                </button>
              </CardContent>
            </Card>
          )}

          <input
            ref={fileInputRef}
            type="file"
            className="hidden"
            onChange={handleFileUpload}
          />

          {/* Findings list */}
          <Card>
            <CardHeader>
              <CardTitle>Findings - Votre evaluation</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-gray-50 text-left text-gray-500">
                    <th className="px-4 py-3">Finding</th>
                    <th className="px-4 py-3">Domaine</th>
                    <th className="px-4 py-3">Severite</th>
                    <th className="px-4 py-3">Statut</th>
                    <th className="px-4 py-3">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {(findings ?? []).map((f) => (
                    <tr key={f.id} className="border-b hover:bg-gray-50">
                      <td className="px-4 py-3">
                        <p className="font-medium">{f.title}</p>
                        <p className="text-xs text-gray-400">{f.description}</p>
                      </td>
                      <td className="px-4 py-3 text-gray-500">{f.domain.replace(/_/g, ' ')}</td>
                      <td className="px-4 py-3">
                        <Badge variant="outline">{f.severity}</Badge>
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant="outline">{f.status}</Badge>
                      </td>
                      <td className="px-4 py-3">
                        <button
                          onClick={() => {
                            setDisputeFindingId(f.id)
                            setDisputeReason('')
                          }}
                          className="text-xs text-[#2E75B6] hover:underline"
                        >
                          Contester
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>

          {/* Questionnaires */}
          <Card>
            <CardHeader>
              <CardTitle>
                <FileText className="mr-2 inline h-5 w-5" />
                Questionnaires assignes
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-gray-50 text-left text-gray-500">
                    <th className="px-4 py-3">Questionnaire</th>
                    <th className="px-4 py-3">Questions</th>
                    <th className="px-4 py-3">Date limite</th>
                    <th className="px-4 py-3">Statut</th>
                    <th className="px-4 py-3">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {(questionnaires ?? []).map((q) => (
                    <tr key={q.id} className="border-b hover:bg-gray-50">
                      <td className="px-4 py-3 font-medium">{q.title}</td>
                      <td className="px-4 py-3 text-gray-500">{q.question_count}</td>
                      <td className="px-4 py-3 text-gray-500">
                        {q.due_date ? new Date(q.due_date).toLocaleDateString('fr-FR') : '-'}
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant="outline">{q.status}</Badge>
                      </td>
                      <td className="px-4 py-3">
                        <button className="text-xs text-[#2E75B6] hover:underline">
                          Repondre
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  )
}
