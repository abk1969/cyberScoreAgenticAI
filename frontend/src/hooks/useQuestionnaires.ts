import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/lib/api'
import { API_ROUTES } from '@/lib/constants'

export interface QuestionnaireTemplate {
  name: string
  description: string
  category: string
  question_count: number
}

export interface QuestionnaireListItem {
  id: string
  title: string
  category: string | null
  version: string
  is_active: boolean
  created_at: string
}

export interface Question {
  id: string
  questionnaire_id: string
  order: number
  text: string
  question_type: string
  options: { choices?: string[] } | null
  is_required: boolean
  weight: number | null
  category: string | null
}

export interface QuestionnaireDetail {
  id: string
  title: string
  description: string | null
  version: string
  category: string | null
  is_active: boolean
  created_at: string
  updated_at: string
  questions: Question[]
}

export interface SmartAnswerResult {
  question_id: string
  suggested_answer: string
  confidence: number
  reasoning: string | null
}

export function useQuestionnaireTemplates() {
  return useQuery({
    queryKey: ['questionnaire-templates'],
    queryFn: () => api.get<QuestionnaireTemplate[]>(API_ROUTES.questionnaireTemplates),
  })
}

export function useQuestionnaires() {
  return useQuery({
    queryKey: ['questionnaires'],
    queryFn: () => api.get<QuestionnaireListItem[]>(API_ROUTES.questionnaires),
  })
}

export function useQuestionnaire(id: string) {
  return useQuery({
    queryKey: ['questionnaire', id],
    queryFn: () => api.get<QuestionnaireDetail>(API_ROUTES.questionnaire(id)),
    enabled: !!id,
  })
}

export function useCreateQuestionnaire() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: { template_name: string; vendor_id: string; title?: string }) =>
      api.post<QuestionnaireDetail>(API_ROUTES.questionnaires, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['questionnaires'] })
    },
  })
}

export function useSendQuestionnaire(id: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: { vendor_id: string; recipient_email: string }) =>
      api.post(API_ROUTES.questionnaireSend(id), data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['questionnaires'] })
      queryClient.invalidateQueries({ queryKey: ['questionnaire', id] })
    },
  })
}

export function useSubmitResponse(id: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (data: { vendor_id: string; answers: { question_id: string; value: string }[] }) =>
      api.post(API_ROUTES.questionnaireRespond(id), data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['questionnaire', id] })
    },
  })
}

export function useSmartAnswer(questionnaireId: string) {
  return useMutation({
    mutationFn: (data: { question_id: string; vendor_context?: string }) =>
      api.post<SmartAnswerResult>(API_ROUTES.questionnaireSmartAnswer(questionnaireId), data),
  })
}
