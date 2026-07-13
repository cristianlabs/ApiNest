import { useDashboardSummary } from '@/features/dashboard/api'
import { QueryError } from '@/components/query-error'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

function statusVariant(status: number | null): 'default' | 'destructive' | 'secondary' {
  if (status === null) return 'destructive'
  if (status >= 200 && status < 300) return 'default'
  if (status >= 400) return 'destructive'
  return 'secondary'
}

export function DashboardPage() {
  const { data, isLoading, isError, error } = useDashboardSummary()

  if (isLoading) return <p className="text-muted-foreground">Carregando...</p>
  if (isError) return <QueryError error={error} />
  if (!data) return null

  const cards = [
    { label: 'Organizações', value: data.organizations_count },
    { label: 'Projetos', value: data.projects_count },
    { label: 'APIs', value: data.apis_count },
    { label: 'Endpoints', value: data.endpoints_count },
  ]

  return (
    <div className="space-y-8">
      <h1 className="text-2xl font-semibold">Dashboard</h1>

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        {cards.map((card) => (
          <Card key={card.label}>
            <CardHeader>
              <CardTitle className="text-muted-foreground">{card.label}</CardTitle>
            </CardHeader>
            <CardContent className="text-3xl font-semibold">{card.value}</CardContent>
          </Card>
        ))}
      </div>

      <section className="space-y-3">
        <h2 className="text-lg font-medium">Status das APIs</h2>
        {data.api_statuses.length === 0 && (
          <p className="text-muted-foreground">Nenhuma requisição registrada ainda.</p>
        )}
        {data.api_statuses.length > 0 && (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>API</TableHead>
                <TableHead>Último status</TableHead>
                <TableHead>Erro</TableHead>
                <TableHead>Verificado em</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.api_statuses.map((status) => (
                <TableRow key={status.api_id}>
                  <TableCell>{status.api_name}</TableCell>
                  <TableCell>
                    <Badge variant={statusVariant(status.last_status_code)}>
                      {status.last_status_code ?? 'Erro'}
                    </Badge>
                  </TableCell>
                  <TableCell className="max-w-xs truncate text-sm text-muted-foreground">
                    {status.last_error ?? '—'}
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {status.last_checked_at
                      ? new Date(status.last_checked_at).toLocaleString('pt-BR')
                      : '—'}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </section>

      <section className="space-y-3">
        <h2 className="text-lg font-medium">Requisições recentes</h2>
        {data.recent_requests.length === 0 && (
          <p className="text-muted-foreground">Nenhuma requisição ainda.</p>
        )}
        {data.recent_requests.length > 0 && (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Método</TableHead>
                <TableHead>URL</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Duração</TableHead>
                <TableHead>Data</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.recent_requests.map((request) => (
                <TableRow key={request.id}>
                  <TableCell>
                    <Badge variant="secondary">{request.method}</Badge>
                  </TableCell>
                  <TableCell className="max-w-xs truncate font-mono text-sm">
                    {request.url}
                  </TableCell>
                  <TableCell>
                    <Badge variant={statusVariant(request.response_status_code)}>
                      {request.response_status_code ?? 'Erro'}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {request.duration_ms} ms
                  </TableCell>
                  <TableCell className="text-sm text-muted-foreground">
                    {new Date(request.created_at).toLocaleString('pt-BR')}
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
