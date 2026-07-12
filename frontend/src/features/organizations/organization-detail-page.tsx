import { toast } from 'sonner'
import { Link, useParams } from 'react-router'

import {
  useCurrentMembership,
  useMembers,
  useOrganization,
  useRemoveMember,
  useUpdateMemberRole,
  type Role,
} from '@/features/organizations/api'
import { InviteMemberDialog } from '@/features/organizations/invite-member-dialog'
import { CreateProjectDialog } from '@/features/projects/create-project-dialog'
import { useProjects } from '@/features/projects/api'
import { useAuthStore } from '@/stores/auth-store'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

const ROLE_LABELS: Record<Role, string> = { admin: 'Admin', editor: 'Editor', viewer: 'Viewer' }

export function OrganizationDetailPage() {
  const { orgId } = useParams<{ orgId: string }>()
  const organizationId = orgId!
  const currentUser = useAuthStore((state) => state.user)

  const { data: organization } = useOrganization(organizationId)
  const { data: members, isLoading: membersLoading } = useMembers(organizationId)
  const { data: projects, isLoading: projectsLoading } = useProjects(organizationId)
  const { membership: currentMembership } = useCurrentMembership(organizationId)

  const updateRole = useUpdateMemberRole(organizationId)
  const removeMember = useRemoveMember(organizationId)

  const isAdmin = currentMembership?.role === 'admin'
  const canCreateProject = isAdmin || currentMembership?.role === 'editor'

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold">{organization?.name ?? 'Organização'}</h1>
        {organization && <p className="text-muted-foreground">{organization.slug}</p>}
      </div>

      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-medium">Membros</h2>
          {isAdmin && <InviteMemberDialog organizationId={organizationId} />}
        </div>

        {membersLoading && <p className="text-muted-foreground">Carregando...</p>}

        {members && (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>E-mail</TableHead>
                <TableHead>Papel</TableHead>
                <TableHead>Status</TableHead>
                {isAdmin && <TableHead className="text-right">Ações</TableHead>}
              </TableRow>
            </TableHeader>
            <TableBody>
              {members.map((member) => {
                const isSelf = member.user_id === currentUser?.id
                return (
                  <TableRow key={member.id}>
                    <TableCell>{member.email}</TableCell>
                    <TableCell>
                      {isAdmin ? (
                        <Select
                          value={member.role}
                          onValueChange={(role) =>
                            updateRole.mutate(
                              { userId: member.user_id, role: role as Role },
                              { onError: (error) => toast.error(error.message) },
                            )
                          }
                        >
                          <SelectTrigger size="sm">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="admin">Admin</SelectItem>
                            <SelectItem value="editor">Editor</SelectItem>
                            <SelectItem value="viewer">Viewer</SelectItem>
                          </SelectContent>
                        </Select>
                      ) : (
                        <Badge variant="outline">{ROLE_LABELS[member.role]}</Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      <Badge variant={member.status === 'active' ? 'default' : 'secondary'}>
                        {member.status}
                      </Badge>
                    </TableCell>
                    {isAdmin && (
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          disabled={isSelf || removeMember.isPending}
                          onClick={() =>
                            removeMember.mutate(member.user_id, {
                              onError: (error) => toast.error(error.message),
                            })
                          }
                        >
                          Remover
                        </Button>
                      </TableCell>
                    )}
                  </TableRow>
                )
              })}
            </TableBody>
          </Table>
        )}
      </section>

      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-medium">Projetos</h2>
          {canCreateProject && <CreateProjectDialog organizationId={organizationId} />}
        </div>

        {projectsLoading && <p className="text-muted-foreground">Carregando...</p>}

        {!projectsLoading && projects?.length === 0 && (
          <p className="text-muted-foreground">Nenhum projeto ainda.</p>
        )}

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {projects?.map((project) => (
            <Link key={project.id} to={`/organizations/${organizationId}/projects/${project.id}`}>
              <Card className="transition-colors hover:bg-muted/50">
                <CardHeader>
                  <CardTitle>{project.name}</CardTitle>
                </CardHeader>
                {project.description && (
                  <CardContent className="text-sm text-muted-foreground">
                    {project.description}
                  </CardContent>
                )}
              </Card>
            </Link>
          ))}
        </div>
      </section>
    </div>
  )
}
