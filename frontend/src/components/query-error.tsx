export function QueryError({ error }: { error: Error }) {
  return <p className="text-sm text-destructive">{error.message}</p>
}
