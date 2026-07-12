import { zodResolver } from '@hookform/resolvers/zod'
import { useEffect } from 'react'
import { Controller, useForm, type Resolver } from 'react-hook-form'
import { toast } from 'sonner'
import { z } from 'zod'

import { useSendRequest, type RequestHistoryOut, type SendRequestInput } from '@/features/rest-client/api'
import { KeyValueListEditor } from '@/features/endpoints/key-value-list-editor'
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
  method: z.enum(['GET', 'POST', 'PUT', 'PATCH', 'DELETE']),
  url: z.string().min(1, 'Informe a URL'),
  headers: z.array(keyValueSchema),
  query_params: z.array(keyValueSchema),
  body: z.string().optional().refine(isValidJsonOrEmpty, 'JSON inválido'),
  auth_type: z.enum(['none', 'bearer', 'basic', 'api_key', 'oauth2']),
  auth_token: z.string().optional(),
  auth_username: z.string().optional(),
  auth_password: z.string().optional(),
  auth_header_name: z.string().optional(),
})
export type RequestFormValues = z.infer<typeof schema>

export const DEFAULT_REQUEST_VALUES: RequestFormValues = {
  method: 'GET',
  url: '',
  headers: [],
  query_params: [],
  body: '',
  auth_type: 'none',
  auth_token: '',
  auth_username: '',
  auth_password: '',
  auth_header_name: '',
}

interface RequestFormProps {
  projectId: string
  canSend: boolean
  prefill?: RequestFormValues
  linkedIds?: { api_id?: string | null; endpoint_id?: string | null }
  onSent: (entry: RequestHistoryOut) => void
}

export function RequestForm({ projectId, canSend, prefill, linkedIds, onSent }: RequestFormProps) {
  const mutation = useSendRequest(projectId)

  const {
    register,
    control,
    handleSubmit,
    reset,
    watch,
    formState: { errors },
  } = useForm<RequestFormValues>({
    resolver: zodResolver(schema) as Resolver<RequestFormValues>,
    defaultValues: DEFAULT_REQUEST_VALUES,
  })

  useEffect(() => {
    if (prefill) reset(prefill)
  }, [prefill, reset])

  const authType = watch('auth_type')

  const onSubmit = (values: RequestFormValues) => {
    const payload: SendRequestInput = {
      ...values,
      ...linkedIds,
      body: parseJsonOrUndefined(values.body),
      auth_token: values.auth_token || undefined,
      auth_username: values.auth_username || undefined,
      auth_password: values.auth_password || undefined,
      auth_header_name: values.auth_header_name || undefined,
    }
    mutation.mutate(payload, {
      onSuccess: (result) => {
        if (result) onSent(result)
      },
      onError: (error) => toast.error(error.message),
    })
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div className="grid grid-cols-[120px_1fr] gap-4">
        <div className="space-y-1.5">
          <Label htmlFor="rc-method">Método</Label>
          <Controller
            control={control}
            name="method"
            render={({ field }) => (
              <Select value={field.value} onValueChange={field.onChange}>
                <SelectTrigger id="rc-method" className="w-full">
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
          <Label htmlFor="rc-url">URL</Label>
          <Input id="rc-url" placeholder="https://api.exemplo.com/users" {...register('url')} />
          {errors.url && <p className="text-sm text-destructive">{errors.url.message}</p>}
        </div>
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
          <KeyValueListEditor label="Query params" items={field.value} onChange={field.onChange} />
        )}
      />

      <div className="space-y-1.5">
        <Label htmlFor="rc-body">Body (JSON, opcional)</Label>
        <Textarea id="rc-body" rows={5} className="font-mono text-xs" {...register('body')} />
        {errors.body && <p className="text-sm text-destructive">{errors.body.message}</p>}
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="rc-auth-type">Autenticação</Label>
        <Controller
          control={control}
          name="auth_type"
          render={({ field }) => (
            <Select value={field.value} onValueChange={field.onChange}>
              <SelectTrigger id="rc-auth-type" className="w-full max-w-xs">
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

      {(authType === 'bearer' || authType === 'oauth2') && (
        <div className="space-y-1.5">
          <Label htmlFor="rc-auth-token">Token</Label>
          <Input id="rc-auth-token" {...register('auth_token')} />
        </div>
      )}

      {authType === 'api_key' && (
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <Label htmlFor="rc-auth-header-name">Nome do header</Label>
            <Input id="rc-auth-header-name" placeholder="X-API-Key" {...register('auth_header_name')} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="rc-auth-token-key">Valor</Label>
            <Input id="rc-auth-token-key" {...register('auth_token')} />
          </div>
        </div>
      )}

      {authType === 'basic' && (
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1.5">
            <Label htmlFor="rc-auth-username">Usuário</Label>
            <Input id="rc-auth-username" {...register('auth_username')} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="rc-auth-password">Senha</Label>
            <Input id="rc-auth-password" type="password" {...register('auth_password')} />
          </div>
        </div>
      )}

      <Button type="submit" disabled={mutation.isPending || !canSend}>
        {mutation.isPending ? 'Enviando...' : 'Enviar'}
      </Button>
      {!canSend && (
        <p className="text-sm text-muted-foreground">
          Seu papel não permite enviar requisições nesta organização.
        </p>
      )}
    </form>
  )
}
