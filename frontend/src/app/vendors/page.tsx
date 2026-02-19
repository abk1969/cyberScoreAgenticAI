'use client'

import Link from 'next/link'
import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { useVendors } from '@/hooks/useVendors'
import { gradeToColor } from '@/lib/scoring-utils'
import { Search, ExternalLink } from 'lucide-react'

export default function VendorsPage() {
  const { data: vendors } = useVendors()
  const [search, setSearch] = useState('')
  const [tierFilter, setTierFilter] = useState<number | null>(null)

  const filtered = (vendors ?? []).filter((v) => {
    const matchSearch = v.name.toLowerCase().includes(search.toLowerCase()) ||
      v.domain.toLowerCase().includes(search.toLowerCase())
    const matchTier = tierFilter === null || v.tier === tierFilter
    return matchSearch && matchTier
  })

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-[#1B3A5C]">Fournisseurs</h1>

      {/* Filters */}
      <div className="flex items-center gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
          <Input
            placeholder="Rechercher par nom ou domaine..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10"
          />
        </div>
        <div className="flex gap-2">
          {[null, 1, 2, 3].map((tier) => (
            <button
              key={tier ?? 'all'}
              onClick={() => setTierFilter(tier)}
              className={`rounded-lg px-3 py-1.5 text-sm font-medium transition-colors ${
                tierFilter === tier
                  ? 'bg-[#2E75B6] text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {tier === null ? 'Tous' : `Tier ${tier}`}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <Card>
        <CardContent className="p-0">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-gray-50 text-left text-gray-500">
                <th className="px-4 py-3">Nom</th>
                <th className="px-4 py-3">Domaine</th>
                <th className="px-4 py-3">Tier</th>
                <th className="px-4 py-3">Industrie</th>
                <th className="px-4 py-3">Score</th>
                <th className="px-4 py-3">Grade</th>
                <th className="px-4 py-3">Dernière analyse</th>
                <th className="px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((v) => (
                <tr key={v.id} className="border-b hover:bg-gray-50">
                  <td className="px-4 py-3 font-medium">{v.name}</td>
                  <td className="px-4 py-3 text-gray-500">{v.domain}</td>
                  <td className="px-4 py-3">
                    <Badge variant="outline" className="text-xs">Tier {v.tier}</Badge>
                  </td>
                  <td className="px-4 py-3 text-gray-500">{v.industry}</td>
                  <td className="px-4 py-3 font-mono font-bold">{v.score}</td>
                  <td className="px-4 py-3">
                    <Badge style={{ backgroundColor: gradeToColor(v.grade), color: '#fff' }}>
                      {v.grade}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-gray-500">{v.lastScanDate}</td>
                  <td className="px-4 py-3">
                    <Link
                      href={`/vendors/${v.id}`}
                      className="inline-flex items-center gap-1 text-[#2E75B6] hover:underline"
                    >
                      Voir <ExternalLink className="h-3 w-3" />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  )
}
