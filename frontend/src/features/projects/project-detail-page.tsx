import { Link, useParams } from 'react-router'

import { useApis } from '@/features/apis/api'
import { ApiFormDialog } from '@/features/apis/api-form-dialog'
import { useCurrentMembership } from '@/features/organizations/api'
import { useProject } from '@/features/projects/api'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export function ProjectDetailPage() {
  const { orgId, projectId } = useParams<{ orgId: string; projectId: string }>()
  const { data: project, isLoading } = useProject(projectId!)
  const { data: apis, isLoading: apisLoading } = useApis(projectId!)
  const { membership } = useCurrentMembership(orgId!)

  const canCreateApi = membership?.role === 'admin' || membership?.role === 'editor'

  if (isLoading) return <p className="text-muted-foreground">Carregando...</p>
  if (!project) return null

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">{project.name}</h1>
        {project.description && <p className="text-muted-foreground">{project.description}</p>}
      </div>

      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-medium">APIs</h2>
          {canCreateApi && (
            <ApiFormDialog
              projectId={projectId!}
              trigger={<Button size="sm">Nova API</Button>}
            />
          )}
        </div>

        {apisLoading && <p className="text-muted-foreground">Carregando...</p>}
        {!apisLoading && apis?.length === 0 && (
          <p className="text-muted-foreground">Nenhuma API ainda.</p>
        )}

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {apis?.map((api) => (
            <Link key={api.id} to={`apis/${api.id}`}>
              <Card className="transition-colors hover:bg-muted/50">
                <CardHeader>
                  <div className="flex items-center gap-2">
                    <CardTitle>{api.name}</CardTitle>
                    <Badge variant="outline">{api.status}</Badge>
                  </div>
                </CardHeader>
                <CardContent className="text-sm text-muted-foreground">{api.base_url}</CardContent>
              </Card>
            </Link>
          ))}
        </div>
      </section>
    </div>
  )
}
