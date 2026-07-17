# Deploy

O deploy de produção do Brokerly usa Docker Swarm em VPS Ubuntu, Traefik v3 como
edge, TLS Let's Encrypt via Cloudflare DNS-01 e serviços internos para app,
PostgreSQL, RabbitMQ, Redis, worker e beat.

## Topologia

| Camada | Componentes |
|---|---|
| DNS | Cloudflare com domínio e wildcard. |
| Edge | Traefik v3 nas portas 80/443. |
| App | Django com Gunicorn e réplicas. |
| Dados | PostgreSQL, Redis e RabbitMQ. |
| Jobs | Celery worker e Celery beat. |
| IA/SMTP | Serviços externos consumidos por app/worker. |

## Pré-requisitos

1. VPS Ubuntu atualizada.
2. Docker instalado.
3. Swarm inicializado.
4. Rede externa `traefik_public`.
5. `.env` de produção com valores reais.
6. Secret `CLOUDFLARE_DNS_API_TOKEN`.
7. DNS apontando para a VPS.

## Comandos base

```bash
docker swarm init
docker network create --driver overlay --attachable traefik_public
docker secret create CLOUDFLARE_DNS_API_TOKEN ./cloudflare-token.txt
```

## Build e deploy

O script `scripts/deploy.sh` executa o ciclo principal: carrega `.env` com parser
seguro, valida pré-condições, faz build/push quando aplicável, aplica o stack e
acompanha rollout.

```bash
bash scripts/deploy.sh
bash scripts/deploy.sh --skip-build
```

## Migrations

O serviço `app` aplica migrations no entrypoint. Para evitar corrida entre
réplicas, usa advisory lock do PostgreSQL. Depois roda `collectstatic --clear`.

!!! note "Start-first"
    O rollout deve favorecer atualização sem downtime e rollback automático em
    caso de falha de healthcheck.

## Traefik

Traefik usa provider Swarm, labels do serviço `app` e certificado via DNS-01.
Cloudflare deve ficar DNS-only na primeira emissão, depois Full (strict) quando
TLS estiver validado.

## Healthchecks

| Serviço | Check |
|---|---|
| app | Endpoint leve HTTP sem banco. |
| db | `pg_isready`. |
| redis | `redis-cli ping`. |
| rabbitmq | `rabbitmq-diagnostics check_port_connectivity`. |

## Pós-deploy

```bash
docker service ls
docker service ps brokerly_app
docker service logs -f brokerly_app
docker service logs -f brokerly_celery_worker
```

## Validações

- Landing pública responde em `https://brokerly.example/`.
- Login redireciona para `/painel/`.
- Admin acessível somente por usuários autorizados.
- Worker processa PDFs e resumos.
- Upload e download protegido funcionam.
- Streaming SSE funciona atrás do proxy.

## Rollback

```bash
docker service rollback brokerly_app
docker service ps brokerly_app
```

## Cuidados

- Não versionar `.env` de produção.
- Não rodar `seed_demo --flush` em produção.
- Não expor `/media/` diretamente.
- Não usar SQLite como fallback.
- Não pular healthchecks em Swarm.
