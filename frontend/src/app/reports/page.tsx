'use client'

import { useQuery } from '@tanstack/react-query'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { api } from '@/lib/api'
import { FileText, Download } from 'lucide-react'

interface Report {
  id: string
  type: string
  format: string
  vendor: string
  date: string
  size: string
  downloadUrl: string
}

interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  pages: number
}

const formatIcons: Record<string, string> = { pdf: 'PDF', pptx: 'PPTX', xlsx: 'XLSX' }

export default function ReportsPage() {
  const { data: reports } = useQuery({
    queryKey: ['reports'],
    queryFn: async () => {
      const res = await api.get<PaginatedResponse<Report>>('/api/v1/reports')
      return res.items
    },
  })

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-[#1B3A5C]">Rapports</h1>
        <button className="inline-flex items-center gap-2 rounded-lg bg-[#2E75B6] px-4 py-2 text-sm font-medium text-white hover:bg-[#1B3A5C]">
          <FileText className="h-4 w-4" /> Generer un rapport
        </button>
      </div>

      <Card>
        <CardContent className="p-0">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-gray-50 text-left text-gray-500">
                <th className="px-4 py-3">Type</th>
                <th className="px-4 py-3">Format</th>
                <th className="px-4 py-3">Fournisseur</th>
                <th className="px-4 py-3">Date</th>
                <th className="px-4 py-3">Taille</th>
                <th className="px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {(reports ?? []).length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-4 py-12 text-center text-gray-400">
                    Aucun rapport disponible. Generez-en un pour commencer.
                  </td>
                </tr>
              ) : (
                (reports ?? []).map((r) => (
                  <tr key={r.id} className="border-b hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium">{r.type}</td>
                    <td className="px-4 py-3">
                      <Badge variant="outline">{formatIcons[r.format] ?? r.format.toUpperCase()}</Badge>
                    </td>
                    <td className="px-4 py-3 text-gray-500">{r.vendor}</td>
                    <td className="px-4 py-3 text-gray-500">{r.date}</td>
                    <td className="px-4 py-3 text-gray-500">{r.size}</td>
                    <td className="px-4 py-3">
                      <a
                        href={r.downloadUrl}
                        className="inline-flex items-center gap-1 text-[#2E75B6] hover:underline"
                      >
                        <Download className="h-3 w-3" /> Telecharger
                      </a>
                    </td>
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
