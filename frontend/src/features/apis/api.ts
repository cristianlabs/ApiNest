import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { apiClient } from '@/api/client'
import { errorMessage } from '@/lib/error-message'

import type { components } from '@/api/schema'

export type ApiOut = components['schemas']['ApiOut']
export type Environment = components['schemas']['Environment']
export type ApiStatus = components['schemas']['ApiStatus']

export interface ApiFormValues {
  name: string
  base_url: string
  description?: string
  environment: Environment
  status: ApiStatus
  tags: string[]
}

export function useApis(projectId: string) {
  return useQuery({
    queryKey: ['projects', projectId, 'apis'],
    queryFn: async () => {
      const { data, error } = await apiClient.GET('/api/v1/projects/{project_id}/apis', {
        params: { path: { project_id: projectId } },
      })
      if (error) throw new Error(errorMessage(error))
      return data
    },
    enabled: Boolean(projectId),
  })
}

export function useApiDetail(apiId: string | undefined) {
  return useQuery({
    queryKey: ['apis', apiId],
    queryFn: async () => {
      const { data, error } = await apiClient.GET('/api/v1/apis/{api_id}', {
        params: { path: { api_id: apiId! } },
      })
      if (error) throw new Error(errorMessage(error))
      return data
    },
    enabled: Boolean(apiId),
  })
}

export function useApiSpec(apiId: string | undefined) {
  return useQuery({
    queryKey: ['apis', apiId, 'openapi.json'],
    queryFn: async () => {
      const { data, error } = await apiClient.GET('/api/v1/apis/{api_id}/openapi.json', {
        params: { path: { api_id: apiId! } },
      })
      if (error) throw new Error(errorMessage(error, 'Não foi possível carregar a documentação.'))
      return data
    },
    enabled: Boolean(apiId),
  })
}

export function useCreateApi(projectId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (input: ApiFormValues) => {
      const { data, error } = await apiClient.POST('/api/v1/projects/{project_id}/apis', {
        params: { path: { project_id: projectId } },
        body: input,
      })
      if (error) throw new Error(errorMessage(error, 'Não foi possível criar a API.'))
      return data
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'apis'] })
    },
  })
}

export function useUpdateApi(apiId: string, projectId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (input: Partial<ApiFormValues>) => {
      const { data, error } = await apiClient.PATCH('/api/v1/apis/{api_id}', {
        params: { path: { api_id: apiId } },
        body: input,
      })
      if (error) throw new Error(errorMessage(error, 'Não foi possível atualizar a API.'))
      return data
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['apis', apiId] })
      void queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'apis'] })
    },
  })
}

export function useDeleteApi(apiId: string, projectId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async () => {
      const { error } = await apiClient.DELETE('/api/v1/apis/{api_id}', {
        params: { path: { api_id: apiId } },
      })
      if (error) throw new Error(errorMessage(error, 'Não foi possível excluir a API.'))
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['projects', projectId, 'apis'] })
    },
  })
}
