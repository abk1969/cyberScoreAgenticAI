'use client'

import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { api } from '@/lib/api'
import { FileQuestion, Send, Plus } from 'lucide-react'

interface Questionnaire {
  id: string
  templateName: string
  vendorName: string
  vendorId: string
  status: 'draft' | 'sent' | 'in_progress' | 'completed' | 'expired'
  sentAt: string | null
  completedAt: string | null
  completionRate: number
}

const STATUS_LABELS: Record<string, string> = {
  draft: 'Brouillon',
  sent: 'Envoyé',
  in_progress: 'En cours',
  completed: 'Complété',
  expired: 'Expiré',
}

const STATUS_COLORS: Record<string, string> = {
  draft: '#94A3B8',
  sent: '#2E75B6',
  in_progress: '#F39C12',
  completed: '#27AE60',
  expired: '#C0392B',
}

export default function QuestionnairesPage() {
  const { data: questionnaires } = useQuery({
    queryKey: ['questionnaires'],
    queryFn: () => api.get<Questionnaire[]>('/api/v1/questionnaires'),
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-[#1B3A5C]">
          <FileQuestion className="mr-2 inline h-6 w-6" />
          Questionnaires
        </h1>
        <div className="flex gap-3">
          <button className="inline-flex items-center gap-2 rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium hover:bg-gray-50">
            <Plus className="h-4 w-4" /> Nouveau questionnaire
          </button>
          <button className="inline-flex items-center gap-2 rounded-lg bg-[#2E75B6] px-4 py-2 text-sm font-medium text-white hover:bg-[#1B3A5C]">
            <Send className="h-4 w-4" /> Envoyer
          </button>
        </div>
      </div>

      {/* Templates summary */}
      <div className="grid grid-cols-4 gap-4">
        {['RGPD', 'DORA', 'ISO 27001', 'NIST CSF'].map((tpl) => (
          <Card key={tpl}>
            <CardContent className="p-4 text-center">
              <p className="text-lg font-bold text-[#1B3A5C]">{tpl}</p>
              <p className="text-xs text-gray-500">Template disponible</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Questionnaires list */}
      <Card>
        <CardHeader>
          <CardTitle>Questionnaires envoyés</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-gray-50 text-left text-gray-500">
                <th className="px-4 py-3">Template</th>
                <th className="px-4 py-3">Fournisseur</th>
                <th className="px-4 py-3">Statut</th>
                <th className="px-4 py-3">Completion</th>
                <th className="px-4 py-3">Envoyé le</th>
                <th className="px-4 py-3">Complété le</th>
              </tr>
            </thead>
            <tbody>
              {(questionnaires ?? []).length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-12 text-center text-gray-400">
                    Aucun questionnaire envoyé. Créez-en un pour commencer.
                  </td>
                </tr>
              ) : (
                (questionnaires ?? []).map((q) => (
                  <tr key={q.id} className="border-b hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium">{q.templateName}</td>
                    <td className="px-4 py-3 text-gray-500">{q.vendorName}</td>
                    <td className="px-4 py-3">
                      <Badge style={{ backgroundColor: STATUS_COLORS[q.status], color: '#fff' }}>
                        {STATUS_LABELS[q.status] ?? q.status}
                      </Badge>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="h-2 w-20 overflow-hidden rounded-full bg-gray-200">
                          <div
                            className="h-full rounded-full bg-[#2E75B6]"
                            style={{ width: `${q.completionRate}%` }}
                          />
                        </div>
                        <span className="text-xs text-gray-500">{q.completionRate}%</span>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-gray-500">{q.sentAt ?? '—'}</td>
                    <td className="px-4 py-3 text-gray-500">{q.completedAt ?? '—'}</td>
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
