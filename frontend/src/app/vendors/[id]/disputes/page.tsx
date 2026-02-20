'use client'

import { useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  AlertTriangle,
  ArrowLeft,
  Plus,
  Loader2,
  Clock,
  CheckCircle,
  XCircle,
  Search,
} from 'lucide-react'
import {
  useDisputes,
  useCreateDispute,
  useResolveDispute,
  useRemediations,
  useCreateRemediation,
} from '@/hooks/useVRM'

const DISPUTE_STATUS_LABELS: Record<string, string> = {
  open: 'Ouvert',
  in_review: 'En examen',
  resolved: 'Resolu',
  rejected: 'Rejete',
}

const DISPUTE_STATUS_COLORS: Record<string, string> = {
  open: '#F39C12',
  in_review: '#2E75B6',
  resolved: '#27AE60',
  rejected: '#C0392B',
}

const PRIORITY_LABELS: Record<string, string> = {
  critical: 'Critique',
  high: 'Eleve',
  medium: 'Moyen',
  low: 'Faible',
}

const PRIORITY_COLORS: Record<string, string> = {
  critical: '#C0392B',
  high: '#E67E22',
  medium: '#F39C12',
  low: '#27AE60',
}

const REMEDIATION_STATUS_LABELS: Record<string, string> = {
  pending: 'En attente',
  in_progress: 'En cours',
  completed: 'Termine',
  overdue: 'En retard',
}

