'use client'

import { useState, useEffect } from 'react'
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  Tooltip,
  Legend,
} from 'recharts'
import { usePortfolioBenchmark } from '@/hooks/useBenchmark'

const SECTORS = [
  { key: 'mutuelle', label: 'Mutuelle' },
  { key: 'assurance', label: 'Assurance' },
  { key: 'sante', label: 'Sante' },
  { key: 'banque', label: 'Banque' },
  { key: 'industrie', label: 'Industrie' },
]

const DOMAIN_SHORT: Record<string, string> = {
  D1: 'Reseau',
  D2: 'DNS',
  D3: 'Web',
  D4: 'Email',
  D5: 'Patching',
  D6: 'IP Rep.',
  D7: 'Fuites',
  D8: 'Reglementaire',
}

interface BenchmarkRadarProps {
  height?: number
  className?: string
}

export function BenchmarkRadar({ height = 380, className }: BenchmarkRadarProps) {
  const [mounted, setMounted] = useState(false)
  useEffect(() => setMounted(true), [])

  const [sector, setSector] = useState('mutuelle')
  const { data: benchmark, isLoading } = usePortfolioBenchmark(sector)

  const chartData = (benchmark?.domain_comparison ?? []).map((d) => ({
    domain: DOMAIN_SHORT[d.code] ?? d.code,
    portfolio: d.portfolio_avg ?? 0,
    sector: d.sector_avg,
  }))

  if (!mounted) return null

  return (
    <div className={className}>
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-[#1B3A5C]">Benchmark Sectoriel</h3>
        <select
          value={sector}
          onChange={(e) => setSector(e.target.value)}
          className="rounded-md border border-gray-300 bg-white px-3 py-1 text-xs text-[#2C3E50] focus:border-[#2E75B6] focus:outline-none focus:ring-1 focus:ring-[#2E75B6]"
        >
          {SECTORS.map((s) => (
            <option key={s.key} value={s.key}>
              {s.label}
            </option>
          ))}
        </select>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center" style={{ height }}>
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-[#2E75B6] border-t-transparent" />
        </div>
      ) : (
        <>
          <ResponsiveContainer width="100%" height={height}>
            <RadarChart data={chartData} cx="50%" cy="50%" outerRadius="70%">
              <PolarGrid stroke="#E2E8F0" />
              <PolarAngleAxis dataKey="domain" tick={{ fill: '#2C3E50', fontSize: 11 }} />
              <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fill: '#94A3B8', fontSize: 10 }} tickCount={5} />
              <Radar
                name="Portfolio"
                dataKey="portfolio"
                stroke="#2E75B6"
                fill="#2E75B6"
                fillOpacity={0.2}
                strokeWidth={2}
              />
              <Radar
                name={`Moyenne ${SECTORS.find((s) => s.key === sector)?.label ?? sector}`}
                dataKey="sector"
                stroke="#E67E22"
                fill="#E67E22"
                fillOpacity={0.1}
                strokeWidth={2}
                strokeDasharray="5 5"
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#fff',
                  border: '1px solid #E2E8F0',
                  borderRadius: '8px',
                  fontSize: '12px',
                }}
                formatter={(value: number, name: string) => [`${value}/100`, name]}
              />
              <Legend
                wrapperStyle={{ fontSize: '11px', paddingTop: '8px' }}
                iconType="line"
              />
            </RadarChart>
          </ResponsiveContainer>

          {benchmark && (
            <div className="mt-2 flex items-center justify-center gap-6 text-xs text-gray-500">
              <span>
                Portfolio:{' '}
                <span className="font-bold text-[#2E75B6]">{benchmark.portfolio_avg_score}</span>
              </span>
              <span>
                Secteur:{' '}
                <span className="font-bold text-[#E67E22]">{benchmark.sector_avg}</span>
              </span>
              <span
                className={`font-bold ${benchmark.delta >= 0 ? 'text-[#27AE60]' : 'text-[#C0392B]'}`}
              >
                {benchmark.delta >= 0 ? '+' : ''}
                {benchmark.delta} pts
              </span>
            </div>
          )}
        </>
      )}
    </div>
  )
}
