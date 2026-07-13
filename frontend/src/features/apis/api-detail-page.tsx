import { toast } from 'sonner'
import { Link, useNavigate, useParams } from 'react-router'

import { useCurrentMembership } from '@/features/organizations/api'
import { useApiDetail, useDeleteApi } from '@/features/apis/api'
import { ApiFormDialog } from '@/features/apis/api-form-dialog'
import { useEndpoints } from '@/features/endpoints/api'
import { QueryError } from '@/components/query-error'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

const ENVIRONMENT_LABELS: Record<string, string> = {
  development: 'Desenvolvimento',
  staging: 'Homologação',
  production: 'Produção',
}

const STATUS_LABELS: Record<string, string> = {
  draft: 'Rascunho',
  active: 'Ativa',
  deprecated: 'Depreciada',
}

export function ApiDetailPage() {
  const { orgId, projectId, apiId } = useParams<{
    orgId: string
    projectId: string
    apiId: string
  }>()
  const navigate = useNavigate()

  const { data: api, isLoading: apiLoading, isError: apiIsError, error: apiError } = useApiDetail(apiId)
  const {
    data: endpoints,
    isLoading: endpointsLoading,
    isError: endpointsIsError,
    error: endpointsError,
  } = useEndpoints(apiId!)
  const { membership } = useCurrentMembership(orgId!)
  const deleteMutation = useDeleteApi(apiId!, projectId!)

  const isAdmin = membership?.role === 'admin'
  const canEdit = isAdmin || membership?.role === 'editor'

  const handleDelete = () => {
    if (!confirm(`Excluir a API "${api?.name}"? Isso também exclui todos os seus endpoints.`)) return
    deleteMutation.mutate(undefined, {
      onSuccess: () => navigate(`/organizations/${orgId}/projects/${projectId}`),
      onError: (error) => toast.error(error.message),
    })
  }

  if (apiLoading) return <p className="text-muted-foreground">Carregando...</p>
  if (apiIsError) return <QueryError error={apiError} />
  if (!api) return null

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-semibold">{api.name}</h1>
            <Badge variant="outline">{STATUS_LABELS[api.status]}</Badge>
          </div>
          <p className="text-muted-foreground">{api.base_url}</p>
          <p className="text-sm text-muted-foreground">
            {ENVIRONMENT_LABELS[api.environment]}
            {api.tags.length > 0 && ` · ${api.tags.join(', ')}`}
          </p>
          {api.description && <p className="mt-2 text-sm">{api.description}</p>}
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" render={<Link to="docs" />}>
            Documentação
          </Button>
          {canEdit && (
            <>
              <ApiFormDialog
                projectId={projectId!}
                api={api}
                trigger={
                  <Button variant="outline" size="sm">
                    Editar
                  </Button>
                }
              />
              {isAdmin && (
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={handleDelete}
                  disabled={deleteMutation.isPending}
                >
                  Excluir
                </Button>
              )}
            </>
          )}
        </div>
      </div>

      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-medium">Endpoints</h2>
          {canEdit && (
            <Button size="sm" render={<Link to="endpoints/new" />}>
              Novo endpoint
            </Button>
          )}
        </div>

        {endpointsLoading && <p className="text-muted-foreground">Carregando...</p>}
        {endpointsIsError && <QueryError error={endpointsError} />}
        {!endpointsLoading && endpoints?.length === 0 && (
          <p className="text-muted-foreground">Nenhum endpoint ainda.</p>
        )}

        {endpoints && endpoints.length > 0 && (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Método</TableHead>
                <TableHead>Path</TableHead>
                <TableHead>Nome</TableHead>
                <TableHead>Ações</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {endpoints.map((endpoint) => (
                <TableRow
                  key={endpoint.id}
                  className="cursor-pointer"
                  onClick={() => navigate(`endpoints/${endpoint.id}`)}
                >
                  <TableCell>
                    <Badge variant="secondary">{endpoint.method}</Badge>
                  </TableCell>
                  <TableCell className="font-mono text-sm">{endpoint.path}</TableCell>
                  <TableCell>{endpoint.name}</TableCell>
                  <TableCell onClick={(e) => e.stopPropagation()}>
                    <Button
                      variant="outline"
                      size="sm"
                      render={
                        <Link
                          to={`/organizations/${orgId}/projects/${projectId}/rest-client?endpointId=${endpoint.id}`}
                        />
                      }
                    >
                      Usar
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </section>
    </div>
  )
}
