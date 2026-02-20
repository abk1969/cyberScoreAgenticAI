'use client'

import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { api } from '@/lib/api'
import { useVendors } from '@/hooks/useVendors'
import { FileText, Presentation, Table, Shield, ChevronRight, Loader2, Download } from 'lucide-react'

const REPORT_TYPES = [
  {
    key: 'executive',
    label: 'Rapport Executif COMEX',
    description: 'Synthese 5 pages pour le comite de direction. Score global, tendances, top risques et actions.',
    icon: Presentation,
    audiences: ['COMEX', 'Direction Generale'],
    defaultFormat: 'pptx',
  },
  {
    key: 'rssi',
    label: 'Rapport RSSI Detaille',
    description: 'Analyse complete des 8 domaines avec constats, preuves et recommandations techniques.',
    icon: FileText,
    audiences: ['RSSI', 'Equipe SSI'],
    defaultFormat: 'pdf',
  },
  {
    key: 'vendor_scorecard',
    label: 'Scorecard Fournisseur',
    description: 'Fiche 1 page par fournisseur: score, domaines, constats cles et recommandations.',
    icon: FileText,
    audiences: ['Achats', 'RSSI', 'Fournisseur'],
    defaultFormat: 'pdf',
  },
  {
    key: 'dora_register',
    label: 'Registre DORA (ACPR)',
    description: 'Registre Art.28 DORA: prestataires TIC, criticite, sous-traitants, certifications, plans de sortie.',
    icon: Shield,
    audiences: ['Compliance', 'ACPR'],
    defaultFormat: 'xlsx',
  },
] as const

const FORMAT_OPTIONS = [
  { key: 'pdf', label: 'PDF', icon: FileText },
  { key: 'pptx', label: 'PowerPoint', icon: Presentation },
  { key: 'xlsx', label: 'Excel', icon: Table },
] as const

type ReportType = (typeof REPORT_TYPES)[number]['key']
type ReportFormat = (typeof FORMAT_OPTIONS)[number]['key']

interface GenerateResult {
  message: string
  report_type: string
  format: string
  vendor_id: string | null
  status: string
}

