import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { apiClient } from '@/api/client'
import { errorMessage } from '@/lib/error-message'

import type { components } from '@/api/schema'

export type ProjectOut = components['schemas']['ProjectOut']

export function useProjects(organizationId: string) {
  return useQuery({
    queryKey: ['organizations', organizationId, 'projects'],
    queryFn: async () => {
      const { data, error } = await apiClient.GET(
        '/api/v1/organizations/{organization_id}/projects',
        { params: { path: { organization_id: organizationId } } },
      )
      if (error) throw new Error(errorMessage(error))
      return data
    },
    enabled: Boolean(organizationId),
  })
}

export function useProject(projectId: string) {
  return useQuery({
    queryKey: ['projects', projectId],
    queryFn: async () => {
      const { data, error } = await apiClient.GET('/api/v1/projects/{project_id}', {
        params: { path: { project_id: projectId } },
      })
      if (error) throw new Error(errorMessage(error))
      return data
    },
    enabled: Boolean(projectId),
  })
}

export function useCreateProject(organizationId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (input: { name: string; description?: string }) => {
      const { data, error } = await apiClient.POST(
        '/api/v1/organizations/{organization_id}/projects',
        { params: { path: { organization_id: organizationId } }, body: input },
      )
      if (error) throw new Error(errorMessage(error, 'Não foi possível criar o projeto.'))
      return data
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: ['organizations', organizationId, 'projects'],
      })
    },
  })
}
