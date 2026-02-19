'use client'

import { useState } from 'react'
import { MessageCircle, X, Send } from 'lucide-react'
import { useChat } from '@/hooks/useChat'

export function ChatWidget() {
  const [isOpen, setIsOpen] = useState(false)
  const { messages, sendMessage, isLoading } = useChat()
  const [input, setInput] = useState('')

  const handleSend = () => {
    if (!input.trim()) return
    sendMessage(input.trim())
    setInput('')
  }

  return (
    <div className="fixed bottom-6 right-6 z-50">
      {isOpen && (
        <div className="mb-3 flex h-[480px] w-[380px] flex-col rounded-xl border border-gray-200 bg-white shadow-xl">
          {/* Header */}
          <div className="flex items-center justify-between rounded-t-xl bg-[#1B3A5C] px-4 py-3">
            <div className="flex items-center gap-2 text-white">
              <MessageCircle className="h-4 w-4" />
              <span className="text-sm font-semibold">ChatMH</span>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="rounded p-1 text-white/70 hover:text-white"
              aria-label="Fermer le chat"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 space-y-3 overflow-y-auto p-4">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-2xl px-3 py-2 text-xs ${
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
                <div className="rounded-2xl bg-gray-100 px-3 py-2 text-xs text-gray-400">
                  Reflexion en cours...
                </div>
              </div>
            )}
          </div>

          {/* Input */}
          <div className="flex items-center gap-2 border-t p-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Posez votre question..."
              className="flex-1 rounded-lg border border-gray-200 px-3 py-2 text-xs focus:border-[#2E75B6] focus:outline-none"
              disabled={isLoading}
              aria-label="Message"
            />
            <button
              onClick={handleSend}
              disabled={isLoading || !input.trim()}
              className="rounded-lg bg-[#2E75B6] p-2 text-white hover:bg-[#1B3A5C] disabled:opacity-50"
              aria-label="Envoyer"
            >
              <Send className="h-3 w-3" />
            </button>
          </div>
        </div>
      )}

      {/* Toggle button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex h-14 w-14 items-center justify-center rounded-full bg-[#2E75B6] text-white shadow-lg transition-transform hover:scale-105 hover:bg-[#1B3A5C]"
        aria-label={isOpen ? 'Fermer le chat' : 'Ouvrir le chat'}
      >
        {isOpen ? <X className="h-6 w-6" /> : <MessageCircle className="h-6 w-6" />}
      </button>
    </div>
  )
}
