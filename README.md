# ApiNest

Plataforma de gerenciamento de APIs — cadastro, documentação, cliente REST, monitoramento, analytics e controle de acesso.

## Desenvolvimento local

```bash
cp backend/.env.example backend/.env
docker compose up --build
```

- API: http://localhost:8000
- Health check: http://localhost:8000/health
- Docs (Swagger): http://localhost:8000/docs
- Adminer (opcional): `docker compose --profile tools up adminer` → http://localhost:8080

## Migrations

```bash
docker compose exec api alembic revision --autogenerate -m "mensagem"
docker compose exec api alembic upgrade head
```

## Testes

```bash
docker compose exec api pytest                                    # suíte completa
docker compose exec api pytest --cov --cov-report=term-missing    # com cobertura
```

## CI

O workflow em `.github/workflows/ci.yml` roda a cada push/PR: sobe Postgres e Redis como
services, instala as dependências, roda lint (`ruff`), aplica as migrations e roda a suíte de
testes com cobertura (mínimo de 70%, relatório publicado como artifact).

## Funcionalidades do MVP (implementadas)

- **Autenticação**: registro/login com JWT + refresh token (rotação single-use), e-mail case-insensitive.
- **Organizações e projetos**: papéis ADMIN/EDITOR/VIEWER, convites, proteção contra remover o último admin.
- **Catálogo de APIs e Endpoints**: CRUD com tags, ambientes, headers/query/path params estruturados.
- **Cliente REST embutido**: envia requisições reais (GET/POST/PUT/PATCH/DELETE) com Bearer/Basic/API Key,
  histórico paginado, proteção contra SSRF (bloqueia IPs privados/loopback e pina a conexão no IP validado).
- **Documentação OpenAPI**: `GET /api/v1/apis/{id}/openapi.json` e `/docs` (Swagger UI) gerados a partir dos
  endpoints cadastrados.
- **Dashboard**: `GET /api/v1/dashboard/summary` com contagens, requisições recentes e status da última
  chamada por API.

## Observabilidade

Toda resposta inclui um header `X-Request-ID` (gerado ou propagado a partir do request), disponível também
no contexto dos logs estruturados (loguru). Exceções não tratadas retornam um erro genérico 500 em JSON e
são logadas com stack trace completo, sem vazar detalhes internos para o cliente.

## Status

Em desenvolvimento — MVP por etapas. Ver plano de implementação para o roadmap detalhado.
