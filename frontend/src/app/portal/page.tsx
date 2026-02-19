'use client'

import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ScoreGauge } from '@/components/charts/ScoreGauge'
import { api } from '@/lib/api'
import { gradeToColor } from '@/lib/scoring-utils'
import { Globe, Upload, MessageSquare, FileText } from 'lucide-react'

interface PortalData {
  vendor: {
    id: string
    name: string
    domain: string
    score: number
    grade: string
  }
  pendingDisputes: number
  pendingQuestionnaires: number
  findings: {
    id: string
    title: string
    severity: string
    status: string
    domain: string
  }[]
}

export default function PortalPage() {
  const { data: portal } = useQuery({
    queryKey: ['portal'],
    queryFn: () => api.get<PortalData>('/api/v1/portal'),
  })

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-[#1B3A5C]">
        <Globe className="mr-2 inline h-6 w-6" />
        Portail Fournisseur
      </h1>

      {!portal ? (
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
                <h2 className="text-xl font-bold text-[#1B3A5C]">{portal.vendor.name}</h2>
                <p className="text-gray-500">{portal.vendor.domain}</p>
              </div>
              <div className="flex items-center gap-6">
                <ScoreGauge score={portal.vendor.score} size={140} />
                <Badge
                  className="px-4 py-2 text-2xl"
                  style={{ backgroundColor: gradeToColor(portal.vendor.grade as 'A' | 'B' | 'C' | 'D' | 'F'), color: '#fff' }}
                >
                  {portal.vendor.grade}
                </Badge>
              </div>
            </CardContent>
          </Card>

          {/* Actions */}
          <div className="grid grid-cols-3 gap-4">
            <Card className="cursor-pointer transition-shadow hover:shadow-md">
              <CardContent className="flex flex-col items-center p-6">
                <MessageSquare className="mb-2 h-8 w-8 text-[#2E75B6]" />
                <p className="font-semibold text-[#1B3A5C]">Contester un finding</p>
                <p className="mt-1 text-xs text-gray-500">
                  {portal.pendingDisputes} contestation(s) en cours
                </p>
              </CardContent>
            </Card>

            <Card className="cursor-pointer transition-shadow hover:shadow-md">
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
                  {portal.pendingQuestionnaires} questionnaire(s) a remplir
                </p>
              </CardContent>
            </Card>
          </div>

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
                  {portal.findings.map((f) => (
                    <tr key={f.id} className="border-b hover:bg-gray-50">
                      <td className="px-4 py-3 font-medium">{f.title}</td>
                      <td className="px-4 py-3 text-gray-500">{f.domain}</td>
                      <td className="px-4 py-3">
                        <Badge variant="outline">{f.severity}</Badge>
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant="outline">{f.status}</Badge>
                      </td>
                      <td className="px-4 py-3">
                        <button className="text-xs text-[#2E75B6] hover:underline">
                          Contester
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
