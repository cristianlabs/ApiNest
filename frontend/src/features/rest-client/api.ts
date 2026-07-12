import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { apiClient } from '@/api/client'
import { errorMessage } from '@/lib/error-message'

import type { components } from '@/api/schema'

export type HTTPMethod = components['schemas']['HTTPMethod']
export type AuthType = components['schemas']['AuthType']
export type KeyValuePair = components['schemas']['KeyValuePair']
export type RequestHistoryOut = components['schemas']['RequestHistoryOut']

export interface SendRequestInput {
  endpoint_id?: string | null
  api_id?: string | null
  method: HTTPMethod
  url: string
  headers: KeyValuePair[]
  query_params: KeyValuePair[]
  body?: unknown
  auth_type: AuthType
  auth_token?: string | null
  auth_username?: string | null
  auth_password?: string | null
  auth_header_name?: string | null
}

export function useSendRequest(projectId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (input: SendRequestInput) => {
      const { data, error } = await apiClient.POST('/api/v1/projects/{project_id}/rest-client/send', {
        params: { path: { project_id: projectId } },
        body: input,
      })
      if (error) throw new Error(errorMessage(error, 'Não foi possível enviar a requisição.'))
      return data
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ['projects', projectId, 'rest-client', 'history'],
      })
    },
  })
}

export function useHistory(projectId: string, page: number, pageSize = 20) {
  return useQuery({
    queryKey: ['projects', projectId, 'rest-client', 'history', page, pageSize],
    queryFn: async () => {
      const { data, error } = await apiClient.GET(
        '/api/v1/projects/{project_id}/rest-client/history',
        {
          params: { path: { project_id: projectId }, query: { page, page_size: pageSize } },
        },
      )
      if (error) throw new Error(errorMessage(error))
      return data
    },
    enabled: Boolean(projectId),
    placeholderData: keepPreviousData,
  })
}

export function useSetFavorite(historyId: string, projectId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (isFavorite: boolean) => {
      const { data, error } = await apiClient.PATCH(
        '/api/v1/rest-client/history/{history_id}/favorite',
        {
          params: { path: { history_id: historyId } },
          body: { is_favorite: isFavorite },
        },
      )
      if (error) throw new Error(errorMessage(error, 'Não foi possível atualizar o favorito.'))
      return data
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ['projects', projectId, 'rest-client', 'history'],
      })
    },
  })
}

export function useDeleteHistoryEntry(historyId: string, projectId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async () => {
      const { error } = await apiClient.DELETE('/api/v1/rest-client/history/{history_id}', {
        params: { path: { history_id: historyId } },
      })
      if (error) throw new Error(errorMessage(error, 'Não foi possível excluir o histórico.'))
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ['projects', projectId, 'rest-client', 'history'],
      })
    },
  })
}
