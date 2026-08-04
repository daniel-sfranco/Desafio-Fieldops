# Desafio técnico — FieldOps

**Vaga:** Desenvolvedor(a) — Projetos Multiplataforma

> **Versão:** 2.2

---

## Contexto

A **FieldOps** é uma empresa fictícia de manutenção de campo. Sua tarefa é entregar uma aplicação full stack para gestão de **ordens de serviço (OS)** com regras de negócio reais.

O sistema será usado por técnicos em campo, supervisores de equipe e administradores. Cada perfil enxerga e altera apenas o que lhe cabe.

---

## Prazo e esforço


| Item             | Detalhe                                     |
| ---------------- | ------------------------------------------- |
| Prazo máximo     | **6 dias corridos** a partir do recebimento |
| Esforço estimado | **12 a 16 horas**                           |
| Itens bônus      | Opcionais                                   |


---

## Stack permitida

**Opção A:** React + TypeScript · Node.js + TypeScript · Prisma · MySQL ou PostgreSQL

**Opção B:** React + TypeScript · Python (FastAPI) · SQL relacional

**Restrições:** banco relacional · JWT com `role` e `teamId` · frontend React + TypeScript

---

## Convenções do projeto

Estas convenções fazem parte do contrato da API e do banco:


| Área              | Convenção                                                                     |
| ----------------- | ----------------------------------------------------------------------------- |
| Revisão da API    | `2026.2` — retornada em `GET /health` e enviada no webhook (`X-Api-Revision`) |
| Códigos de erro   | prefixo `FLX_` (ex.: `FLX_FORBIDDEN`)                                         |
| Rastreio          | todo erro inclui `flxTraceId` (UUID)                                          |
| Tabelas SQL       | prefixo `flx_` (ex.: `flx_work_orders`)                                       |
| Paginação (query) | parâmetro `perPage` — a resposta usa `meta.limit` com o mesmo valor numérico  |
| Usuários de seed  | domínio `@fieldops.eval`                                                      |


---

## Modelo de domínio

### Usuário (`flx_users`)


| Campo      | Tipo            | Observação                                   |
| ---------- | --------------- | -------------------------------------------- |
| `id`       | UUID ou inteiro | —                                            |
| `email`    | string          | único                                        |
| `password` | string          | hash (bcrypt ou argon2)                      |
| `name`     | string          | —                                            |
| `role`     | enum            | `technician`                                 |
| `teamId`   | string          | obrigatório para `technician` e `supervisor` |


### Ordem de serviço (`flx_work_orders`)


| Campo                     | Tipo             | Observação                                        |
| ------------------------- | ---------------- | ------------------------------------------------- |
| `id`                      | UUID ou inteiro  | —                                                 |
| `title`                   | string           | obrigatório                                       |
| `description`             | string           | opcional                                          |
| `status`                  | enum             | `open`                                            |
| `priority`                | enum             | `low`                                             |
| `resolutionNotes`         | string           | obrigatório para `done` (mín. 10 caracteres)      |
| `assigneeId`              | FK → `flx_users` | apenas usuários com `role: technician`            |
| `teamId`                  | string           | equipe da OS                                      |
| `version`                 | inteiro          | controle de concorrência otimista (inicia em `1`) |
| `createdAt` / `updatedAt` | datetime         | —                                                 |


### Checklist (`flx_checklist_items`)

Criado automaticamente com **pelo menos 1 item** em toda nova OS.


| Campo         | Tipo            |
| ------------- | --------------- |
| `id`          | UUID ou inteiro |
| `workOrderId` | FK              |
| `label`       | string          |
| `completed`   | boolean         |


### Auditoria (`flx_work_order_events`)

Registre **cada** alteração de `status`.


| Campo         | Tipo            |
| ------------- | --------------- |
| `id`          | UUID ou inteiro |
| `workOrderId` | FK              |
| `actorId`     | FK usuário      |
| `fromStatus`  | enum ou `null`  |
| `toStatus`    | enum            |
| `createdAt`   | datetime        |


---

## Regras de negócio

### Papéis e escopo


