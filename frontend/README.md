# ApiNest — Frontend

SPA em Vite + React + TypeScript que consome a API do ApiNest (`../backend`).

## Stack

- **Vite + React 19 + TypeScript**
- **Tailwind CSS v4** + **shadcn/ui** (estilo "Nova")
- **React Router** — roteamento
- **TanStack Query** — cache e estado de dados do servidor
- **react-hook-form + zod** — formulários e validação
- **Zustand** — estado de autenticação (tokens/usuário atual)
- **openapi-fetch** + tipos gerados via **openapi-typescript** a partir do `openapi.json` do backend

## Setup

Pré-requisito: o backend rodando (`docker compose up` na raiz do `ApiNest`), já que os tipos da
API são gerados a partir dele e o app precisa dele para funcionar.

```bash
cd frontend
npm install
cp .env.example .env.local
npm run dev
```

Acesse http://localhost:5173.

## Scripts

```bash
npm run dev                  # servidor de desenvolvimento com HMR
npm run build                # typecheck + build de produção em dist/
npm run preview              # serve o build de produção localmente
npm run lint                 # oxlint
npm run generate:api-types   # regenera src/api/schema.d.ts a partir do openapi.json do backend
```

Rode `generate:api-types` sempre que o backend ganhar/alterar endpoints — ele precisa estar
rodando em `http://localhost:8000` (ou ajuste a URL no script em `package.json`).

## Variáveis de ambiente

| Variável | Descrição | Padrão |
|---|---|---|
| `VITE_API_BASE_URL` | Origem da API (sem `/api/v1` — os paths gerados já incluem o prefixo) | `http://localhost:8000` |

## Estrutura

```
src/
├── api/         # client.ts (cliente HTTP tipado com auth), schema.d.ts (gerado, não editar)
├── components/  # componentes shadcn/ui (components/ui) + componentes compartilhados
├── routes/      # páginas e definição de rotas (React Router)
├── stores/      # estado global (auth-store via Zustand)
└── main.tsx     # providers (QueryClient, Router, Toaster)
```

## Status

Em desenvolvimento por etapas (F0–F6), acompanhando o backend. Ver plano de implementação para
o roadmap detalhado.
