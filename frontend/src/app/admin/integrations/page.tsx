'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { useIntegrations, useConfigureIntegration, useTestIntegration } from '@/hooks/useIntegrations'
import { Settings, Zap, CheckCircle, XCircle, Loader2 } from 'lucide-react'

interface IntegrationCardProps {
  type: string
  label: string
  description: string
  enabled: boolean
  configured: boolean
  fields: { key: string; label: string; type: string }[]
  onConfigure: (type: string, config: Record<string, string>) => void
  onTest: (type: string) => void
  testing: boolean
}

function IntegrationCard({
  type, label, description, enabled, configured, fields,
  onConfigure, onTest, testing,
}: IntegrationCardProps) {
  const [values, setValues] = useState<Record<string, string>>({})
  const [expanded, setExpanded] = useState(false)

  return (
    <Card className={`border-2 transition-colors ${configured ? 'border-green-200' : 'border-gray-200'}`}>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <div className="flex items-center gap-3">
          <Zap className={`h-5 w-5 ${configured ? 'text-green-500' : 'text-gray-400'}`} />
          <div>
            <CardTitle className="text-base">{label}</CardTitle>
            <p className="text-xs text-gray-500">{description}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {configured ? (
            <Badge className="bg-green-100 text-green-700">Connected</Badge>
          ) : (
            <Badge variant="outline" className="text-gray-500">Not configured</Badge>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex gap-2">
          <button
            onClick={() => setExpanded(!expanded)}
            className="rounded bg-[#2E75B6] px-3 py-1.5 text-xs font-medium text-white hover:bg-[#1B3A5C]"
          >
            <Settings className="mr-1 inline h-3 w-3" />
            Configure
          </button>
          <button
            onClick={() => onTest(type)}
            disabled={!configured || testing}
            className="rounded border border-gray-300 px-3 py-1.5 text-xs font-medium hover:bg-gray-50 disabled:opacity-50"
          >
            {testing ? (
              <Loader2 className="mr-1 inline h-3 w-3 animate-spin" />
            ) : (
              <Zap className="mr-1 inline h-3 w-3" />
            )}
            Test
          </button>
        </div>

        {expanded && (
          <div className="mt-4 space-y-3 rounded-lg border bg-gray-50 p-4">
            {fields.map((field) => (
              <div key={field.key}>
                <label className="mb-1 block text-xs font-medium text-gray-600">{field.label}</label>
                <input
                  type={field.type}
                  value={values[field.key] || ''}
                  onChange={(e) => setValues({ ...values, [field.key]: e.target.value })}
                  className="w-full rounded border px-3 py-1.5 text-sm focus:border-[#2E75B6] focus:outline-none"
                  placeholder={field.label}
                />
              </div>
            ))}
            <button
              onClick={() => {
                onConfigure(type, values)
                setExpanded(false)
              }}
              className="rounded bg-[#2E75B6] px-4 py-1.5 text-xs font-medium text-white hover:bg-[#1B3A5C]"
            >
              Save Configuration
            </button>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

const INTEGRATION_META: Record<string, {
  label: string
  description: string
  fields: { key: string; label: string; type: string }[]
}> = {
  splunk: {
    label: 'Splunk SIEM',
    description: 'Push scoring events and alerts to Splunk via HEC',
    fields: [
      { key: 'url', label: 'HEC URL', type: 'text' },
      { key: 'token', label: 'HEC Token', type: 'password' },
    ],
  },
  servicenow: {
    label: 'ServiceNow ITSM',
    description: 'Create incidents and remediation tasks automatically',
    fields: [
      { key: 'url', label: 'Instance Name', type: 'text' },
      { key: 'username', label: 'Username', type: 'text' },
      { key: 'password', label: 'Password', type: 'password' },
    ],
  },
  slack: {
    label: 'Slack',
    description: 'Alert notifications via Slack webhooks with Block Kit',
    fields: [
      { key: 'url', label: 'Webhook URL', type: 'text' },
    ],
  },
  teams: {
    label: 'Microsoft Teams',
    description: 'Alert notifications via Teams webhooks with Adaptive Cards',
    fields: [
      { key: 'url', label: 'Webhook URL', type: 'text' },
    ],
  },
}

export default function IntegrationsPage() {
  const { data } = useIntegrations()
  const configureMutation = useConfigureIntegration()
  const testMutation = useTestIntegration()
  const [testingType, setTestingType] = useState<string | null>(null)
  const [testResult, setTestResult] = useState<{ type: string; success: boolean; message: string } | null>(null)

  const integrations = data?.integrations ?? []

  const handleConfigure = (type: string, config: Record<string, string>) => {
    configureMutation.mutate({
      type,
      config: {
        type,
        enabled: true,
        url: config.url || '',
        token: config.token || '',
        username: config.username || '',
        password: config.password || '',
      },
    })
  }

  const handleTest = async (type: string) => {
    setTestingType(type)
    setTestResult(null)
    try {
      const result = await testMutation.mutateAsync(type)
      setTestResult(result)
    } finally {
      setTestingType(null)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-[#1B3A5C]">
          <Settings className="mr-2 inline h-6 w-6" />
          Integrations
        </h1>
        <p className="text-sm text-gray-500">
          {integrations.filter((i) => i.configured).length} / {integrations.length} configured
        </p>
      </div>

      {testResult && (
        <div className={`flex items-center gap-2 rounded-lg p-3 text-sm ${testResult.success ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
          {testResult.success ? (
            <CheckCircle className="h-4 w-4" />
          ) : (
            <XCircle className="h-4 w-4" />
          )}
          <span className="font-medium">{INTEGRATION_META[testResult.type]?.label}:</span>
          {testResult.message}
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {Object.entries(INTEGRATION_META).map(([type, meta]) => {
          const status = integrations.find((i) => i.type === type)
          return (
            <IntegrationCard
              key={type}
              type={type}
              label={meta.label}
              description={meta.description}
              enabled={status?.enabled ?? false}
              configured={status?.configured ?? false}
              fields={meta.fields}
              onConfigure={handleConfigure}
              onTest={handleTest}
              testing={testingType === type}
            />
          )
        })}
      </div>
    </div>
  )
}
