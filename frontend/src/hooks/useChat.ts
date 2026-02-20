'use client'

import { useState, useCallback } from 'react'
import { api } from '@/lib/api'
import { API_ROUTES } from '@/lib/constants'
import type { ChatMessage } from '@/types/api'

interface ChatResponse {
  id: string
  content: string
  timestamp: string
}

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '0',
      role: 'assistant',
      content: 'Bonjour, je suis CyberChat, votre assistant IA cyber scoring. Comment puis-je vous aider ?',
      timestamp: new Date().toISOString(),
    },
  ])
  const [isLoading, setIsLoading] = useState(false)

  const sendMessage = useCallback(async (content: string) => {
    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, userMsg])
    setIsLoading(true)

    try {
      const response = await api.post<ChatResponse>(API_ROUTES.chat, {
        message: content,
      })

      const aiMsg: ChatMessage = {
        id: response.id ?? (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.content,
        timestamp: response.timestamp ?? new Date().toISOString(),
      }
      setMessages((prev) => [...prev, aiMsg])
    } catch {
      const errorMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Erreur lors de la communication avec le serveur. Veuillez réessayer.',
        timestamp: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, errorMsg])
    } finally {
      setIsLoading(false)
    }
  }, [])

  return { messages, sendMessage, isLoading }
}
