import { useEffect, useMemo, useState } from 'react'
import { useParams, useSearchParams } from 'react-router'

import { useApiDetail } from '@/features/apis/api'
import { useEndpointDetail } from '@/features/endpoints/api'
import { useCurrentMembership } from '@/features/organizations/api'
import { HistoryList } from '@/features/rest-client/history-list'
import { ResponseViewer } from '@/features/rest-client/response-viewer'
import { RequestForm, type RequestFormValues } from '@/features/rest-client/request-form'
import type { RequestHistoryOut } from '@/features/rest-client/api'

interface FormSeed {
  key: string
  values: RequestFormValues
  linkedIds: { api_id?: string | null; endpoint_id?: string | null }
}

function historyToFormValues(entry: RequestHistoryOut): RequestFormValues {
  return {
    method: entry.method,
    url: entry.url,
    headers: entry.request_headers,
    query_params: entry.request_query_params,
    body:
      entry.request_body !== null && entry.request_body !== undefined
        ? JSON.stringify(entry.request_body, null, 2)
        : '',
    auth_type: entry.auth_type,
    auth_token: '',
    auth_username: '',
    auth_password: '',
    auth_header_name: '',
  }
}

export function RestClientPage() {
  const { orgId, projectId } = useParams<{ orgId: string; projectId: string }>()
  const [searchParams] = useSearchParams()
  const endpointId = searchParams.get('endpointId') ?? undefined

  const { membership } = useCurrentMembership(orgId!)
  const canSend = membership?.role === 'admin' || membership?.role === 'editor'

  const endpointQuery = useEndpointDetail(endpointId)
  const apiQuery = useApiDetail(endpointQuery.data?.api_id)

  const [seed, setSeed] = useState<FormSeed | undefined>(undefined)
  const [latest, setLatest] = useState<RequestHistoryOut | undefined>(undefined)

  useEffect(() => {
    if (!endpointQuery.data || !apiQuery.data) return
    const endpoint = endpointQuery.data
    const base = apiQuery.data.base_url.replace(/\/$/, '')
    const path = endpoint.path.startsWith('/') ? endpoint.path : `/${endpoint.path}`
    const headerName =
      endpoint.auth_type === 'api_key' &&
      endpoint.auth_config &&
      typeof endpoint.auth_config.header_name === 'string'
        ? (endpoint.auth_config.header_name as string)
        : ''
    setSeed({
      key: `endpoint-${endpoint.id}`,
      values: {
        method: endpoint.method,
        url: base + path,
        headers: endpoint.headers,
        query_params: endpoint.query_params,
        body: endpoint.body_schema ? JSON.stringify(endpoint.body_schema, null, 2) : '',
        auth_type: endpoint.auth_type,
        auth_token: '',
        auth_username: '',
        auth_password: '',
        auth_header_name: headerName,
      },
      linkedIds: { api_id: endpoint.api_id, endpoint_id: endpoint.id },
    })
    // Only re-seed when the fetched endpoint itself changes, not on every render.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [endpointQuery.data, apiQuery.data])

  const handleReuse = (entry: RequestHistoryOut) => {
    setSeed({
      key: `history-${entry.id}-${Date.now()}`,
      values: historyToFormValues(entry),
      linkedIds: { api_id: entry.api_id, endpoint_id: entry.endpoint_id },
    })
    setLatest(entry)
  }

  const prefill = useMemo(() => seed?.values, [seed])
  const linkedIds = useMemo(() => seed?.linkedIds ?? {}, [seed])

  return (
    <div className="max-w-3xl space-y-8">
      <h1 className="text-2xl font-semibold">Cliente REST</h1>

      <RequestForm
        key={seed?.key ?? 'blank'}
        projectId={projectId!}
        canSend={canSend}
        prefill={prefill}
        linkedIds={linkedIds}
        onSent={setLatest}
      />

      {latest && <ResponseViewer entry={latest} />}

      <HistoryList projectId={projectId!} onView={setLatest} onReuse={handleReuse} />
    </div>
  )
}