export default function ReportGeneratePage() {
  const [step, setStep] = useState(0)
  const [reportType, setReportType] = useState<ReportType | null>(null)
  const [selectedVendors, setSelectedVendors] = useState<string[]>([])
  const [format, setFormat] = useState<ReportFormat>('pdf')

  const { data: vendors } = useVendors()

  const generateMutation = useMutation({
    mutationFn: (params: { report_type: string; format: string; vendor_id: string | null }) =>
      api.post<GenerateResult>('/api/v1/reports/generate', params),
  })

  const selectedReportConfig = REPORT_TYPES.find((r) => r.key === reportType)

  function handleTypeSelect(key: ReportType) {
    setReportType(key)
    const config = REPORT_TYPES.find((r) => r.key === key)
    if (config) setFormat(config.defaultFormat as ReportFormat)
    setStep(1)
  }

  function handleGenerate() {
    if (!reportType) return
    generateMutation.mutate({
      report_type: reportType,
      format,
      vendor_id: selectedVendors.length === 1 ? selectedVendors[0] : null,
    })
    setStep(3)
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-[#1B3A5C]">Generer un Rapport</h1>

      {/* Progress steps */}
      <div className="flex items-center gap-2 text-sm">
        {['Type de rapport', 'Fournisseurs', 'Format & Generation'].map((label, i) => (
          <div key={label} className="flex items-center gap-2">
            <div
              className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold ${
                i <= step ? 'bg-[#2E75B6] text-white' : 'bg-gray-200 text-gray-500'
              }`}
            >
              {i + 1}
            </div>
            <span className={i <= step ? 'font-medium text-[#1B3A5C]' : 'text-gray-400'}>{label}</span>
            {i < 2 && <ChevronRight className="h-4 w-4 text-gray-300" />}
          </div>
        ))}
      </div>

      {/* Step 0: Select report type */}
      {step === 0 && (
        <div className="grid grid-cols-2 gap-4">
          {REPORT_TYPES.map((rt) => {
            const Icon = rt.icon
            return (
              <Card
                key={rt.key}
                className={`cursor-pointer transition-all hover:border-[#2E75B6] hover:shadow-md ${
                  reportType === rt.key ? 'border-2 border-[#2E75B6] shadow-md' : ''
                }`}
                onClick={() => handleTypeSelect(rt.key)}
              >
                <CardHeader className="pb-2">
                  <CardTitle className="flex items-center gap-3 text-base">
                    <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#1B3A5C]">
                      <Icon className="h-5 w-5 text-white" />
                    </div>
                    {rt.label}
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-gray-500">{rt.description}</p>
                  <div className="mt-3 flex gap-2">
                    {rt.audiences.map((a) => (
                      <Badge key={a} variant="secondary" className="text-xs">
                        {a}
                      </Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}

      {/* Step 1: Select vendors */}
      {step === 1 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Selectionner les fournisseurs</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-3">
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={selectedVendors.length === 0}
                  onChange={() => setSelectedVendors([])}
                  className="rounded border-gray-300"
                />
                Tous les fournisseurs (portfolio)
              </label>
            </div>

            <div className="max-h-60 space-y-2 overflow-y-auto rounded-lg border p-3">
              {(vendors ?? []).map((v: { id: string; name: string }) => (
                <label key={v.id} className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={selectedVendors.includes(v.id)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedVendors([...selectedVendors, v.id])
                      } else {
                        setSelectedVendors(selectedVendors.filter((id) => id !== v.id))
                      }
                    }}
                    className="rounded border-gray-300"
                  />
                  {v.name}
                </label>
              ))}
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => setStep(0)}
                className="rounded-lg border px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-50"
              >
                Retour
              </button>
              <button
                onClick={() => setStep(2)}
                className="rounded-lg bg-[#2E75B6] px-4 py-2 text-sm font-medium text-white hover:bg-[#1B3A5C]"
              >
                Continuer
              </button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Step 2: Format & Generate */}
      {step === 2 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Format et generation</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <p className="mb-3 text-sm font-medium text-gray-700">Format de sortie</p>
              <div className="flex gap-3">
                {FORMAT_OPTIONS.map((fo) => {
                  const Icon = fo.icon
                  return (
                    <button
                      key={fo.key}
                      onClick={() => setFormat(fo.key)}
                      className={`flex items-center gap-2 rounded-lg border-2 px-5 py-3 text-sm font-medium transition-all ${
                        format === fo.key
                          ? 'border-[#2E75B6] bg-blue-50 text-[#2E75B6]'
                          : 'border-gray-200 text-gray-600 hover:border-gray-300'
                      }`}
                    >
                      <Icon className="h-4 w-4" />
                      {fo.label}
                    </button>
                  )
                })}
              </div>
            </div>

            {/* Summary */}
            <div className="rounded-lg bg-[#F7F9FA] p-4 text-sm">
              <p className="font-medium text-[#1B3A5C]">Resume</p>
              <div className="mt-2 space-y-1 text-gray-600">
                <p>Type: <span className="font-medium">{selectedReportConfig?.label}</span></p>
                <p>Fournisseurs: <span className="font-medium">{selectedVendors.length || 'Tous'}</span></p>
                <p>Format: <span className="font-medium">{format.toUpperCase()}</span></p>
              </div>
            </div>

            <div className="flex gap-3">
              <button
                onClick={() => setStep(1)}
                className="rounded-lg border px-4 py-2 text-sm font-medium text-gray-600 hover:bg-gray-50"
              >
                Retour
              </button>
              <button
                onClick={handleGenerate}
                className="flex items-center gap-2 rounded-lg bg-[#2E75B6] px-6 py-2 text-sm font-medium text-white hover:bg-[#1B3A5C]"
              >
                <Download className="h-4 w-4" />
                Generer le rapport
              </button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Step 3: Result */}
      {step === 3 && (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            {generateMutation.isPending && (
              <>
                <Loader2 className="h-12 w-12 animate-spin text-[#2E75B6]" />
                <p className="mt-4 text-lg font-medium text-[#1B3A5C]">Generation en cours...</p>
                <p className="text-sm text-gray-500">Le rapport est en cours de generation.</p>
              </>
            )}
            {generateMutation.isSuccess && (
              <>
                <div className="flex h-16 w-16 items-center justify-center rounded-full bg-green-100">
                  <FileText className="h-8 w-8 text-[#27AE60]" />
                </div>
                <p className="mt-4 text-lg font-medium text-[#1B3A5C]">Rapport genere</p>
                <p className="text-sm text-gray-500">
                  {generateMutation.data?.message ?? 'Le rapport sera disponible sous peu.'}
                </p>
                <button
                  onClick={() => { setStep(0); generateMutation.reset() }}
                  className="mt-6 rounded-lg bg-[#2E75B6] px-6 py-2 text-sm font-medium text-white hover:bg-[#1B3A5C]"
                >
                  Generer un autre rapport
                </button>
              </>
            )}
            {generateMutation.isError && (
              <>
                <div className="flex h-16 w-16 items-center justify-center rounded-full bg-red-100">
                  <FileText className="h-8 w-8 text-[#C0392B]" />
                </div>
                <p className="mt-4 text-lg font-medium text-[#C0392B]">Erreur</p>
                <p className="text-sm text-gray-500">La generation du rapport a echoue.</p>
                <button
                  onClick={() => { setStep(2); generateMutation.reset() }}
                  className="mt-6 rounded-lg border px-6 py-2 text-sm font-medium text-gray-600 hover:bg-gray-50"
                >
                  Reessayer
                </button>
              </>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
