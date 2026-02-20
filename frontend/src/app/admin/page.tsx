'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Select } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Settings, Brain, Shield, Users, Save, Loader2, CheckCircle, XCircle, EyeOff, Wifi, WifiOff } from 'lucide-react'
import { api } from '@/lib/api'

const LLM_PROVIDERS = [
  { value: 'mistral', label: 'Mistral AI (Souverain)' },
  { value: 'llama', label: 'LLaMA (Self-hosted vLLM)' },
  { value: 'anthropic', label: 'Anthropic Claude (via passerelle)' },
  { value: 'openai', label: 'OpenAI (via passerelle)' },
]

const LLM_MODELS: Record<string, { value: string; label: string }[]> = {
  mistral: [
    { value: 'mistral-large-latest', label: 'Mistral Large' },
    { value: 'mistral-medium-latest', label: 'Mistral Medium' },
    { value: 'mistral-small-latest', label: 'Mistral Small' },
  ],
  llama: [
    { value: 'llama-3.1-70b', label: 'LLaMA 3.1 70B' },
    { value: 'llama-3.1-8b', label: 'LLaMA 3.1 8B' },
  ],
  anthropic: [
    { value: 'claude-opus-4-6', label: 'Claude Opus 4.6' },
    { value: 'claude-sonnet-4-6', label: 'Claude Sonnet 4.6' },
  ],
  openai: [
    { value: 'gpt-4o', label: 'GPT-4o' },
    { value: 'gpt-4o-mini', label: 'GPT-4o Mini' },
  ],
}

