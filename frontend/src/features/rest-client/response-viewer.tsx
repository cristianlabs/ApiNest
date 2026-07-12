import type { RequestHistoryOut } from '@/features/rest-client/api'
import { Badge } from '@/components/ui/badge'

function prettyBody(body: string | null): string {
  if (!body) return ''
  try {
    return JSON.stringify(JSON.parse(body), null, 2)
  } catch {
    return body
  }
}

function statusVariant(status: number | null): 'default' | 'destructive' | 'secondary' {
  if (status === null) return 'destructive'
  if (status >= 200 && status < 300) return 'default'
  if (status >= 400) return 'destructive'
  return 'secondary'
}

export function ResponseViewer({ entry }: { entry: RequestHistoryOut }) {
  return (
    <div className="space-y-4 rounded-lg border p-4">
      <div className="flex items-center gap-2">
        <Badge variant={statusVariant(entry.response_status_code)}>
          {entry.response_status_code ?? 'Erro'}
        </Badge>
        <span className="text-sm text-muted-foreground">{entry.duration_ms} ms</span>
        <span className="truncate text-sm text-muted-foreground">
          {entry.method} {entry.url}
        </span>
      </div>

      {entry.error && <p className="text-sm text-destructive">{entry.error}</p>}

      {entry.response_headers && Object.keys(entry.response_headers).length > 0 && (
        <div className="space-y-1.5">
          <p className="text-sm font-medium">Headers</p>
          <div className="space-y-1 rounded-md bg-muted p-2 font-mono text-xs">
            {Object.entries(entry.response_headers).map(([key, value]) => (
              <div key={key}>
                <span className="text-muted-foreground">{key}:</span> {String(value)}
              </div>
            ))}
          </div>
        </div>
      )}

      {entry.response_body && (
        <div className="space-y-1.5">
          <p className="text-sm font-medium">Body</p>
          <pre className="max-h-96 overflow-auto rounded-md bg-muted p-2 font-mono text-xs whitespace-pre-wrap">
            {prettyBody(entry.response_body)}
          </pre>
        </div>
      )}
    </div>
  )
}
