# Brokerly Docs

Brokerly é um SaaS multi-tenant para corretoras de seguros, escrito em Python e
Django, com operação em português brasileiro e isolamento rígido por corretora.
Esta documentação reorganiza o PRD em guias técnicos para desenvolvimento,
operação, segurança e deploy.

!!! note "Fonte de verdade"
    O PRD continua sendo a fonte primária do produto. Estes documentos resumem e
    estruturam as seções do PRD para consulta diária.

## Visão rápida

| Área | Descrição |
|---|---|
| Operação | Clientes, seguradoras, propostas, apólices, sinistros, endossos e renovações. |
| Comercial | CRM com pipeline, etapas e negociações em grid e Kanban. |
| Financeiro | Comissões da corretora, repasses para agentes e produtores e relatórios. |
| Inteligência | Resumos por IA e chat com ferramentas isoladas por tenant. |
| Plataforma | Celery, RabbitMQ, Redis, PostgreSQL, WhiteNoise, Traefik e Docker Swarm. |

## Para quem é esta documentação

| Perfil | Use principalmente |
|---|---|
| Pessoa desenvolvedora | Arquitetura, domínio, multi-tenant, ambiente local e runbook. |
| Operação técnica | Deploy, backup, variáveis de ambiente e Celery. |
| Revisão de segurança | Multi-tenant, permissões, mídia protegida e IA. |
| Produto/design | Modelo de domínio, permissões e visão de fluxos. |

## Como navegar

- Comece por [Arquitetura](architecture.md) para entender os blocos técnicos.
- Leia [Multi Tenant](multi-tenant.md) antes de tocar em qualquer query.
- Consulte [Modelo de Domínio](domain-model.md) quando criar ou alterar entidade.
- Use [Permissões](permissions.md) para validar escopo por perfil de usuário.
- Siga [Ambiente Local](local-dev.md) para subir o projeto em desenvolvimento.
- Use [Deploy](deploy.md), [Backup](backup.md) e [Runbook](runbook.md) em operação.

## Princípios do projeto

1. Toda entidade sensível pertence a uma corretora.
2. O usuário só enxerga dados do próprio tenant.
3. Código fica em inglês; interface e mensagens ficam em pt-BR.
4. Valores monetários usam `DecimalField`, nunca `FloatField`.
5. Tarefas pesadas rodam no Celery, não no request/response.
6. IA nunca escolhe tenant: o servidor injeta a corretora nas tools.
7. Arquivos protegidos nunca são servidos por `/media/` público.

## Stack principal

| Camada | Tecnologia |
|---|---|
| Linguagem | Python 3.13+ |
| Web | Django 6 |
| Banco | PostgreSQL 16 |
| Assíncrono | Celery, RabbitMQ e Redis |
| IA | LangChain 1.x, LangGraph e OpenAI GPT-5.5-mini |
| PDF | ReportLab e PyPDF |
| Estáticos | WhiteNoise |
| Produção | Docker Swarm, Traefik v3 e Gunicorn |

## Convenções úteis

```bash
docker compose up -d --build
docker compose exec app python manage.py migrate
docker compose exec app python manage.py check
docker compose logs -f celery_worker
```

!!! warning "Antes de implementar"
    Leia o `AGENTS.md` e a seção correspondente do PRD. Se houver conflito entre
    intuição e contrato técnico, siga o contrato técnico.

## Mapa dos documentos

- [Arquitetura](architecture.md)
- [Multi Tenant](multi-tenant.md)
- [Modelo de Domínio](domain-model.md)
- [Permissões](permissions.md)
- [Mídia Protegida](protected-media.md)
- [Agentes de IA](ai-agents.md)
- [Tarefas Celery](celery-tasks.md)
- [Variáveis de Ambiente](env-vars.md)
- [Ambiente Local](local-dev.md)
- [Deploy](deploy.md)
- [Backup](backup.md)
- [Runbook](runbook.md)
