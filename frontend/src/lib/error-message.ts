/**
 * Extracts a human-readable message from a FastAPI-style error body, which can be either
 * `{"detail": "some message"}` (HTTPException) or `{"detail": [{"msg": "...", ...}, ...]}`
 * (Pydantic validation errors).
 */
export function errorMessage(error: unknown, fallback = 'Algo deu errado. Tente novamente.'): string {
  if (error && typeof error === 'object' && 'detail' in error) {
    const detail = (error as { detail: unknown }).detail
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail)) {
      return detail
        .map((item) =>
          item && typeof item === 'object' && 'msg' in item ? String(item.msg) : String(item),
        )
        .join('; ')
    }
  }
  return fallback
}