| Papel        | Escopo                                                        |
| ------------ | ------------------------------------------------------------- |
| `technician` | Acessa somente OS da sua `teamId` **em que é o `assigneeId`** |
| `supervisor` | Acessa todas as OS da sua `teamId`; pode definir `assigneeId` |
| `admin`      | Acesso global                                                 |


O escopo vale para **listagem e detalhe**. Um técnico não pode filtrar ou burlar escopo via query string.

Documente no README se retorna `403` ou `404` fora do escopo.

### Transições de status

```
open → in_progress → done
in_progress → open   (condicionado ao checklist)
```


| Transição                    | Pré-condição                                          |
| ---------------------------- | ----------------------------------------------------- |
| `→ in_progress`              | `assigneeId` preenchido com técnico da mesma `teamId` |
| `→ done`                     | `resolutionNotes` ≥ 10 caracteres                     |
| `→ done` se `priority: high` | apenas `supervisor` ou `admin`                        |
| `in_progress → open`         | ao menos um item do checklist com `completed: false`  |


Transição inválida → `4xx` com `FLX_INVALID_STATUS_TRANSITION`.

### Concorrência otimista

Toda alteração de `status` envia `version` atual. Se o registro mudou desde a leitura:

- retornar `**409 Conflict**` com `FLX_CONCURRENT_UPDATE`
- **não** aplicar a transição

Inclua teste com duas requisições concorrentes.

### Webhook

Disparar `POST {WEBHOOK_URL}` após mudança de `status` bem-sucedida.

**Headers:**

- `Content-Type: application/json`
- `X-Api-Revision: 2026.2`
- `X-Signature: <HMAC-SHA256 do body em hex>` (`WEBHOOK_SECRET`)

**Body:**

```json
{
  "eventId": "550e8400-e29b-41d4-a716-446655440000",
  "workOrderId": 1,
  "fromStatus": "open",
  "toStatus": "in_progress",
  "actorId": 2,
  "occurredAt": "2026-06-19T14:00:00.000Z"
}
```

Reentregas com o mesmo `eventId` não devem gerar efeito duplicado (idempotência).

---

## API — Backend

### Auth JWT

- `POST /auth/register` (seed documentado)
- `POST /auth/login`
- Claims: `sub`, `role`, `teamId`
- Token inválido → `401` / `FLX_UNAUTHORIZED`

### Ordens de serviço


| Método   | Rota                       | Observação                                                    |
| -------- | -------------------------- | ------------------------------------------------------------- |
| `POST`   | `/work-orders`             | cria OS + checklist inicial                                   |
| `GET`    | `/work-orders`             | listagem paginada (ver abaixo)                                |
| `GET`    | `/work-orders/:id`         | detalhe                                                       |
| `PATCH`  | `/work-orders/:id`         | status, assignee, notas; exige `version` em mudança de status |
| `DELETE` | `/work-orders/:id`         | opcional — documente se omitir                                |
| `GET`    | `/work-orders/:id/history` | eventos de auditoria                                          |


### Listagem

```
GET /work-orders?page=1&perPage=20&status=open&priority=high&sort=createdAt:desc
```


| Parâmetro            | Regra                                         |
| -------------------- | --------------------------------------------- |
| `page`               | ≥ 1, padrão `1`                               |
| `perPage`            | 1–100, padrão `20`                            |
| `status`, `priority` | filtros opcionais respeitando escopo do papel |
| `sort`               | `createdAt:asc`                               |


**Resposta:**

```json
{
  "data": [],
  "meta": {
    "page": 1,
    "limit": 20,
    "total": 0,
    "totalPages": 0
  }
}
```

`meta.limit` deve refletir o `perPage` efetivo. Página além do intervalo → `data: []`, sem erro 500.

### Health

```
GET /health
```

```json
{
  "status": "ok",
  "apiRevision": "2026.2",
  "service": "fieldops-lite"
}
```

### Erros

```json
{
  "error": {
    "code": "FLX_VALIDATION_ERROR",
    "message": "perPage must be between 1 and 100",
    "flxTraceId": "8f4e2a1b-3c5d-4e6f-9a0b-1c2d3e4f5a6b",
    "details": {}
  }
}
```

