import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { apiClient } from '@/api/client'
import { errorMessage } from '@/lib/error-message'

import type { components } from '@/api/schema'

export type EndpointOut = components['schemas']['EndpointOut']
export type HTTPMethod = components['schemas']['HTTPMethod']
export type AuthType = components['schemas']['AuthType']
export type KeyValuePair = components['schemas']['KeyValuePair']

export interface EndpointFormValues {
  name: string
  method: HTTPMethod
  path: string
  headers: KeyValuePair[]
  query_params: KeyValuePair[]
  path_params: KeyValuePair[]
  body_schema?: unknown
  expected_status_code: number
  expected_response_schema?: unknown
  auth_type: AuthType
  auth_config?: Record<string, unknown> | null
}

export function useEndpoints(apiId: string) {
  return useQuery({
    queryKey: ['apis', apiId, 'endpoints'],
    queryFn: async () => {
      const { data, error } = await apiClient.GET('/api/v1/apis/{api_id}/endpoints', {
        params: { path: { api_id: apiId } },
      })
      if (error) throw new Error(errorMessage(error))
      return data
    },
    enabled: Boolean(apiId),
  })
}

export function useEndpointDetail(endpointId: string | undefined) {
  return useQuery({
    queryKey: ['endpoints', endpointId],
    queryFn: async () => {
      const { data, error } = await apiClient.GET('/api/v1/endpoints/{endpoint_id}', {
        params: { path: { endpoint_id: endpointId! } },
      })
      if (error) throw new Error(errorMessage(error))
      return data
    },
    enabled: Boolean(endpointId),
  })
}

export function useCreateEndpoint(apiId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (input: EndpointFormValues) => {
      const { data, error } = await apiClient.POST('/api/v1/apis/{api_id}/endpoints', {
        params: { path: { api_id: apiId } },
        body: input,
      })
      if (error) throw new Error(errorMessage(error, 'Não foi possível criar o endpoint.'))
      return data
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['apis', apiId, 'endpoints'] })
    },
  })
}

export function useUpdateEndpoint(endpointId: string, apiId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (input: Partial<EndpointFormValues>) => {
      const { data, error } = await apiClient.PATCH('/api/v1/endpoints/{endpoint_id}', {
        params: { path: { endpoint_id: endpointId } },
        body: input,
      })
      if (error) throw new Error(errorMessage(error, 'Não foi possível atualizar o endpoint.'))
      return data
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['endpoints', endpointId] })
      void queryClient.invalidateQueries({ queryKey: ['apis', apiId, 'endpoints'] })
    },
  })
}

export function useDeleteEndpoint(endpointId: string, apiId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async () => {
      const { error } = await apiClient.DELETE('/api/v1/endpoints/{endpoint_id}', {
        params: { path: { endpoint_id: endpointId } },
      })
      if (error) throw new Error(errorMessage(error, 'Não foi possível excluir o endpoint.'))
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['apis', apiId, 'endpoints'] })
    },
  })
}
