# Runbook

Este runbook reúne comandos e procedimentos para operar o Brokerly em
desenvolvimento e produção. Use-o durante incidentes, validações pós-deploy e
rotinas de manutenção.

## Comandos locais

```bash
docker compose ps
docker compose logs -f app
docker compose logs -f celery_worker
docker compose exec app python manage.py check
docker compose exec app python manage.py migrate
```

## Comandos em Swarm

```bash
docker service ls
docker service ps brokerly_app
docker service logs -f brokerly_app
docker service logs -f brokerly_celery_worker
docker stack services brokerly
```

## Healthcheck

| Componente | Verificação |
|---|---|
| App | HTTP 200 no endpoint de saúde. |
| Banco | `pg_isready`. |
| RabbitMQ | Porta AMQP e management UI. |
| Redis | `redis-cli ping`. |
| Worker | Logs sem crash loop e tasks processando. |

## Incidente: app fora do ar

1. Verifique DNS e Traefik.
2. Confira `docker service ps brokerly_app`.
3. Leia logs do app.
4. Verifique migrations recentes.
5. Se rollout falhou, avalie rollback.

```bash
docker service rollback brokerly_app
```

## Incidente: erro de banco

| Sintoma | Ação |
|---|---|
| Conexão recusada | Ver serviço `db` e healthcheck. |
| Migration travada | Conferir advisory lock e logs do entrypoint. |
| Query lenta | Revisar índices por `brokerage` e agregações. |
| Disco cheio | Checar dumps, logs e volume do PostgreSQL. |

## Incidente: tasks paradas

1. Verifique RabbitMQ.
2. Verifique worker.
3. Veja `django-celery-results`.
4. Reinicie worker se houve deploy de task nova.

```bash
docker service logs -f brokerly_celery_worker
```

## Incidente: PDF ou IA falhando

| Área | Diagnóstico |
|---|---|
| PDF | Ver `ReportJob.status` e `error_message`. |
| IA | Ver status do resumo, chave OpenAI e timeout. |
| Notificação | Conferir criação de `Notification`. |

## Incidente: vazamento cross-tenant suspeito

1. Interrompa o fluxo afetado se necessário.
2. Identifique view/query/tool envolvida.
3. Verifique filtro por `brokerage`.
4. Corrija no servidor, não no template.
5. Audite logs e registros acessados.

!!! warning "Prioridade máxima"
    Vazamento entre tenants é incidente crítico. Trate como segurança, não como
    bug visual.

## Manutenção

- Aplicar migrations apenas via fluxo de deploy.
- Rodar `collectstatic --clear` em produção.
- Testar restore periodicamente.
- Revisar logs de workers.
- Validar renovação TLS após mudanças de DNS.

## Troubleshooting rápido

| Sintoma | Provável causa | Próximo passo |
|---|---|---|
| 400 no healthcheck | Host header ausente no Traefik | Conferir labels de healthcheck. |
| 403 em relatório | Role sem permissão | Validar `User.role`. |
| 404 em download | Tenant ou dono divergente | Confirmar `brokerage` do objeto. |
| SSE não flui | Buffer do proxy | Conferir Traefik/Gunicorn. |
| OpenAI 401 | Chave ausente/inválida | Corrigir secret/env sem logar valor. |

## Registro de incidentes

Para cada incidente, registre:

- data e horário;
- impacto;
- causa raiz;
- comandos executados;
- correção aplicada;
- ação preventiva.
