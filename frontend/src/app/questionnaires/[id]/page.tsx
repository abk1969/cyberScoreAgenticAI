'use client'

import { useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  FileQuestion,
  ArrowLeft,
  Send,
  Sparkles,
  Loader2,
  CheckCircle,
} from 'lucide-react'
import {
  useQuestionnaire,
  useSendQuestionnaire,
  useSubmitResponse,
  useSmartAnswer,
} from '@/hooks/useQuestionnaires'

export default function QuestionnaireDetailPage() {
  const params = useParams()
  const router = useRouter()
  const id = params.id as string

  const { data: questionnaire, isLoading } = useQuestionnaire(id)
  const sendQuestionnaire = useSendQuestionnaire(id)
  const submitResponse = useSubmitResponse(id)
  const smartAnswer = useSmartAnswer(id)

  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [smartSuggestions, setSmartSuggestions] = useState<
    Record<string, { answer: string; confidence: number; reasoning: string | null }>
  >({})
  const [vendorId, setVendorId] = useState('')
  const [recipientEmail, setRecipientEmail] = useState('')
  const [showSendForm, setShowSendForm] = useState(false)
  const [submitted, setSubmitted] = useState(false)

  const handleAnswerChange = (questionId: string, value: string) => {
    setAnswers((prev) => ({ ...prev, [questionId]: value }))
  }

  const handleSmartAnswer = (questionId: string) => {
    smartAnswer.mutate(
      { question_id: questionId, vendor_context: vendorId ? `Vendor ID: ${vendorId}` : undefined },
      {
        onSuccess: (result) => {
          setSmartSuggestions((prev) => ({
            ...prev,
            [questionId]: {
              answer: result.suggested_answer,
              confidence: result.confidence,
              reasoning: result.reasoning,
            },
          }))
        },
      }
    )
  }

  const applySmartAnswer = (questionId: string) => {
    const suggestion = smartSuggestions[questionId]
    if (suggestion) {
      setAnswers((prev) => ({ ...prev, [questionId]: suggestion.answer }))
    }
  }

  const handleSubmit = () => {
    if (!vendorId) return
    const answerList = Object.entries(answers).map(([question_id, value]) => ({
      question_id,
      value,
    }))
    submitResponse.mutate(
      { vendor_id: vendorId, answers: answerList },
      { onSuccess: () => setSubmitted(true) }
    )
  }

  const handleSend = () => {
    if (!vendorId || !recipientEmail) return
    sendQuestionnaire.mutate(
      { vendor_id: vendorId, recipient_email: recipientEmail },
      { onSuccess: () => setShowSendForm(false) }
    )
  }

  if (isLoading) {
    return (
      <div className="flex justify-center py-20">
        <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
      </div>
    )
  }

  if (!questionnaire) {
    return (
      <div className="py-20 text-center text-gray-400">
        Questionnaire introuvable.
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => router.push('/questionnaires')}
          className="rounded-lg border border-gray-300 p-2 hover:bg-gray-50"
        >
          <ArrowLeft className="h-4 w-4" />
        </button>
        <div className="flex-1">
          <h1 className="text-2xl font-bold text-[#1B3A5C]">
            <FileQuestion className="mr-2 inline h-6 w-6" />
            {questionnaire.title}
          </h1>
          <p className="text-sm text-gray-500">{questionnaire.description}</p>
        </div>
        <Badge className="bg-[#2E75B6] text-white">
          {questionnaire.category ?? 'Custom'}
        </Badge>
      </div>

      {/* Vendor ID + Send */}
      <Card>
        <CardContent className="flex items-end gap-4 p-4">
          <div className="flex-1">
            <label className="mb-1 block text-sm font-medium text-gray-700">
              ID Fournisseur
            </label>
            <input
              type="text"
              value={vendorId}
              onChange={(e) => setVendorId(e.target.value)}
              placeholder="UUID du fournisseur"
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
            />
          </div>
          <button
            onClick={() => setShowSendForm(!showSendForm)}
            className="inline-flex items-center gap-2 rounded-lg border border-[#2E75B6] px-4 py-2 text-sm font-medium text-[#2E75B6] hover:bg-blue-50"
          >
            <Send className="h-4 w-4" /> Envoyer
          </button>
        </CardContent>
      </Card>

      {/* Send form */}
      {showSendForm && (
        <Card>
          <CardContent className="space-y-3 p-4">
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                Email du destinataire
              </label>
              <input
                type="email"
                value={recipientEmail}
                onChange={(e) => setRecipientEmail(e.target.value)}
                placeholder="contact@fournisseur.com"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
              />
            </div>
            <button
              onClick={handleSend}
              disabled={sendQuestionnaire.isPending || !vendorId || !recipientEmail}
              className="inline-flex items-center gap-2 rounded-lg bg-[#2E75B6] px-4 py-2 text-sm font-medium text-white hover:bg-[#1B3A5C] disabled:opacity-50"
            >
              {sendQuestionnaire.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
              Envoyer le questionnaire
            </button>
          </CardContent>
        </Card>
      )}

      {/* Success message */}
      {submitted && (
        <Card className="border-green-300 bg-green-50">
          <CardContent className="flex items-center gap-3 p-4">
            <CheckCircle className="h-5 w-5 text-green-600" />
            <p className="text-sm font-medium text-green-800">
              Reponses soumises avec succes !
            </p>
          </CardContent>
        </Card>
      )}

      {/* Questions */}
      <div className="space-y-4">
        {questionnaire.questions
          .sort((a, b) => a.order - b.order)
          .map((q) => (
            <Card key={q.id}>
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between">
                  <CardTitle className="text-sm font-medium text-[#1B3A5C]">
                    {q.order}. {q.text}
                    {q.is_required && <span className="ml-1 text-red-500">*</span>}
                  </CardTitle>
                  {q.category && (
                    <Badge variant="outline" className="text-xs">
                      {q.category}
                    </Badge>
                  )}
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {/* Answer input */}
                {q.question_type === 'single_choice' && q.options?.choices ? (
                  <div className="space-y-2">
                    {q.options.choices.map((choice: string) => (
                      <label key={choice} className="flex items-center gap-2 text-sm">
                        <input
                          type="radio"
                          name={`q-${q.id}`}
                          value={choice}
                          checked={answers[q.id] === choice}
                          onChange={() => handleAnswerChange(q.id, choice)}
                          className="text-[#2E75B6]"
                        />
                        {choice}
                      </label>
                    ))}
                  </div>
                ) : (
                  <textarea
                    value={answers[q.id] ?? ''}
                    onChange={(e) => handleAnswerChange(q.id, e.target.value)}
                    placeholder="Votre reponse..."
                    rows={3}
                    className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm"
                  />
                )}

                {/* Smart answer */}
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleSmartAnswer(q.id)}
                    disabled={smartAnswer.isPending}
                    className="inline-flex items-center gap-1 rounded-lg border border-purple-300 px-3 py-1.5 text-xs font-medium text-purple-700 hover:bg-purple-50 disabled:opacity-50"
                  >
                    {smartAnswer.isPending ? (
                      <Loader2 className="h-3 w-3 animate-spin" />
                    ) : (
                      <Sparkles className="h-3 w-3" />
                    )}
                    Suggestion IA
                  </button>

                  {smartSuggestions[q.id] && (
                    <button
                      onClick={() => applySmartAnswer(q.id)}
                      className="text-xs text-purple-600 hover:underline"
                    >
                      Appliquer la suggestion
                    </button>
                  )}
                </div>

                {/* Smart answer result */}
                {smartSuggestions[q.id] && (
                  <div className="rounded-lg border border-purple-200 bg-purple-50 p-3">
                    <p className="text-sm text-purple-800">
                      {smartSuggestions[q.id].answer}
                    </p>
                    <div className="mt-2 flex items-center gap-4 text-xs text-purple-600">
                      <span>
                        Confiance : {Math.round(smartSuggestions[q.id].confidence * 100)}%
                      </span>
                      {smartSuggestions[q.id].reasoning && (
                        <span>{smartSuggestions[q.id].reasoning}</span>
                      )}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
      </div>

      {/* Submit button */}
      {questionnaire.questions.length > 0 && !submitted && (
        <div className="flex justify-end">
          <button
            onClick={handleSubmit}
            disabled={submitResponse.isPending || !vendorId}
            className="inline-flex items-center gap-2 rounded-lg bg-[#27AE60] px-6 py-3 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50"
          >
            {submitResponse.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
            Soumettre les reponses
          </button>
        </div>
      )}
    </div>
  )
}
