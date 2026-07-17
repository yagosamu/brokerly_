# Ambiente Local

O ambiente local usa Docker Compose para manter paridade com produção:
PostgreSQL, RabbitMQ, Redis, app Django, Celery worker e Celery beat. O objetivo é
evitar diferenças entre dev e produção, especialmente no banco.

## Pré-requisitos

- Docker Desktop ou Docker Engine com Compose.
- Python 3.13+ para comandos opcionais no host.
- `.env` baseado em `.env.example`.
- Portas 8000, 5432, 5672, 15672 e 6379 disponíveis.

## Serviços

| Serviço | Porta | Função |
|---|---:|---|
| `app` | 8000 | Django dev server. |
| `db` | 5432 | PostgreSQL 16. |
| `rabbitmq` | 5672/15672 | Broker e UI. |
| `redis` | 6379 | Cache/result backend. |
| `celery_worker` | n/a | Tarefas assíncronas. |
| `celery_beat` | n/a | Agendamentos. |

## Subir ambiente

```bash
docker compose up -d --build
docker compose exec app python manage.py migrate
docker compose exec app python manage.py createsuperuser
```

## Comandos úteis

```bash
docker compose ps
docker compose logs -f app
docker compose logs -f celery_worker
docker compose exec app python manage.py check
docker compose exec app python manage.py shell
```

## Fluxo de desenvolvimento

1. Leia o PRD e o `AGENTS.md`.
2. Implemente a mudança no app correto.
3. Rode migrations quando houver model.
4. Rode `python manage.py check`.
5. Valide manualmente com shell ou HTTP.
6. Atualize PRD/docs quando a sprint pedir.
7. Faça commits atômicos.

## Migrations

```bash
docker compose exec app python manage.py makemigrations
docker compose exec app python manage.py migrate
docker compose exec app python manage.py makemigrations --check --dry-run
```

!!! warning "Não edite migrations aplicadas"
    Se uma migration já foi aplicada em produção, crie nova migration corretiva.

## Celery local

Workers já sobem pelo Compose. Se alterar tasks ou apps, reinicie o worker:

```bash
docker compose restart celery_worker celery_beat
```

## Semear dados de demonstração

Para popular o ambiente com dados fake diversos:

```bash
docker compose exec app python manage.py seed_demo --brokerages 3
```

Flags úteis:

- `--flush` — apaga TODOS os dados de domínio antes, mantendo superusers.
- `--seed N` — semente reproduzível (default `42`).
- `--with-files` — cria anexos PDF placeholder.
- `--force` — necessário em ambientes com `DEBUG=False`.

Usuários criados:

- `owner@corretora-1.local`
- `owner@corretora-2.local`
- `owner@corretora-3.local`

Senha padrão:

```text
Brokerly@2026
```

## Documentação local

Docs usam dependências separadas:

```bash
python -m venv .docsvenv
.docsvenv/bin/pip install -r requirements-docs.txt
.docsvenv/bin/mkdocs serve
```

No PowerShell:

```powershell
.docsvenv\Scripts\pip install -r requirements-docs.txt
.docsvenv\Scripts\mkdocs serve
```

## Problemas comuns

| Sintoma | Ação |
|---|---|
| Docker API indisponível | Abrir Docker Desktop e aguardar engine. |
| Banco não resolve `db` no host | Rode comandos dentro do container `app`. |
| Worker não vê task nova | Reinicie `celery_worker`. |
| Static antigo | Rode `collectstatic --clear` em cenário de deploy. |
| Erro de OpenAI | Verifique `OPENAI_API_KEY` no ambiente correto. |
