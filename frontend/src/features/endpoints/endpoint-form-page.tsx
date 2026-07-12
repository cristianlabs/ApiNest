import { zodResolver } from '@hookform/resolvers/zod'
import { useEffect } from 'react'
import { Controller, useForm, type Resolver } from 'react-hook-form'
import { useNavigate, useParams } from 'react-router'
import { toast } from 'sonner'
import { z } from 'zod'

import {
  useCreateEndpoint,
  useDeleteEndpoint,
  useEndpointDetail,
  useUpdateEndpoint,
} from '@/features/endpoints/api'
import { KeyValueListEditor } from '@/features/endpoints/key-value-list-editor'
import { useCurrentMembership } from '@/features/organizations/api'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'

function isValidJsonOrEmpty(value?: string): boolean {
  if (!value || value.trim() === '') return true
  try {
    JSON.parse(value)
    return true
  } catch {
    return false
  }
}

function parseJsonOrUndefined(value?: string): unknown {
  if (!value || value.trim() === '') return undefined
  return JSON.parse(value)
}

const keyValueSchema = z.object({
  key: z.string(),
  value: z.string(),
  description: z.string().nullable().optional(),
})

const schema = z.object({
  name: z.string().min(1, 'Informe um nome'),
  method: z.enum(['GET', 'POST', 'PUT', 'PATCH', 'DELETE']),
  path: z.string().min(1, 'Informe o path'),
  headers: z.array(keyValueSchema),
  query_params: z.array(keyValueSchema),
  path_params: z.array(keyValueSchema),
  body_schema: z.string().optional().refine(isValidJsonOrEmpty, 'JSON inválido'),
  expected_status_code: z.coerce.number().int().min(100).max(599),
  expected_response_schema: z.string().optional().refine(isValidJsonOrEmpty, 'JSON inválido'),
  auth_type: z.enum(['none', 'bearer', 'basic', 'api_key', 'oauth2']),
  auth_config: z.string().optional().refine(isValidJsonOrEmpty, 'JSON inválido'),
})
type FormValues = z.infer<typeof schema>

const DEFAULT_VALUES: FormValues = {
  name: '',
  method: 'GET',
  path: '',
  headers: [],
  query_params: [],
  path_params: [],
  body_schema: '',
  expected_status_code: 200,
  expected_response_schema: '',
  auth_type: 'none',
  auth_config: '',
}

