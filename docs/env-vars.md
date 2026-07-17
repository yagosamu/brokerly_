# Variáveis de Ambiente

O Brokerly lê configuração por `.env` usando `django-environ`. O arquivo real não
é versionado; `.env.example` documenta chaves esperadas sem credenciais. Em
produção, segredos críticos devem migrar para Docker Secrets sempre que possível.

## Regras

!!! warning "Segredos"
    Nunca versione `.env`, tokens, senhas, chaves privadas ou dumps com dados
    sensíveis.

## Tabela principal

| Variável | Exemplo | Uso |
|---|---|---|
| `DEBUG` | `False` | Deve ser falso em produção. |
| `SECRET_KEY` | `***` | Chave secreta Django. |
| `DOMAIN` | `brokerly.example` | Domínio base usado no stack. |
| `ALLOWED_HOSTS` | `brokerly.example,.brokerly.example,localhost` | Hostnames aceitos. |
| `CSRF_TRUSTED_ORIGINS` | `https://brokerly.example,https://*.brokerly.example` | Origens CSRF com esquema. |
| `DATABASE_URL` | `postgres://brokerly:***@db:5432/brokerly` | Conexão PostgreSQL. |
| `POSTGRES_DB` | `brokerly` | Nome do banco. |
| `POSTGRES_USER` | `brokerly` | Usuário do banco. |
| `POSTGRES_PASSWORD` | `***` | Senha do banco. |
| `CELERY_BROKER_URL` | `amqp://brokerly:***@rabbitmq:5672//` | Broker RabbitMQ. |
| `CELERY_RESULT_BACKEND` | `redis://redis:6379/1` | Backend de resultados/cache. |
| `CACHE_URL` | `redis://redis:6379/2` | Cache Django. |
| `RABBITMQ_DEFAULT_USER` | `brokerly` | Usuário RabbitMQ. |
| `RABBITMQ_DEFAULT_PASS` | `***` | Senha RabbitMQ. |
| `OPENAI_API_KEY` | `***` | Chave OpenAI. |
| `OPENAI_MODEL` | `gpt-5.5-mini` | Modelo padrão. |
| `EMAIL_HOST` | `smtp.example.com` | Servidor SMTP. |
| `EMAIL_PORT` | `587` | Porta SMTP. |
| `EMAIL_HOST_USER` | `no-reply@brokerly.example` | Usuário SMTP. |
| `EMAIL_HOST_PASSWORD` | `***` | Senha SMTP. |
| `DEFAULT_FROM_EMAIL` | `Brokerly <no-reply@brokerly.example>` | Remetente padrão. |

## Listas

`ALLOWED_HOSTS` e `CSRF_TRUSTED_ORIGINS` são listas separadas por vírgula.
Hostname não leva `https://`; origem CSRF sempre leva esquema.

```env
ALLOWED_HOSTS=brokerly.example,.brokerly.example,localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=https://brokerly.example,https://*.brokerly.example
```

## Produção

Segredos recomendados para Docker Secrets:

- `CLOUDFLARE_DNS_API_TOKEN`
- `SECRET_KEY`
- `POSTGRES_PASSWORD`
- `RABBITMQ_DEFAULT_PASS`
- `OPENAI_API_KEY`
- `EMAIL_HOST_PASSWORD`

## Parser seguro em scripts

Scripts shell não devem usar `source .env`. Use leitura controlada de
`KEY=VALUE`, preservando caracteres especiais.

```bash
while IFS='=' read -r key value; do
    case "$key" in
        ''|\#*) continue ;;
    esac
    value="${value%\"}"; value="${value#\"}"
    value="${value%\'}"; value="${value#\'}"
    export "$key=$value"
done < .env
```

## Checklist

- [ ] `.env` está no `.gitignore`?
- [ ] Produção usa `DEBUG=False`?
- [ ] `ALLOWED_HOSTS` não contém URL completa?
- [ ] `CSRF_TRUSTED_ORIGINS` contém `https://`?
- [ ] Chave OpenAI não aparece em logs?
- [ ] `.env.example` foi atualizado quando nova variável foi criada?
