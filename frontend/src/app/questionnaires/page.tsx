'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { FileQuestion, Send, Plus, ChevronRight, Loader2 } from 'lucide-react'
import {
  useQuestionnaires,
  useQuestionnaireTemplates,
  useCreateQuestionnaire,
} from '@/hooks/useQuestionnaires'

const STATUS_LABELS: Record<string, string> = {
  draft: 'Brouillon',
  sent: 'Envoye',
  in_progress: 'En cours',
  completed: 'Complete',
  expired: 'Expire',
}

const STATUS_COLORS: Record<string, string> = {
  draft: '#94A3B8',
  sent: '#2E75B6',
  in_progress: '#F39C12',
  completed: '#27AE60',
  expired: '#C0392B',
}

export default function QuestionnairesPage() {
  const { data: questionnaires, isLoading: loadingList } = useQuestionnaires()
  const { data: templates, isLoading: loadingTemplates } = useQuestionnaireTemplates()
  const createQuestionnaire = useCreateQuestionnaire()
  const [showCreate, setShowCreate] = useState(false)
  const [selectedTemplate, setSelectedTemplate] = useState('')
  const [vendorId, setVendorId] = useState('')

  const handleCreate = () => {
    if (!selectedTemplate || !vendorId) return
    createQuestionnaire.mutate(
      { template_name: selectedTemplate, vendor_id: vendorId },
      { onSuccess: () => { setShowCreate(false); setSelectedTemplate(''); setVendorId('') } }
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-[#1B3A5C]">
          <FileQuestion className="mr-2 inline h-6 w-6" />
          Questionnaires
        </h1>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="inline-flex items-center gap-2 rounded-lg bg-[#2E75B6] px-4 py-2 text-sm font-medium text-white hover:bg-[#1B3A5C]"
        >
          <Plus className="h-4 w-4" /> Nouveau questionnaire
        </button>
      </div>

      {/* Create form */}
      {showCreate && (
        <Card>
          <CardHeader>
            <CardTitle>Creer un questionnaire</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">Template</label>
              <select
                value={selectedTemplate}
                onChange={(e) => setSelectedTemplate(e.target.value)}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
              >
                <option value="">Choisir un template...</option>
                {(templates ?? []).map((t) => (
                  <option key={t.name} value={t.name}>
                    {t.name} — {t.description} ({t.question_count} questions)
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">ID Fournisseur</label>
              <input
                type="text"
                value={vendorId}
                onChange={(e) => setVendorId(e.target.value)}
                placeholder="UUID du fournisseur"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
              />
            </div>
            <div className="flex gap-3">
              <button
                onClick={handleCreate}
                disabled={createQuestionnaire.isPending || !selectedTemplate || !vendorId}
                className="inline-flex items-center gap-2 rounded-lg bg-[#27AE60] px-4 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50"
              >
                {createQuestionnaire.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
                Creer
              </button>
              <button
                onClick={() => setShowCreate(false)}
                className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium hover:bg-gray-50"
              >
                Annuler
              </button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Templates summary */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-5">
        {loadingTemplates ? (
          <div className="col-span-full flex justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
          </div>
        ) : (
          (templates ?? []).map((tpl) => (
            <Card key={tpl.name} className="cursor-pointer hover:shadow-md transition-shadow">
              <CardContent className="p-4 text-center">
                <p className="text-lg font-bold text-[#1B3A5C]">{tpl.name}</p>
                <p className="text-xs text-gray-500">{tpl.question_count} questions</p>
                <p className="mt-1 text-xs text-gray-400">{tpl.category}</p>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      {/* Questionnaires list */}
      <Card>
        <CardHeader>
          <CardTitle>Questionnaires</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {loadingList ? (
            <div className="flex justify-center py-12">
              <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-gray-50 text-left text-gray-500">
                  <th className="px-4 py-3">Titre</th>
                  <th className="px-4 py-3">Categorie</th>
                  <th className="px-4 py-3">Version</th>
                  <th className="px-4 py-3">Statut</th>
                  <th className="px-4 py-3">Cree le</th>
                  <th className="px-4 py-3"></th>
                </tr>
              </thead>
              <tbody>
                {(questionnaires ?? []).length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-4 py-12 text-center text-gray-400">
                      Aucun questionnaire. Creez-en un pour commencer.
                    </td>
                  </tr>
                ) : (
                  (questionnaires ?? []).map((q) => (
                    <tr key={q.id} className="border-b hover:bg-gray-50">
                      <td className="px-4 py-3 font-medium">{q.title}</td>
                      <td className="px-4 py-3 text-gray-500">{q.category ?? '—'}</td>
                      <td className="px-4 py-3 text-gray-500">{q.version}</td>
                      <td className="px-4 py-3">
                        <Badge
                          style={{
                            backgroundColor: q.is_active ? '#27AE60' : '#94A3B8',
                            color: '#fff',
                          }}
                        >
                          {q.is_active ? 'Actif' : 'Inactif'}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-gray-500">
                        {new Date(q.created_at).toLocaleDateString('fr-FR')}
                      </td>
                      <td className="px-4 py-3">
                        <Link
                          href={`/questionnaires/${q.id}`}
                          className="inline-flex items-center gap-1 text-[#2E75B6] hover:underline"
                        >
                          Voir <ChevronRight className="h-4 w-4" />
                        </Link>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