export default function VendorDisputesPage() {
  const params = useParams()
  const router = useRouter()
  const vendorId = params.id as string

  const { data: disputes, isLoading: loadingDisputes } = useDisputes(vendorId)
  const { data: remediations, isLoading: loadingRemediations } = useRemediations(vendorId)
  const createDispute = useCreateDispute(vendorId)
  const resolveDispute = useResolveDispute()
  const createRemediation = useCreateRemediation(vendorId)

  const [showDisputeForm, setShowDisputeForm] = useState(false)
  const [showRemediationForm, setShowRemediationForm] = useState(false)

  // Dispute form state
  const [findingId, setFindingId] = useState('')
  const [evidenceUrl, setEvidenceUrl] = useState('')
  const [requesterEmail, setRequesterEmail] = useState('')

  // Remediation form state
  const [remTitle, setRemTitle] = useState('')
  const [remDescription, setRemDescription] = useState('')
  const [remPriority, setRemPriority] = useState('medium')
  const [remDeadline, setRemDeadline] = useState('')
  const [remAssignedTo, setRemAssignedTo] = useState('')

  const handleCreateDispute = () => {
    if (!findingId || !requesterEmail) return
    createDispute.mutate(
      {
        finding_id: findingId,
        evidence_url: evidenceUrl || undefined,
        requester_email: requesterEmail,
      },
      {
        onSuccess: () => {
          setShowDisputeForm(false)
          setFindingId('')
          setEvidenceUrl('')
          setRequesterEmail('')
        },
      }
    )
  }

  const handleCreateRemediation = () => {
    if (!remTitle || !remDescription || !remDeadline) return
    createRemediation.mutate(
      {
        title: remTitle,
        description: remDescription,
        priority: remPriority,
        deadline: new Date(remDeadline).toISOString(),
        assigned_to: remAssignedTo || undefined,
      },
      {
        onSuccess: () => {
          setShowRemediationForm(false)
          setRemTitle('')
          setRemDescription('')
          setRemPriority('medium')
          setRemDeadline('')
          setRemAssignedTo('')
        },
      }
    )
  }

  const handleResolve = (disputeId: string, status: string) => {
    resolveDispute.mutate({ disputeId, data: { status } })
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => router.back()}
          className="rounded-lg border border-gray-300 p-2 hover:bg-gray-50"
        >
          <ArrowLeft className="h-4 w-4" />
        </button>
        <h1 className="text-2xl font-bold text-[#1B3A5C]">
          <AlertTriangle className="mr-2 inline h-6 w-6" />
          Contestations & Remediation
        </h1>
      </div>

      {/* Disputes section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-[#1B3A5C]">Contestations</h2>
          <button
            onClick={() => setShowDisputeForm(!showDisputeForm)}
            className="inline-flex items-center gap-2 rounded-lg bg-[#2E75B6] px-4 py-2 text-sm font-medium text-white hover:bg-[#1B3A5C]"
          >
            <Plus className="h-4 w-4" /> Nouvelle contestation
          </button>
        </div>

        {/* Create dispute form */}
        {showDisputeForm && (
          <Card>
            <CardContent className="space-y-3 p-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">
                    ID du finding
                  </label>
                  <input
                    type="text"
                    value={findingId}
                    onChange={(e) => setFindingId(e.target.value)}
                    placeholder="UUID du finding conteste"
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">
                    Email du demandeur
                  </label>
                  <input
                    type="email"
                    value={requesterEmail}
                    onChange={(e) => setRequesterEmail(e.target.value)}
                    placeholder="demandeur@example.com"
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                  />
                </div>
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">
                  URL de la preuve (optionnel)
                </label>
                <input
                  type="url"
                  value={evidenceUrl}
                  onChange={(e) => setEvidenceUrl(e.target.value)}
                  placeholder="https://..."
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                />
              </div>
              <div className="flex gap-3">
                <button
                  onClick={handleCreateDispute}
                  disabled={createDispute.isPending || !findingId || !requesterEmail}
                  className="inline-flex items-center gap-2 rounded-lg bg-[#27AE60] px-4 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50"
                >
                  {createDispute.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
                  Creer
                </button>
                <button
                  onClick={() => setShowDisputeForm(false)}
                  className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium hover:bg-gray-50"
                >
                  Annuler
                </button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Disputes list */}
        <Card>
          <CardContent className="p-0">
            {loadingDisputes ? (
              <div className="flex justify-center py-12">
                <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
              </div>
            ) : (disputes ?? []).length === 0 ? (
              <div className="px-4 py-12 text-center text-gray-400">
                Aucune contestation pour ce fournisseur.
              </div>
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-gray-50 text-left text-gray-500">
                    <th className="px-4 py-3">Finding</th>
                    <th className="px-4 py-3">Statut</th>
                    <th className="px-4 py-3">Demandeur</th>
                    <th className="px-4 py-3">SLA</th>
                    <th className="px-4 py-3">Cree le</th>
                    <th className="px-4 py-3">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {(disputes ?? []).map((d) => (
                    <tr key={d.id} className="border-b hover:bg-gray-50">
                      <td className="px-4 py-3 font-mono text-xs">{d.finding_id.slice(0, 8)}...</td>
                      <td className="px-4 py-3">
                        <Badge
                          style={{
                            backgroundColor: DISPUTE_STATUS_COLORS[d.status],
                            color: '#fff',
                          }}
                        >
                          {DISPUTE_STATUS_LABELS[d.status] ?? d.status}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-gray-500">{d.requester_email}</td>
                      <td className="px-4 py-3 text-gray-500">
                        <div className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          {new Date(d.sla_deadline).toLocaleDateString('fr-FR')}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-gray-500">
                        {new Date(d.created_at).toLocaleDateString('fr-FR')}
                      </td>
                      <td className="px-4 py-3">
                        {d.status === 'open' && (
                          <div className="flex gap-1">
                            <button
                              onClick={() => handleResolve(d.id, 'in_review')}
                              className="rounded px-2 py-1 text-xs text-blue-600 hover:bg-blue-50"
                            >
                              <Search className="inline h-3 w-3" /> Examiner
                            </button>
                          </div>
                        )}
                        {d.status === 'in_review' && (
                          <div className="flex gap-1">
                            <button
                              onClick={() => handleResolve(d.id, 'resolved')}
                              className="rounded px-2 py-1 text-xs text-green-600 hover:bg-green-50"
                            >
                              <CheckCircle className="inline h-3 w-3" /> Resoudre
                            </button>
                            <button
                              onClick={() => handleResolve(d.id, 'rejected')}
                              className="rounded px-2 py-1 text-xs text-red-600 hover:bg-red-50"
                            >
                              <XCircle className="inline h-3 w-3" /> Rejeter
                            </button>
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Remediation section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-[#1B3A5C]">Plan de remediation</h2>
          <button
            onClick={() => setShowRemediationForm(!showRemediationForm)}
            className="inline-flex items-center gap-2 rounded-lg border border-[#2E75B6] px-4 py-2 text-sm font-medium text-[#2E75B6] hover:bg-blue-50"
          >
            <Plus className="h-4 w-4" /> Ajouter une action
          </button>
        </div>

        {/* Create remediation form */}
        {showRemediationForm && (
          <Card>
            <CardContent className="space-y-3 p-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">Titre</label>
                  <input
                    type="text"
                    value={remTitle}
                    onChange={(e) => setRemTitle(e.target.value)}
                    placeholder="Titre de l'action"
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">Priorite</label>
                  <select
                    value={remPriority}
                    onChange={(e) => setRemPriority(e.target.value)}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                  >
                    <option value="critical">Critique</option>
                    <option value="high">Eleve</option>
                    <option value="medium">Moyen</option>
                    <option value="low">Faible</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">Description</label>
                <textarea
                  value={remDescription}
                  onChange={(e) => setRemDescription(e.target.value)}
                  placeholder="Description de l'action de remediation"
                  rows={3}
                  className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">Echeance</label>
                  <input
                    type="date"
                    value={remDeadline}
                    onChange={(e) => setRemDeadline(e.target.value)}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                  />
                </div>
                <div>
                  <label className="mb-1 block text-sm font-medium text-gray-700">
                    Assigne a (optionnel)
                  </label>
                  <input
                    type="text"
                    value={remAssignedTo}
                    onChange={(e) => setRemAssignedTo(e.target.value)}
                    placeholder="Nom ou email"
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                  />
                </div>
              </div>
              <div className="flex gap-3">
                <button
                  onClick={handleCreateRemediation}
                  disabled={
                    createRemediation.isPending || !remTitle || !remDescription || !remDeadline
                  }
                  className="inline-flex items-center gap-2 rounded-lg bg-[#27AE60] px-4 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50"
                >
                  {createRemediation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
                  Creer
                </button>
                <button
                  onClick={() => setShowRemediationForm(false)}
                  className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-medium hover:bg-gray-50"
                >
                  Annuler
                </button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Remediations list */}
        <Card>
          <CardContent className="p-0">
            {loadingRemediations ? (
              <div className="flex justify-center py-12">
                <Loader2 className="h-6 w-6 animate-spin text-gray-400" />
              </div>
            ) : (remediations ?? []).length === 0 ? (
              <div className="px-4 py-12 text-center text-gray-400">
                Aucune action de remediation pour ce fournisseur.
              </div>
            ) : (
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-gray-50 text-left text-gray-500">
                    <th className="px-4 py-3">Titre</th>
                    <th className="px-4 py-3">Priorite</th>
                    <th className="px-4 py-3">Statut</th>
                    <th className="px-4 py-3">Echeance</th>
                    <th className="px-4 py-3">Assigne a</th>
                  </tr>
                </thead>
                <tbody>
                  {(remediations ?? []).map((r) => (
                    <tr key={r.id} className="border-b hover:bg-gray-50">
                      <td className="px-4 py-3 font-medium">{r.title}</td>
                      <td className="px-4 py-3">
                        <Badge
                          style={{
                            backgroundColor: PRIORITY_COLORS[r.priority],
                            color: '#fff',
                          }}
                        >
                          {PRIORITY_LABELS[r.priority] ?? r.priority}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-gray-500">
                        {REMEDIATION_STATUS_LABELS[r.status] ?? r.status}
                      </td>
                      <td className="px-4 py-3 text-gray-500">
                        {new Date(r.deadline).toLocaleDateString('fr-FR')}
                      </td>
                      <td className="px-4 py-3 text-gray-500">{r.assigned_to ?? '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
