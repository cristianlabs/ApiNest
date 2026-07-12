import { StarIcon } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'

import {
  useDeleteHistoryEntry,
  useHistory,
  useSetFavorite,
  type RequestHistoryOut,
} from '@/features/rest-client/api'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

function statusVariant(status: number | null): 'default' | 'destructive' | 'secondary' {
  if (status === null) return 'destructive'
  if (status >= 200 && status < 300) return 'default'
  if (status >= 400) return 'destructive'
  return 'secondary'
}

interface HistoryRowProps {
  entry: RequestHistoryOut
  projectId: string
  onView: (entry: RequestHistoryOut) => void
  onReuse: (entry: RequestHistoryOut) => void
}

function HistoryRow({ entry, projectId, onView, onReuse }: HistoryRowProps) {
  const favoriteMutation = useSetFavorite(entry.id, projectId)
  const deleteMutation = useDeleteHistoryEntry(entry.id, projectId)

  const toggleFavorite = () => {
    favoriteMutation.mutate(!entry.is_favorite, {
      onError: (error) => toast.error(error.message),
    })
  }

  const handleDelete = () => {
    if (!confirm('Excluir este item do histórico?')) return
    deleteMutation.mutate(undefined, {
      onError: (error) => toast.error(error.message),
    })
  }

  return (
    <TableRow className="cursor-pointer" onClick={() => onView(entry)}>
      <TableCell>
        <Badge variant="secondary">{entry.method}</Badge>
      </TableCell>
      <TableCell className="max-w-xs truncate font-mono text-sm">{entry.url}</TableCell>
      <TableCell>
        <Badge variant={statusVariant(entry.response_status_code)}>
          {entry.response_status_code ?? 'Erro'}
        </Badge>
      </TableCell>
      <TableCell className="text-sm text-muted-foreground">{entry.duration_ms} ms</TableCell>
      <TableCell className="text-sm text-muted-foreground">
        {new Date(entry.created_at).toLocaleString('pt-BR')}
      </TableCell>
      <TableCell>
        <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
          <Button
            type="button"
            variant="ghost"
            size="icon"
            aria-label="Favoritar"
            onClick={toggleFavorite}
            disabled={favoriteMutation.isPending}
          >
            <StarIcon className={entry.is_favorite ? 'fill-current text-yellow-500' : ''} />
          </Button>
          <Button type="button" variant="outline" size="sm" onClick={() => onReuse(entry)}>
            Reusar
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="text-destructive"
            onClick={handleDelete}
            disabled={deleteMutation.isPending}
          >
            Excluir
          </Button>
        </div>
      </TableCell>
    </TableRow>
  )
}

interface HistoryListProps {
  projectId: string
  onView: (entry: RequestHistoryOut) => void
  onReuse: (entry: RequestHistoryOut) => void
}

export function HistoryList({ projectId, onView, onReuse }: HistoryListProps) {
  const pageSize = 20
  const [page, setPage] = useState(1)
  const historyQuery = useHistory(projectId, page, pageSize)
  const data = historyQuery.data
  const totalPages = data ? Math.max(1, Math.ceil(data.total / data.page_size)) : 1

  return (
    <div className="space-y-3">
      <h2 className="text-lg font-medium">Histórico</h2>

      {historyQuery.isLoading && <p className="text-muted-foreground">Carregando...</p>}
      {!historyQuery.isLoading && data?.items.length === 0 && (
        <p className="text-muted-foreground">Nenhuma requisição ainda.</p>
      )}

      {data && data.items.length > 0 && (
        <>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Método</TableHead>
                <TableHead>URL</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Duração</TableHead>
                <TableHead>Data</TableHead>
                <TableHead>Ações</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.items.map((entry) => (
                <HistoryRow
                  key={entry.id}
                  entry={entry}
                  projectId={projectId}
                  onView={onView}
                  onReuse={onReuse}
                />
              ))}
            </TableBody>
          </Table>

          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">
              Página {data.page} de {totalPages} ({data.total} no total)
            </p>
            <div className="flex gap-2">
              <Button
                type="button"
                variant="outline"
                size="sm"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
              >
                Anterior
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => p + 1)}
              >
                Próxima
              </Button>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
