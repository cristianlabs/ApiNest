import { useQuery } from '@tanstack/react-query'

import { apiClient } from '@/api/client'
import { errorMessage } from '@/lib/error-message'

import type { components } from '@/api/schema'

export type DashboardSummary = components['schemas']['DashboardSummary']

export function useDashboardSummary() {
  return useQuery({
    queryKey: ['dashboard', 'summary'],
    queryFn: async () => {
      const { data, error } = await apiClient.GET('/api/v1/dashboard/summary')
      if (error) throw new Error(errorMessage(error))
      return data
    },
  })
}
