import { zodResolver } from '@hookform/resolvers/zod'
import { type ReactElement, useState } from 'react'
import { Controller, useForm } from 'react-hook-form'
import { useNavigate, useParams } from 'react-router'
import { toast } from 'sonner'
import { z } from 'zod'

import { useCreateApi, useUpdateApi, type ApiOut } from '@/features/apis/api'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
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

const schema = z.object({
  name: z.string().min(1, 'Informe um nome'),
  base_url: z.string().min(1, 'Informe a URL base'),
  description: z.string().optional(),
  environment: z.enum(['production', 'staging', 'development']),
  status: z.enum(['active', 'deprecated', 'draft']),
  tags: z.string().optional(),
})
type FormValues = z.infer<typeof schema>

function toTags(value?: string): string[] {
  if (!value) return []
  return value
    .split(',')
    .map((tag) => tag.trim())
    .filter(Boolean)
}

interface ApiFormDialogProps {
  projectId: string
  api?: ApiOut
  trigger: ReactElement
}

export function ApiFormDialog({ projectId, api, trigger }: ApiFormDialogProps) {
  const [open, setOpen] = useState(false)
  const navigate = useNavigate()
  const { orgId } = useParams<{ orgId: string }>()
  const isEdit = Boolean(api)

  const {
    register,
    control,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: api
      ? {
          name: api.name,
          base_url: api.base_url,
          description: api.description ?? '',
          environment: api.environment,
          status: api.status,
          tags: api.tags.join(', '),
        }
      : { environment: 'development', status: 'draft' },
  })

  const createMutation = useCreateApi(projectId)
  const updateMutation = useUpdateApi(api?.id ?? '', projectId)
  const mutation = isEdit ? updateMutation : createMutation

  const onSubmit = (values: FormValues) => {
    const payload = { ...values, tags: toTags(values.tags) }
    mutation.mutate(payload, {
      onSuccess: (result) => {
        setOpen(false)
        if (!isEdit && result) {
          navigate(`/organizations/${orgId}/projects/${projectId}/apis/${result.id}`)
        }
      },
      onError: (error) => toast.error(error.message),
    })
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(nextOpen) => {
        setOpen(nextOpen)
        if (!nextOpen) reset()
      }}
      disablePointerDismissal
    >
      <DialogTrigger render={trigger} />
      <DialogContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <DialogHeader>
            <DialogTitle>{isEdit ? 'Editar API' : 'Nova API'}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="api-name">Nome</Label>
              <Input id="api-name" {...register('name')} />
              {errors.name && <p className="text-sm text-destructive">{errors.name.message}</p>}
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="api-base-url">URL base</Label>
              <Input
                id="api-base-url"
                placeholder="https://api.exemplo.com"
                {...register('base_url')}
              />
              {errors.base_url && (
                <p className="text-sm text-destructive">{errors.base_url.message}</p>
              )}
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <Label htmlFor="api-environment">Ambiente</Label>
                <Controller
                  control={control}
                  name="environment"
                  render={({ field }) => (
                    <Select value={field.value} onValueChange={field.onChange}>
                      <SelectTrigger id="api-environment" className="w-full">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="development">Desenvolvimento</SelectItem>
                        <SelectItem value="staging">Homologação</SelectItem>
                        <SelectItem value="production">Produção</SelectItem>
                      </SelectContent>
                    </Select>
                  )}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="api-status">Status</Label>
                <Controller
                  control={control}
                  name="status"
                  render={({ field }) => (
                    <Select value={field.value} onValueChange={field.onChange}>
                      <SelectTrigger id="api-status" className="w-full">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="draft">Rascunho</SelectItem>
                        <SelectItem value="active">Ativa</SelectItem>
                        <SelectItem value="deprecated">Depreciada</SelectItem>
                      </SelectContent>
                    </Select>
                  )}
                />
              </div>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="api-tags">Tags (separadas por vírgula)</Label>
              <Input id="api-tags" placeholder="core, billing" {...register('tags')} />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="api-description">Descrição (opcional)</Label>
              <Textarea id="api-description" {...register('description')} />
            </div>
          </div>
          <DialogFooter>
            <Button type="submit" disabled={mutation.isPending}>
              {mutation.isPending ? 'Salvando...' : isEdit ? 'Salvar' : 'Criar'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