export function EndpointFormPage() {
  const { orgId, projectId, apiId, endpointId } = useParams<{
    orgId: string
    projectId: string
    apiId: string
    endpointId?: string
  }>()
  const navigate = useNavigate()
  const isEdit = Boolean(endpointId)

  const endpointQuery = useEndpointDetail(endpointId)
  const createMutation = useCreateEndpoint(apiId!)
  const updateMutation = useUpdateEndpoint(endpointId ?? '', apiId!)
  const deleteMutation = useDeleteEndpoint(endpointId ?? '', apiId!)
  const mutation = isEdit ? updateMutation : createMutation
  const { membership } = useCurrentMembership(orgId!)
  const isAdmin = membership?.role === 'admin'

  const {
    register,
    control,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema) as Resolver<FormValues>,
    defaultValues: DEFAULT_VALUES,
  })

  useEffect(() => {
    if (!endpointQuery.data) return
    const endpoint = endpointQuery.data
    reset({
      name: endpoint.name,
      method: endpoint.method,
      path: endpoint.path,
      headers: endpoint.headers,
      query_params: endpoint.query_params,
      path_params: endpoint.path_params,
      body_schema: endpoint.body_schema ? JSON.stringify(endpoint.body_schema, null, 2) : '',
      expected_status_code: endpoint.expected_status_code,
      expected_response_schema: endpoint.expected_response_schema
        ? JSON.stringify(endpoint.expected_response_schema, null, 2)
        : '',
      auth_type: endpoint.auth_type,
      auth_config: endpoint.auth_config ? JSON.stringify(endpoint.auth_config, null, 2) : '',
    })
    // reset is stable; this should only re-run when the fetched endpoint itself changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [endpointQuery.data])

  const backToApi = () => navigate(`/organizations/${orgId}/projects/${projectId}/apis/${apiId}`)

  const onSubmit = (values: FormValues) => {
    const payload = {
      ...values,
      body_schema: parseJsonOrUndefined(values.body_schema),
      expected_response_schema: parseJsonOrUndefined(values.expected_response_schema),
      auth_config: parseJsonOrUndefined(values.auth_config) as Record<string, unknown> | undefined,
    }
    mutation.mutate(payload, {
      onSuccess: () => {
        toast.success(isEdit ? 'Endpoint atualizado' : 'Endpoint criado')
        backToApi()
      },
      onError: (error) => toast.error(error.message),
    })
  }

  const handleDelete = () => {
    if (!confirm('Excluir este endpoint?')) return
    deleteMutation.mutate(undefined, {
      onSuccess: () => {
        toast.success('Endpoint excluído')
        backToApi()
      },
      onError: (error) => toast.error(error.message),
    })
  }

  if (isEdit && endpointQuery.isLoading) {
    return <p className="text-muted-foreground">Carregando...</p>
  }

  return (
    <div className="max-w-2xl space-y-6">
      <h1 className="text-2xl font-semibold">{isEdit ? 'Editar endpoint' : 'Novo endpoint'}</h1>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        <div className="grid grid-cols-[120px_1fr] gap-4">
          <div className="space-y-1.5">
            <Label htmlFor="ep-method">Método</Label>
            <Controller
              control={control}
              name="method"
              render={({ field }) => (
                <Select value={field.value} onValueChange={field.onChange}>
                  <SelectTrigger id="ep-method" className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="GET">GET</SelectItem>
                    <SelectItem value="POST">POST</SelectItem>
                    <SelectItem value="PUT">PUT</SelectItem>
                    <SelectItem value="PATCH">PATCH</SelectItem>
                    <SelectItem value="DELETE">DELETE</SelectItem>
                  </SelectContent>
                </Select>
              )}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="ep-path">Path</Label>
            <Input id="ep-path" placeholder="/users/{id}" {...register('path')} />
            {errors.path && <p className="text-sm text-destructive">{errors.path.message}</p>}
          </div>
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="ep-name">Nome</Label>
          <Input id="ep-name" {...register('name')} />
          {errors.name && <p className="text-sm text-destructive">{errors.name.message}</p>}
        </div>

        <Controller
          control={control}
          name="headers"
          render={({ field }) => (
            <KeyValueListEditor label="Headers" items={field.value} onChange={field.onChange} />
          )}
        />
        <Controller
          control={control}
          name="query_params"
          render={({ field }) => (
            <KeyValueListEditor
              label="Query params"
              items={field.value}
              onChange={field.onChange}
            />
          )}
        />
        <Controller
          control={control}
          name="path_params"
          render={({ field }) => (
            <KeyValueListEditor label="Path params" items={field.value} onChange={field.onChange} />
          )}
        />

        <div className="space-y-1.5">
          <Label htmlFor="ep-body-schema">Body schema (JSON, opcional)</Label>
          <Textarea id="ep-body-schema" rows={4} className="font-mono text-xs" {...register('body_schema')} />
          {errors.body_schema && (
            <p className="text-sm text-destructive">{errors.body_schema.message}</p>
          )}
        </div>

        <div className="grid grid-cols-[160px_1fr] gap-4">
          <div className="space-y-1.5">
            <Label htmlFor="ep-status">Status esperado</Label>
            <Input id="ep-status" type="number" {...register('expected_status_code')} />
            {errors.expected_status_code && (
              <p className="text-sm text-destructive">{errors.expected_status_code.message}</p>
            )}
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="ep-auth-type">Autenticação</Label>
            <Controller
              control={control}
              name="auth_type"
              render={({ field }) => (
                <Select value={field.value} onValueChange={field.onChange}>
                  <SelectTrigger id="ep-auth-type" className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">Nenhuma</SelectItem>
                    <SelectItem value="bearer">Bearer</SelectItem>
                    <SelectItem value="basic">Basic</SelectItem>
                    <SelectItem value="api_key">API Key</SelectItem>
                    <SelectItem value="oauth2">OAuth2</SelectItem>
                  </SelectContent>
                </Select>
              )}
            />
          </div>
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="ep-response-schema">Response schema esperado (JSON, opcional)</Label>
          <Textarea
            id="ep-response-schema"
            rows={4}
            className="font-mono text-xs"
            {...register('expected_response_schema')}
          />
          {errors.expected_response_schema && (
            <p className="text-sm text-destructive">{errors.expected_response_schema.message}</p>
          )}
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="ep-auth-config">Config de autenticação (JSON, opcional)</Label>
          <Textarea
            id="ep-auth-config"
            rows={3}
            className="font-mono text-xs"
            placeholder='{"header_name": "X-API-Key"}'
            {...register('auth_config')}
          />
          {errors.auth_config && (
            <p className="text-sm text-destructive">{errors.auth_config.message}</p>
          )}
        </div>

        <div className="flex gap-2">
          <Button type="submit" disabled={mutation.isPending}>
            {mutation.isPending ? 'Salvando...' : isEdit ? 'Salvar' : 'Criar endpoint'}
          </Button>
          <Button type="button" variant="outline" onClick={backToApi}>
            Cancelar
          </Button>
          {isEdit && isAdmin && (
            <Button
              type="button"
              variant="destructive"
              className="ml-auto"
              onClick={handleDelete}
              disabled={deleteMutation.isPending}
            >
              Excluir
            </Button>
          )}
        </div>
      </form>
    </div>
  )
}