export default function AdminPage() {
  const [provider, setProvider] = useState('mistral')
  const [model, setModel] = useState('mistral-large-latest')
  const [apiKey, setApiKey] = useState('')
  const [baseUrl, setBaseUrl] = useState('')
  const [testStatus, setTestStatus] = useState<'idle' | 'testing' | 'success' | 'error'>('idle')
  const [saving, setSaving] = useState(false)
  const [proxyStatus, setProxyStatus] = useState<{
    status: string; mode: string; visible_ip: string | null; message: string
  } | null>(null)
  const [proxyChecking, setProxyChecking] = useState(false)

  const handleProviderChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newProvider = e.target.value
    setProvider(newProvider)
    const models = LLM_MODELS[newProvider]
    if (models && models.length > 0) {
      setModel(models[0].value)
    }
  }

  const handleCheckProxy = async () => {
    setProxyChecking(true)
    try {
      const result = await api.get<{
        status: string; mode: string; visible_ip: string | null; message: string
      }>('/api/v1/admin/proxy/status')
      setProxyStatus(result)
    } catch {
      setProxyStatus({ status: 'error', mode: 'unknown', visible_ip: null, message: 'Impossible de verifier le proxy' })
    } finally {
      setProxyChecking(false)
    }
  }

  const handleTestConnection = async () => {
    setTestStatus('testing')
    try {
      await api.post('/api/v1/admin/llm/test', {
        provider,
        model,
        api_key: apiKey || undefined,
        base_url: baseUrl || undefined,
      })
      setTestStatus('success')
    } catch {
      setTestStatus('error')
    }
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      await api.post('/api/v1/admin/llm/config', {
        provider,
        model,
        api_key: apiKey || undefined,
        base_url: baseUrl || undefined,
      })
    } catch {
      // Error handled by api client
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-[#1B3A5C]">
        <Settings className="mr-2 inline h-6 w-6" />
        Administration
      </h1>

      <Tabs defaultValue="llm">
        <TabsList>
          <TabsTrigger value="llm">
            <Brain className="mr-1.5 h-4 w-4" /> Fournisseur LLM
          </TabsTrigger>
          <TabsTrigger value="proxy">
            <EyeOff className="mr-1.5 h-4 w-4" /> Anonymisation IP
          </TabsTrigger>
          <TabsTrigger value="scoring">
            <Shield className="mr-1.5 h-4 w-4" /> Configuration Scoring
          </TabsTrigger>
          <TabsTrigger value="users">
            <Users className="mr-1.5 h-4 w-4" /> Utilisateurs
          </TabsTrigger>
        </TabsList>

        {/* LLM Configuration */}
        <TabsContent value="llm">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Brain className="h-5 w-5" />
                Configuration du fournisseur LLM
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-2 gap-6">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-[#2C3E50]">Fournisseur</label>
                  <Select
                    options={LLM_PROVIDERS}
                    value={provider}
                    onChange={handleProviderChange}
                  />
                  <p className="text-xs text-gray-500">
                    Priorite recommandee : Mistral ou LLaMA (souverainete)
                  </p>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium text-[#2C3E50]">Modele</label>
                  <Select
                    options={LLM_MODELS[provider] ?? []}
                    value={model}
                    onChange={(e) => setModel(e.target.value)}
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium text-[#2C3E50]">Cle API</label>
                  <Input
                    type="password"
                    placeholder="sk-..."
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                  />
                  <p className="text-xs text-gray-500">
                    Laissez vide pour utiliser la variable d'environnement
                  </p>
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium text-[#2C3E50]">URL de base (optionnel)</label>
                  <Input
                    type="url"
                    placeholder="https://api.mistral.ai/v1"
                    value={baseUrl}
                    onChange={(e) => setBaseUrl(e.target.value)}
                  />
                  <p className="text-xs text-gray-500">
                    Pour vLLM self-hosted ou passerelle souveraine
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-4 border-t pt-4">
                <button
                  onClick={handleTestConnection}
                  disabled={testStatus === 'testing'}
                  className="inline-flex items-center gap-2 rounded-lg border border-[#2E75B6] px-4 py-2 text-sm font-medium text-[#2E75B6] hover:bg-[#2E75B6]/5 disabled:opacity-50"
                >
                  {testStatus === 'testing' ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : testStatus === 'success' ? (
                    <CheckCircle className="h-4 w-4 text-[#27AE60]" />
                  ) : testStatus === 'error' ? (
                    <XCircle className="h-4 w-4 text-[#C0392B]" />
                  ) : null}
                  Tester la connexion
                </button>

                {testStatus === 'success' && (
                  <Badge style={{ backgroundColor: '#27AE60', color: '#fff' }}>Connexion OK</Badge>
                )}
                {testStatus === 'error' && (
                  <Badge style={{ backgroundColor: '#C0392B', color: '#fff' }}>Echec de connexion</Badge>
                )}

                <div className="flex-1" />

                <button
                  onClick={handleSave}
                  disabled={saving}
                  className="inline-flex items-center gap-2 rounded-lg bg-[#2E75B6] px-4 py-2 text-sm font-medium text-white hover:bg-[#1B3A5C] disabled:opacity-50"
                >
                  {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />}
                  Enregistrer
                </button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Proxy / IP Anonymization */}
        <TabsContent value="proxy">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <EyeOff className="h-5 w-5" />
                Anonymisation IP des scans OSINT
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <p className="text-sm text-gray-600">
                Tous les scans OSINT (Shodan, Censys, HIBP, VirusTotal, etc.) passent par un proxy
                pour masquer l&apos;adresse IP source de l&apos;application. Configurez le mode proxy
                dans le fichier <code className="rounded bg-gray-100 px-1">.env</code>.
              </p>

              <div className="rounded-lg border p-4 space-y-3">
                <h3 className="text-sm font-semibold text-[#1B3A5C]">Modes disponibles</h3>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div className="rounded border p-3">
                    <p className="font-medium">tor</p>
                    <p className="text-xs text-gray-500">SOCKS5 via Tor (anonymat maximal)</p>
                  </div>
                  <div className="rounded border p-3">
                    <p className="font-medium">socks5</p>
                    <p className="text-xs text-gray-500">Proxy SOCKS5 generique</p>
                  </div>
                  <div className="rounded border p-3">
                    <p className="font-medium">http</p>
                    <p className="text-xs text-gray-500">Proxy HTTP/HTTPS</p>
                  </div>
                  <div className="rounded border p-3">
                    <p className="font-medium">rotating</p>
                    <p className="text-xs text-gray-500">Liste rotative de proxys</p>
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-4 border-t pt-4">
                <button
                  onClick={handleCheckProxy}
                  disabled={proxyChecking}
                  className="inline-flex items-center gap-2 rounded-lg border border-[#2E75B6] px-4 py-2 text-sm font-medium text-[#2E75B6] hover:bg-[#2E75B6]/5 disabled:opacity-50"
                >
                  {proxyChecking ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Wifi className="h-4 w-4" />
                  )}
                  Verifier le proxy
                </button>

                {proxyStatus && (
                  <div className="flex items-center gap-3">
                    {proxyStatus.status === 'active' ? (
                      <Badge style={{ backgroundColor: '#27AE60', color: '#fff' }}>
                        <Wifi className="mr-1 h-3 w-3" /> Proxy actif
                      </Badge>
                    ) : proxyStatus.status === 'disabled' ? (
                      <Badge style={{ backgroundColor: '#E67E22', color: '#fff' }}>
                        <WifiOff className="mr-1 h-3 w-3" /> Proxy desactive
                      </Badge>
                    ) : (
                      <Badge style={{ backgroundColor: '#C0392B', color: '#fff' }}>
                        <XCircle className="mr-1 h-3 w-3" /> Erreur proxy
                      </Badge>
                    )}
                    <span className="text-sm text-gray-600">{proxyStatus.message}</span>
                  </div>
                )}
              </div>

              {proxyStatus?.visible_ip && (
                <div className="rounded-lg bg-green-50 border border-green-200 p-4">
                  <p className="text-sm font-medium text-green-800">
                    IP visible par les cibles : <code className="font-mono text-lg">{proxyStatus.visible_ip}</code>
                  </p>
                  <p className="mt-1 text-xs text-green-600">
                    Mode : {proxyStatus.mode} — Votre IP reelle est masquee
                  </p>
                </div>
              )}

              {proxyStatus?.status === 'disabled' && (
                <div className="rounded-lg bg-orange-50 border border-orange-200 p-4">
                  <p className="text-sm font-medium text-orange-800">
                    Attention : les scans OSINT utilisent votre IP reelle.
                  </p>
                  <p className="mt-1 text-xs text-orange-600">
                    Configurez <code>CS_PROXY_MODE=tor</code> dans .env pour activer l&apos;anonymisation.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Scoring Configuration */}
        <TabsContent value="scoring">
          <Card>
            <CardHeader>
              <CardTitle>Ponderations du Scoring</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-500">
                Configuration des poids par domaine de scoring. Module en cours de developpement.
              </p>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Users */}
        <TabsContent value="users">
          <Card>
            <CardHeader>
              <CardTitle>Gestion des Utilisateurs</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-500">
                Gestion via Keycloak SSO. Module en cours de developpement.
              </p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}
