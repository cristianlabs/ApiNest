import { useParams } from 'react-router'

import { useProject } from '@/features/projects/api'

export function ProjectDetailPage() {
  const { projectId } = useParams<{ projectId: string }>()
  const { data: project, isLoading } = useProject(projectId!)

  if (isLoading) return <p className="text-muted-foreground">Carregando...</p>
  if (!project) return null

  return (
    <div className="space-y-2">
      <h1 className="text-2xl font-semibold">{project.name}</h1>
      {project.description && <p className="text-muted-foreground">{project.description}</p>}
      <p className="text-sm text-muted-foreground">
        O catálogo de APIs deste projeto chega na próxima etapa.
      </p>
    </div>
  )
}
