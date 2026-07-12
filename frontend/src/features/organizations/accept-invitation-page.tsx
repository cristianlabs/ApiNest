import { Link, useParams } from 'react-router'

import { useAcceptInvitation } from '@/features/organizations/api'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export function AcceptInvitationPage() {
  const { token } = useParams<{ token: string }>()
  const query = useAcceptInvitation(token)

  return (
    <div className="flex min-h-svh items-center justify-center p-4">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>Convite</CardTitle>
          <CardDescription>
            {query.isLoading && 'Processando seu convite...'}
            {query.isSuccess && 'Convite aceito com sucesso!'}
            {query.isError && query.error.message}
          </CardDescription>
        </CardHeader>
        {(query.isSuccess || query.isError) && (
          <CardContent>
            <Button render={<Link to="/organizations" />} className="w-full">
              Ver organizações
            </Button>
          </CardContent>
        )}
      </Card>
    </div>
  )
}
