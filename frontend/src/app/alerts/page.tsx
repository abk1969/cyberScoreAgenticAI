'use client'

import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { useAlerts, useMarkAlertRead } from '@/hooks/useAlerts'
import { CheckCircle } from 'lucide-react'

const severityColors: Record<string, string> = {
  critical: '#C0392B', high: '#E67E22', medium: '#F39C12', low: '#2ECC71',
}

export default function AlertsPage() {
  const { data: alerts } = useAlerts()
  const markRead = useMarkAlertRead()

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-[#1B3A5C]">Alertes</h1>

      <div className="space-y-3">
        {(alerts ?? []).map((alert) => (
          <Card key={alert.id} className="overflow-hidden">
            <div className="flex">
              <div className="w-1.5" style={{ backgroundColor: severityColors[alert.severity] }} />
              <CardContent className="flex flex-1 items-center justify-between p-4">
                <div>
                  <div className="flex items-center gap-2">
                    <Badge style={{ backgroundColor: severityColors[alert.severity], color: '#fff' }}>
                      {alert.severity}
                    </Badge>
                    <span className="font-semibold">{alert.title}</span>
                  </div>
                  <p className="mt-1 text-sm text-gray-500">{alert.vendorName} — {alert.description}</p>
                  <p className="mt-1 text-xs text-gray-400">{new Date(alert.createdAt).toLocaleString('fr-FR')}</p>
                </div>
                <div className="flex gap-2">
                  {!alert.isRead && (
                    <button
                      onClick={() => markRead.mutate(alert.id)}
                      className="rounded-lg border border-gray-200 px-3 py-1.5 text-xs hover:bg-gray-50"
                    >
                      <CheckCircle className="mr-1 inline h-3 w-3" /> Marquer lu
                    </button>
                  )}
                </div>
              </CardContent>
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}
