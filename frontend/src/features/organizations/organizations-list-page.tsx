import { Link } from 'react-router'

import { CreateOrganizationDialog } from '@/features/organizations/create-organization-dialog'
import { useOrganizations } from '@/features/organizations/api'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export function OrganizationsListPage() {
  const { data: organizations, isLoading } = useOrganizations()

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Organizações</h1>
          <p className="text-muted-foreground">Organizações das quais você é membro.</p>
        </div>
        <CreateOrganizationDialog />
      </div>

      {isLoading && <p className="text-muted-foreground">Carregando...</p>}

      {!isLoading && organizations?.length === 0 && (
        <p className="text-muted-foreground">
          Você ainda não faz parte de nenhuma organização. Crie uma para começar.
        </p>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {organizations?.map((organization) => (
          <Link key={organization.id} to={`/organizations/${organization.id}`}>
            <Card className="transition-colors hover:bg-muted/50">
              <CardHeader>
                <CardTitle>{organization.name}</CardTitle>
              </CardHeader>
              <CardContent className="text-sm text-muted-foreground">
                {organization.slug}
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  )
}
