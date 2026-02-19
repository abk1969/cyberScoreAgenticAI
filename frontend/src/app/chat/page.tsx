'use client'

import { useState } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { useChat } from '@/hooks/useChat'
import { Send, MessageCircle } from 'lucide-react'

const SUGGESTIONS = [
  'Quels sont nos 5 fournisseurs les plus risqués ?',
  'Score DORA d\'Atos ?',
  'Quel est notre risque de concentration sur AWS ?',
  'Combien de fournisseurs Tier 1 ont un score inférieur à C ?',
]

export default function ChatPage() {
  const { messages, sendMessage, isLoading } = useChat()
  const [input, setInput] = useState('')

  const handleSend = () => {
    if (!input.trim()) return
    sendMessage(input.trim())
    setInput('')
  }

  return (
    <div className="flex h-[calc(100vh-8rem)] flex-col">
      <h1 className="mb-4 text-2xl font-bold text-[#1B3A5C]">
        <MessageCircle className="mr-2 inline h-6 w-6" />
        ChatMH — Assistant IA
      </h1>

      {/* Messages */}
      <Card className="flex-1 overflow-hidden">
        <CardContent className="flex h-full flex-col p-0">
          <div className="flex-1 space-y-4 overflow-y-auto p-4">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[70%] rounded-2xl px-4 py-2.5 text-sm ${
                    msg.role === 'user'
                      ? 'bg-[#2E75B6] text-white'
                      : 'bg-gray-100 text-[#2C3E50]'
                  }`}
                >
                  {msg.content}
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex justify-start">
                <div className="rounded-2xl bg-gray-100 px-4 py-2.5 text-sm text-gray-400">
                  Réflexion en cours...
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
  )
}
