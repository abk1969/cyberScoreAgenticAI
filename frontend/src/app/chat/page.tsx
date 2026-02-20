'use client'

import { useState } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { useChat } from '@/hooks/useChat'
import { Send, MessageCircle, History, ExternalLink, FileText, Shield, AlertTriangle } from 'lucide-react'

interface ChatSource {
  type: string
  id: string
  title: string
  relevance: number
}

const SUGGESTIONS = [
  'Quels sont nos 5 fournisseurs les plus risques ?',
  "Score DORA d'Atos ?",
  'Quel est notre risque de concentration sur AWS ?',
  'Combien de fournisseurs Tier 1 ont un score inferieur a C ?',
]

const SOURCE_ICONS: Record<string, typeof FileText> = {
  score: Shield,
  finding: AlertTriangle,
  document: FileText,
}

function SourceBadge({ source }: { source: ChatSource }) {
  const Icon = SOURCE_ICONS[source.type] ?? FileText
  const relevancePct = Math.round(source.relevance * 100)

  return (
    <a
      href={
        source.type === 'score'
          ? `/vendors/${source.id}/scoring`
          : source.type === 'finding'
            ? `/vendors/${source.id}`
            : '#'
      }
      className="inline-flex items-center gap-1 rounded-md border border-blue-200 bg-blue-50 px-2 py-0.5 text-xs text-blue-700 hover:bg-blue-100 transition-colors"
      title={`${source.title} (pertinence: ${relevancePct}%)`}
    >
      <Icon className="h-3 w-3" />
      <span className="max-w-[120px] truncate">{source.title || source.type}</span>
      <span className="text-blue-400">{relevancePct}%</span>
      <ExternalLink className="h-2.5 w-2.5" />
    </a>
  )
}

export default function ChatPage() {
  const { messages, sendMessage, isLoading } = useChat()
  const [input, setInput] = useState('')
  const [showHistory, setShowHistory] = useState(false)

  const handleSend = () => {
    if (!input.trim()) return
    sendMessage(input.trim())
    setInput('')
  }

  // Group messages into conversations for history sidebar
  const userMessages = messages.filter((m) => m.role === 'user')

  return (
    <div className="flex h-[calc(100vh-8rem)] gap-4">
      {/* History sidebar */}
      <div
        className={`flex-shrink-0 transition-all duration-200 ${
          showHistory ? 'w-64' : 'w-0'
        } overflow-hidden`}
      >
        <Card className="h-full">
          <CardContent className="flex h-full flex-col p-0">
            <div className="border-b p-3">
              <h3 className="text-sm font-semibold text-[#1B3A5C]">Historique</h3>
            </div>
            <div className="flex-1 overflow-y-auto p-2">
              {userMessages.length === 0 ? (
                <p className="p-2 text-xs text-gray-400">Aucun historique</p>
              ) : (
                userMessages.map((msg) => (
                  <div
                    key={msg.id}
                    className="mb-1 rounded-md p-2 text-xs text-gray-600 hover:bg-gray-50 cursor-default"
                    title={msg.content}
                  >
                    <p className="truncate">{msg.content}</p>
                    <span className="text-[10px] text-gray-400">
                      {new Date(msg.timestamp).toLocaleTimeString('fr-FR', {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </span>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main chat area */}
      <div className="flex flex-1 flex-col">
        <div className="mb-4 flex items-center justify-between">
          <h1 className="text-2xl font-bold text-[#1B3A5C]">
            <MessageCircle className="mr-2 inline h-6 w-6" />
            ChatMH — Assistant IA
          </h1>
          <button
            onClick={() => setShowHistory(!showHistory)}
            className={`rounded-lg p-2 transition-colors ${
              showHistory
                ? 'bg-[#2E75B6] text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
            aria-label="Historique"
          >
            <History className="h-4 w-4" />
          </button>
        </div>

        {/* Messages */}
        <Card className="flex-1 overflow-hidden">
          <CardContent className="flex h-full flex-col p-0">
            <div className="flex-1 space-y-4 overflow-y-auto p-4">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div className="max-w-[70%]">
                    <div
                      className={`rounded-2xl px-4 py-2.5 text-sm ${
                        msg.role === 'user'
                          ? 'bg-[#2E75B6] text-white'
                          : 'bg-gray-100 text-[#2C3E50]'
                      }`}
                    >
                      {msg.content}
                    </div>
                    {/* Source citations for assistant messages */}
                    {msg.role === 'assistant' &&
                      (msg as any).sources &&
                      (msg as any).sources.length > 0 && (
                        <div className="mt-1.5 flex flex-wrap gap-1">
                          {(msg as any).sources.map((src: ChatSource, i: number) => (
                            <SourceBadge key={`${src.id}-${i}`} source={src} />
                          ))}
                        </div>
                      )}
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="flex justify-start">
                  <div className="rounded-2xl bg-gray-100 px-4 py-2.5 text-sm text-gray-400">
                    <span className="inline-flex items-center gap-1">
                      <span className="animate-pulse">Reflexion en cours</span>
                      <span className="animate-bounce">...</span>
                    </span>
                  </div>
                </div>
              )}
            </div>

            {/* Suggestions */}
            {messages.length <= 1 && (
              <div className="flex flex-wrap gap-2 border-t px-4 py-3">
                {SUGGESTIONS.map((s) => (
                  <button
                    key={s}
                    onClick={() => sendMessage(s)}
                    className="rounded-full border border-gray-200 px-3 py-1 text-xs text-[#2E75B6] hover:bg-[#2E75B6]/5"
                  >
                    {s}
                  </button>
                ))}
              </div>
            )}

            {/* Input */}
            <div className="flex items-center gap-2 border-t p-4">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                placeholder="Posez votre question..."
                className="flex-1 rounded-lg border border-gray-200 px-4 py-2.5 text-sm focus:border-[#2E75B6] focus:outline-none"
                disabled={isLoading}
                aria-label="Message"
              />
              <button
                onClick={handleSend}
                disabled={isLoading || !input.trim()}
                className="rounded-lg bg-[#2E75B6] p-2.5 text-white hover:bg-[#1B3A5C] disabled:opacity-50"
                aria-label="Envoyer"
              >
                <Send className="h-4 w-4" />
              </button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
