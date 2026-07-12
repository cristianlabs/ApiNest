import SwaggerUI from 'swagger-ui-react'
import 'swagger-ui-react/swagger-ui.css'
import { useParams } from 'react-router'

import { useApiSpec } from '@/features/apis/api'

export function ApiDocsPage() {
  const { apiId } = useParams<{ apiId: string }>()
  const { data: spec, isLoading, error } = useApiSpec(apiId)

  if (isLoading) return <p className="text-muted-foreground">Carregando documentação...</p>
  if (error) return <p className="text-destructive">{error.message}</p>
  if (!spec) return null

  return (
    <div className="rounded-lg border bg-white">
      <SwaggerUI spec={spec} />
    </div>
  )
}
