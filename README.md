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
docker compose exec api pytest
```

## Status

Em desenvolvimento — MVP por etapas. Ver plano de implementação para o roadmap detalhado.
