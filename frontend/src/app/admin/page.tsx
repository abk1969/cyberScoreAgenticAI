'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Select } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Settings, Brain, Shield, Users, Save, Loader2, CheckCircle, XCircle } from 'lucide-react'
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

  const handleProviderChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newProvider = e.target.value
    setProvider(newProvider)
    const models = LLM_MODELS[newProvider]
    if (models && models.length > 0) {
      setModel(models[0].value)
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
