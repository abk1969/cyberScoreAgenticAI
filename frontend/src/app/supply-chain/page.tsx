'use client'

import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { SupplyChainGraph } from '@/components/charts/SupplyChainGraph'
import { api } from '@/lib/api'
import { Network } from 'lucide-react'
import type { SupplyChainGraphData } from '@/types/chart'

export default function SupplyChainPage() {
  const { data: graphData } = useQuery({
    queryKey: ['supply-chain-graph'],
    queryFn: () => api.get<SupplyChainGraphData>('/api/v1/supply-chain/graph'),
  })

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-[#1B3A5C]">
        <Network className="mr-2 inline h-6 w-6" />
        Cartographie Supply Chain
      </h1>

      <Card>
        <CardHeader>
          <CardTitle>Graphe de dependances N-tiers</CardTitle>
        </CardHeader>
        <CardContent>
          {graphData && graphData.nodes.length > 0 ? (
            <SupplyChainGraph data={graphData} width={900} height={600} />
          ) : (
            <div className="flex flex-col items-center justify-center py-20">
              <Network className="mb-4 h-16 w-16 text-gray-300" />
              <h3 className="text-lg font-semibold text-gray-400">
                Aucune donnee de supply chain disponible
              </h3>
              <p className="mt-2 text-sm text-gray-400">
                Lancez un scan Nth-Party pour generer le graphe de dependances.
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
