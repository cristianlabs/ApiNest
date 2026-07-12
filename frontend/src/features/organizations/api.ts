import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { apiClient } from '@/api/client'
import { errorMessage } from '@/lib/error-message'
import { useAuthStore } from '@/stores/auth-store'

import type { components } from '@/api/schema'

export type Role = components['schemas']['Role']
export type OrganizationOut = components['schemas']['OrganizationOut']
export type MemberOut = components['schemas']['MemberOut']
export type InvitationOut = components['schemas']['InvitationOut']

export function useOrganizations() {
  return useQuery({
    queryKey: ['organizations'],
    queryFn: async () => {
      const { data, error } = await apiClient.GET('/api/v1/organizations')
      if (error) throw new Error(errorMessage(error))
      return data
    },
  })
}

export function useOrganization(organizationId: string) {
  return useQuery({
    queryKey: ['organizations', organizationId],
    queryFn: async () => {
      const { data, error } = await apiClient.GET('/api/v1/organizations/{organization_id}', {
        params: { path: { organization_id: organizationId } },
      })
      if (error) throw new Error(errorMessage(error))
      return data
    },
    enabled: Boolean(organizationId),
  })
}

export function useCreateOrganization() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (name: string) => {
      const { data, error } = await apiClient.POST('/api/v1/organizations', { body: { name } })
      if (error) throw new Error(errorMessage(error, 'Não foi possível criar a organização.'))
      return data
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['organizations'] })
    },
  })
}

export function useMembers(organizationId: string) {
  return useQuery({
    queryKey: ['organizations', organizationId, 'members'],
    queryFn: async () => {
      const { data, error } = await apiClient.GET(
        '/api/v1/organizations/{organization_id}/members',
        { params: { path: { organization_id: organizationId } } },
      )
      if (error) throw new Error(errorMessage(error))
      return data
    },
    enabled: Boolean(organizationId),
  })
}

/** The current user's own membership within an organization (role/status), derived from the
 * members list — used to decide which actions to show without a dedicated backend endpoint. */
export function useCurrentMembership(organizationId: string) {
  const user = useAuthStore((state) => state.user)
  const membersQuery = useMembers(organizationId)
  const membership = membersQuery.data?.find((member) => member.user_id === user?.id)
  return { membership, isLoading: membersQuery.isLoading }
}

export function useInviteMember(organizationId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (input: { email: string; role: Role }) => {
      const { data, error } = await apiClient.POST(
        '/api/v1/organizations/{organization_id}/invitations',
        { params: { path: { organization_id: organizationId } }, body: input },
      )
      if (error) throw new Error(errorMessage(error, 'Não foi possível enviar o convite.'))
      return data
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['organizations', organizationId, 'members'] })
    },
  })
}

export function useUpdateMemberRole(organizationId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (input: { userId: string; role: Role }) => {
      const { data, error } = await apiClient.PATCH(
        '/api/v1/organizations/{organization_id}/members/{user_id}',
        {
          params: { path: { organization_id: organizationId, user_id: input.userId } },
          body: { role: input.role },
        },
      )
      if (error) throw new Error(errorMessage(error, 'Não foi possível alterar o papel.'))
      return data
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['organizations', organizationId, 'members'] })
    },
  })
}

export function useRemoveMember(organizationId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (userId: string) => {
      const { error } = await apiClient.DELETE(
        '/api/v1/organizations/{organization_id}/members/{user_id}',
        { params: { path: { organization_id: organizationId, user_id: userId } } },
      )
      if (error) throw new Error(errorMessage(error, 'Não foi possível remover o membro.'))
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['organizations', organizationId, 'members'] })
    },
  })
}

/** Uses useQuery (not useMutation) deliberately: accepting an invitation is triggered once
 * from a route param via an effect-less render, and only React Query's own request
 * deduplication (keyed by queryKey) reliably collapses the double-invocation that React's
 * StrictMode performs in development — a useEffect+useRef guard does not survive it here. */
export function useAcceptInvitation(token: string | undefined) {
  return useQuery({
    queryKey: ['invitations', token, 'accept'],
    queryFn: async () => {
      const { data, error } = await apiClient.POST('/api/v1/invitations/{token}/accept', {
        params: { path: { token: token! } },
      })
      if (error) throw new Error(errorMessage(error, 'Convite inválido ou expirado.'))
      return data
    },
    enabled: Boolean(token),
    retry: false,
    staleTime: Infinity,
    gcTime: Infinity,
  })
}
