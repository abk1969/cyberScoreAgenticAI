import { Badge } from '@/components/ui/badge'
import { severityToColor } from '@/lib/scoring-utils'
import { SEVERITY_LABELS, DOMAIN_LABELS } from '@/lib/constants'
import type { Finding } from '@/types/scoring'

interface FindingRowProps {
  finding: Finding
  className?: string
}

const STATUS_LABELS: Record<string, string> = {
  open: 'Ouvert',
  acknowledged: 'Acquitté',
  disputed: 'Contesté',
  resolved: 'Résolu',
  false_positive: 'Faux positif',
}

export function FindingRow({ finding, className }: FindingRowProps) {
  const severityColor = severityToColor(finding.severity)

  return (
    <tr className={className}>
      <td className="px-4 py-3">
        <div>
          <p className="font-medium text-[#2C3E50]">{finding.title}</p>
          <p className="mt-0.5 text-xs text-gray-500">{finding.description}</p>
        </div>
      </td>
      <td className="px-4 py-3 text-xs text-gray-500">
        {DOMAIN_LABELS[finding.domain] ?? finding.domain}
      </td>
      <td className="px-4 py-3">
        <Badge style={{ backgroundColor: severityColor, color: '#fff' }}>
          {SEVERITY_LABELS[finding.severity] ?? finding.severity}
        </Badge>
      </td>
      <td className="px-4 py-3 font-mono text-sm">
        {finding.cvssScore !== null ? finding.cvssScore.toFixed(1) : '—'}
      </td>
      <td className="px-4 py-3 text-xs text-gray-500">{finding.source}</td>
      <td className="px-4 py-3">
        <Badge variant="outline">{STATUS_LABELS[finding.status] ?? finding.status}</Badge>
      </td>
      <td className="px-4 py-3 text-xs text-gray-500">{finding.detectedAt}</td>
    </tr>
  )
}