Códigos esperados: `FLX_UNAUTHORIZED`, `FLX_FORBIDDEN`, `FLX_NOT_FOUND`, `FLX_VALIDATION_ERROR`, `FLX_INVALID_STATUS_TRANSITION`, `FLX_CONCURRENT_UPDATE`.

### Testes (mínimo 8)


| Área                                              | Mín. |
| ------------------------------------------------- | ---- |
| Auth e escopo (listagem + detalhe)                | 2    |
| Paginação com `perPage`                           | 2    |
| Transições de status                              | 2    |
| `high` bloqueado para `technician`                | 1    |
| Concorrência (`409`) ou webhook (HMAC + revision) | 1    |


Testes devem validar comportamento real.

---

## Frontend (React + TypeScript)

1. Login, logout, token persistido
2. Listagem com `perPage`, filtros, ordenação
3. Criar/editar OS conforme papel
4. Mudança de status com `version` e `resolutionNotes` quando necessário
5. Histórico de auditoria
6. Exibir `error.code` (e `flxTraceId` em ambiente de desenvolvimento)
7. UI adaptada ao papel do usuário logado
8. Estados de loading, erro e lista vazia

---

## DevOps e documentação

### Docker

`docker compose up` sobe API + banco. Incluir `.env.example` (`WEBHOOK_URL`, `WEBHOOK_SECRET`, etc.).

### CI

GitHub Actions executando testes em push ou PR.

### Commits

Mínimo **8 commits** em branches `feature/`*, com pelo menos **1 merge** para `main`.

### README.md

1. Setup (Docker e local)
2. Diagrama do fluxo principal
3. **2–3 ADRs** com decisões reais do seu código (concorrência, escopo por papel, webhook)
4. Tabela de usuários seed (`@fieldops.eval`)
5. Limitações conhecidas

### AI_USAGE.md

Documentação **honesta** sobre ferramentas de apoio (IDE, assistentes, etc.):

1. O que foi gerado automaticamente e o que você revisou manualmente
2. Pelo menos **uma** decisão técnica em que você **discordou** da sugestão automática — explique o porquê
3. Partes escritas sem assistente
4. Limitações que permanecem na entrega

> Este arquivo será confrontado com o código no debrief. Descrições genéricas não substituem compreensão do que foi entregue.

---

## Usuários seed (obrigatório)


| Email                        | Senha         | Role         | teamId       |
| ---------------------------- | ------------- | ------------ | ------------ |
| `tech-a@fieldops.eval`       | `password123` | `technician` | `team-alpha` |
| `tech-b@fieldops.eval`       | `password123` | `technician` | `team-beta`  |
| `supervisor-a@fieldops.eval` | `password123` | `supervisor` | `team-alpha` |
| `admin@fieldops.eval`        | `password123` | `admin`      | —            |


---

## Bônus (até 2)


| ID  | Item                               |
| --- | ---------------------------------- |
| B1  | GCP / `DEPLOY.md`                  |
| B2  | n8n consumindo webhook             |
| B3  | Mobile (lista + detalhe)           |
| B4  | E2E (login → criar OS → transição) |
| B5  | OpenAPI + client tipado            |


---

## Regras

- Trabalho individual
- Ferramentas de apoio permitidas; você deve compreender e explicar a entrega
- Não usar código proprietário de empregadores anteriores

---

## Entrega

- Repositório GitHub
- `README.md` + `AI_USAGE.md`
- Opcional: URL de demo ou vídeo ≤ 5 min

---

## O que avaliamos


| Avaliamos                                   | Não avaliamos  |
| ------------------------------------------- | -------------- |
| Regras de negócio e escopo correto          | Pixel-perfect  |
| API e paginação (`perPage`)                 | Framework CSS  |
| Testes relevantes                           | Bônus omitidos |
| Concorrência e webhook                      |                |
| ADRs e `AI_USAGE.md` coerentes com o código |                |
| Explicação no debrief                       |                |


---

## Dúvidas

Objetivas sobre escopo até a metade do prazo, por e-mail.

---

