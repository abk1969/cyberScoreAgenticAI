'use client'

import Link from 'next/link'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { useADScore, useM365Score, useGRCMaturity } from '@/hooks/useInternal'
import { Shield, Server, Cloud, FileCheck } from 'lucide-react'

const GRADE_COLORS: Record<string, string> = {
  A: '#27AE60',
  B: '#2ECC71',
  C: '#F39C12',
  D: '#E67E22',
  F: '#C0392B',
}

function ScoreCard({
  title,
  icon: Icon,
  score,
  grade,
  findingsCount,
  href,
  loading,
}: {
  title: string
  icon: typeof Shield
  score: number | undefined
  grade: string | undefined
  findingsCount: number | undefined
  href: string
  loading: boolean
}) {
  return (
    <Link href={href}>
      <Card className="transition-shadow hover:shadow-lg cursor-pointer">
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-lg">{title}</CardTitle>
          <Icon className="h-6 w-6 text-[#2E75B6]" />
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="animate-pulse space-y-2">
              <div className="h-10 bg-gray-200 rounded w-24" />
              <div className="h-4 bg-gray-200 rounded w-32" />
            </div>
          ) : score !== undefined ? (
            <>
              <div className="flex items-baseline gap-3">
                <span className="text-4xl font-bold text-[#1B3A5C]">{score}</span>
                <span className="text-sm text-gray-500">/ 1000</span>
                {grade && (
                  <Badge
                    className="text-white text-lg px-3 py-1"
                    style={{ backgroundColor: GRADE_COLORS[grade] ?? '#6B7280' }}
                  >
                    {grade}
                  </Badge>
                )}
              </div>
              <p className="mt-2 text-sm text-gray-500">
                {findingsCount ?? 0} findings detectes
              </p>
            </>
          ) : (
            <p className="text-sm text-gray-400">Aucun scan disponible</p>
          )}
        </CardContent>
      </Card>
    </Link>
  )
}

export default function InternalOverviewPage() {
  const { data: adScore, isLoading: adLoading } = useADScore()
  const { data: m365Score, isLoading: m365Loading } = useM365Score()
  const { data: maturity, isLoading: grcLoading } = useGRCMaturity()

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-[#1B3A5C]">Scoring Interne</h1>
      <p className="text-gray-600">
        Vue consolidee de la securite interne : Active Directory, Microsoft 365 et conformite GRC/PSSI.
      </p>

      <div className="grid grid-cols-3 gap-6">
        <ScoreCard
          title="AD Rating"
          icon={Server}
          score={adScore?.score}
          grade={adScore?.grade}
          findingsCount={adScore?.findings_count}
          href="/internal/ad"
          loading={adLoading}
        />

        <ScoreCard
          title="M365 Rating"
          icon={Cloud}
          score={m365Score?.score}
          grade={m365Score?.grade}
          findingsCount={m365Score?.findings_count}
          href="/internal/m365"
          loading={m365Loading}
        />

        <Link href="/internal/grc">
          <Card className="transition-shadow hover:shadow-lg cursor-pointer">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-lg">GRC / PSSI</CardTitle>
              <FileCheck className="h-6 w-6 text-[#2E75B6]" />
            </CardHeader>
            <CardContent>
              {grcLoading ? (
                <div className="animate-pulse space-y-2">
                  <div className="h-10 bg-gray-200 rounded w-24" />
                  <div className="h-4 bg-gray-200 rounded w-32" />
                </div>
              ) : maturity ? (
                <>
                  <div className="flex items-baseline gap-3">
                    <span className="text-4xl font-bold text-[#1B3A5C]">
                      {maturity.overall_maturity.toFixed(1)}
                    </span>
                    <span className="text-sm text-gray-500">/ 5.0</span>
                  </div>
                  <p className="mt-2 text-sm text-gray-500">
                    Maturite moyenne sur {maturity.domain_count} domaines
                  </p>
                </>
              ) : (
                <p className="text-sm text-gray-400">Aucune evaluation disponible</p>
              )}
            </CardContent>
          </Card>
        </Link>
      </div>

      {/* Category breakdown cards */}
      <div className="grid grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Categories AD</CardTitle>
          </CardHeader>
          <CardContent>
            {adScore?.category_scores ? (
              <div className="space-y-3">
                {Object.entries(adScore.category_scores).map(([cat, score]) => (
                  <div key={cat} className="flex items-center justify-between">
                    <span className="text-sm capitalize">{cat.replace(/_/g, ' ')}</span>
                    <div className="flex items-center gap-2">
                      <div className="h-2 w-32 rounded-full bg-gray-200">
                        <div
                          className="h-2 rounded-full"
                          style={{
                            width: `${Math.min(100, (score as number))}%`,
                            backgroundColor: (score as number) >= 80 ? '#27AE60' : (score as number) >= 50 ? '#F39C12' : '#C0392B',
                          }}
                        />
                      </div>
                      <span className="text-sm font-mono w-10 text-right">{(score as number).toFixed(0)}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-400">Pas de donnees AD</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Categories M365</CardTitle>
          </CardHeader>
          <CardContent>
            {m365Score?.category_scores ? (
              <div className="space-y-3">
                {Object.entries(m365Score.category_scores).map(([cat, score]) => (
                  <div key={cat} className="flex items-center justify-between">
                    <span className="text-sm capitalize">{cat.replace(/_/g, ' ')}</span>
                    <div className="flex items-center gap-2">
                      <div className="h-2 w-32 rounded-full bg-gray-200">
                        <div
                          className="h-2 rounded-full"
                          style={{
                            width: `${Math.min(100, (score as number))}%`,
                            backgroundColor: (score as number) >= 80 ? '#27AE60' : (score as number) >= 50 ? '#F39C12' : '#C0392B',
                          }}
                        />
                      </div>
                      <span className="text-sm font-mono w-10 text-right">{(score as number).toFixed(0)}</span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-400">Pas de donnees M365</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
