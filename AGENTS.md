# AGENTS.md — Brokerly

> **Este arquivo é o contrato técnico do projeto.** Qualquer agente de IA que escreve ou modifica código no Brokerly DEVE ler este arquivo antes de agir e DEVE seguir tudo o que está aqui sem exceção. Quando algo aqui contradisser sua intuição, **siga este arquivo**.

---

## 1. O que é o Brokerly

SaaS **multi-tenant** de gestão para corretoras de seguros, em Português Brasileiro. Cada corretora é um tenant isolado; usuários acessam apenas dados da sua própria corretora. Diferencial: agentes de IA (LangChain 1.0+ / LangGraph + OpenAI GPT-5.5-mini) que resumem entidades e respondem perguntas sobre os dados da corretora — sempre com escopo restrito ao tenant.

---

## 2. Fonte única de verdade

**`@PRD.md`** é a fonte única de verdade do produto e da arquitetura. Toda decisão de implementação DEVE citá-lo. Se este arquivo (`AGENTS.md`) e o PRD divergirem, o **PRD vence**. Atualize o AGENTS.md se notar divergência.

Para qualquer feature, encontre primeiro:

1. A seção do PRD que descreve o requisito (FXX / NFRXX).
2. A entidade na "Modelagem de Domínio" (PRD §13–14).
3. A sprint correspondente na seção 53 do PRD.

---

## 3. Stack obrigatória

| Camada | Tecnologia | Versão mínima |
|---|---|---|
| Linguagem | Python | 3.13+ |
| Framework web | Django | 6.0+ |
| Banco | PostgreSQL | 16 |
| Broker (Celery) | RabbitMQ | 3 |
| Cache / result backend | Redis | 7 |
| Background jobs | Celery + django-celery-beat + dj-celery-panel | últimas |
| IA | LangChain 1.0+ / LangGraph | últimas |
| LLM | OpenAI **GPT-5.5-mini** | — |
| PDF | ReportLab + PyPDF | últimas |
| Estáticos | WhiteNoise (`CompressedStaticFilesStorage`) | últimas |
| Web server prod | Traefik v3 + Gunicorn | — |
| Orquestração prod | Docker Swarm | — |
| Docs | MkDocs + Mermaid | — |
| Env parsing | `django-environ` | últimas |

**PROIBIDO** trocar qualquer item dessa lista sem aprovação explícita do usuário no chat.

---

## 4. Convenções de código (invioláveis)

- **Código em inglês.** Identificadores, arquivos, pastas, comentários — tudo em inglês.
- **UI em pt-BR.** Templates, mensagens, labels, e-mails, validações — tudo em Português Brasileiro.
- **Aspas simples** em Python (`'foo'`, não `"foo"`), exceto quando a string contém aspas simples.
- **PEP-8** estrito. Linhas até 99 caracteres.
- **Timezone:** `America/Sao_Paulo`. `USE_TZ=True`.
- **NÃO escreva testes.** Sem `pytest`, sem `unittest`, sem fixtures, sem mocks, sem `tests.py` — testes estão fora de escopo por decisão do produto.
- **`.venv` na raiz.** `requirements.txt` na raiz, sempre atualizado.
- **Único `settings.py`** em `core/settings.py`. Credenciais via `.env` (lidas com `django-environ`).
- **Todo model de domínio** herda `BaseModel` (timestamps `created_at`/`updated_at`) e, se for tenant-scoped, `TenantAwareModel` (FK obrigatória `brokerage`).
- **CBVs sempre que possível.** Use mixins (`LoginRequiredMixin`, `TenantQuerysetMixin`, `RoleRequiredMixin`). FBVs só para casos triviais.
- **Signals** ficam em `signals.py` da app correspondente. Registre em `apps.py` (`ready()`).
- **Valores monetários** → `DecimalField(max_digits=14, decimal_places=2)`. Percentuais → `DecimalField(max_digits=6, decimal_places=4)`. **NUNCA `FloatField`.**
- **Datas** → `DateField`/`DateTimeField` com timezone.

---

## 5. Estrutura do projeto

```
brokerly/
├── .venv/                  # ambiente virtual (gitignored)
├── .env                    # credenciais locais (gitignored)
├── .env.example            # template versionado
├── manage.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml      # dev
├── docker-stack.yml        # produção (Swarm)
├── entrypoint.sh           # app: wait_for_db + advisory lock migrate + collectstatic --clear
├── worker-entrypoint.sh    # celery: wait_for_db apenas
├── scripts/
│   ├── deploy.sh
│   └── backup.sh
├── core/                   # app principal: settings.py, urls.py, celery.py, wsgi.py
├── base/                   # app de recursos compartilhados: BaseModel, mixins, managers
├── accounts/               # User customizado (login por e-mail)
├── tenants/                # Brokerage, Plan, Subscription, TenantMiddleware
├── clients/                # cadastro de clientes
├── insurers/               # seguradoras + ramos (LineOfBusiness)
├── policies/               # apólices
├── proposals/              # propostas
├── coverages/              # coberturas + itens cobertos
├── claims/                 # sinistros
├── endorsements/           # endossos
├── renewals/               # renovações
├── partners/               # agentes + produtores
├── commissions/            # comissões + repasses
├── crm/                    # CRM (Pipeline, Stage, Deal, kanban)
├── dashboard/              # views do dashboard
├── reports/                # relatórios PDF/CSV
├── documents/              # anexos protegidos
├── notifications/          # notificações na interface
├── ai_agents/              # agentes LangChain/LangGraph
├── design_system/
│   ├── design-system.html  # ÚNICA referência visual (NUNCA inventar fora dela)
│   └── refs/duralux/       # template base
├── docs/                   # MkDocs
├── templates/              # base.html, base_app.html, base_auth.html, partials/
├── static/                 # CSS/JS custom
└── PRD.md                  # fonte única de verdade
```

**Apps Django ficam na raiz**, não em `apps/`. App principal: `core`. App de recursos compartilhados: `base`.

---

## 6. Multi-tenant — regras INVIOLÁVEIS

Brokerly usa **shared schema com FK `brokerage`** em toda entidade de domínio.

1. **Toda model sensível herda `TenantAwareModel`** (que adiciona FK `brokerage` obrigatória).
2. **Toda view privada usa `TenantQuerysetMixin`** que filtra `get_queryset()` por `request.tenant`.
3. **`TenantMiddleware`** resolve `request.tenant = request.user.brokerage` no início do request.
4. **Forms com FK** filtram o queryset do campo por tenant — usuário NUNCA pode selecionar entidade de outra corretora.
5. **`clean()`/`save()`** validam que FKs relacionadas pertencem ao mesmo `brokerage`.
6. **Tools de IA** recebem `brokerage` do servidor via factory (`build_tenant_tools(brokerage)`). O modelo NUNCA escolhe o tenant. NUNCA aceitar `brokerage_id` como argumento de tool.
7. **Constraints unique** são sempre `UniqueConstraint(fields=['brokerage', ...])`. **NUNCA** unique global em campos de domínio.
8. **Anexos/media** servidos apenas por view protegida (auth + tenant + permissão). **NUNCA** mapear `/media/` publicamente. Path: `brokerage_<id>/<app>/<uuid>.<ext>`.

Qualquer view que retorne dados de domínio sem filtro de tenant é **bug crítico de segurança**.

---

## 7. Design System

**`@design_system/design-system.html`** é a ÚNICA referência visual do projeto. Cores, tipografia, componentes, espaçamentos, ícones (Feather) e animações DEVEM vir dele. Os assets do tema (`refs/duralux/css/*` e `js/*`) são servidos via `STATICFILES_DIRS` sob o prefixo `vendor/duralux/`.

- **NUNCA invente** cor, sombra, raio, fonte, ícone ou animação fora do design system.
- **NUNCA use estilos inline.** Tudo via classes do `theme.min.css` / `bootstrap.min.css` / `tokens.css`.
- **Templates base:** `base.html` (esqueleto + assets), `base_auth.html` (login/registro), `base_app.html` (shell com sidebar + topbar).
- Tarefas de UI são de responsabilidade do orquestrador (Claude). Codex NÃO deve criar componentes visuais novos sem instrução explícita — apenas seguir os templates existentes.

---

## 8. Banco de dados e migrations

- **PostgreSQL em dev e prod.** PROIBIDO SQLite.
- **Migrations** são versionadas; nunca edite uma migration já aplicada em produção.
- Em produção, o `entrypoint.sh` aplica migrations com **advisory lock do PostgreSQL** (`pg_try_advisory_lock(1)`) para evitar corrida entre réplicas.
- `collectstatic` SEMPRE com `--noinput --clear` (evita `FileNotFoundError` do WhiteNoise em redeploys).
- **Soft delete** (`is_active`) para entidades críticas. Exclusão física só onde seguro.

---

## 9. Background jobs

- **Tarefas pesadas** (resumos de IA, PDF, e-mail) rodam no Celery worker, NUNCA no request/response.
- Padrão UX: botão dispara task → loading no botão → mensagem "você será notificado" → notificação na interface quando concluir.
- **Beat** usa `django_celery_beat.schedulers:DatabaseScheduler`.
- **Visualização** das tasks no Django Admin via `dj-celery-panel`.

---

## 10. IA — regras de implementação

- LangChain 1.0+ + LangGraph. **NUNCA trocar de framework.**
- Modelo: **GPT-5.5-mini via OpenAI**. NUNCA trocar.
- Tools recebem `brokerage` injetado no servidor (factory `build_tenant_tools(brokerage)`).
- Resumos por entidade são tasks Celery; o resultado é salvo em campo de texto da entidade (`ai_summary`) com status (`pending`/`processing`/`done`/`failed`) e `ai_summary_updated_at`.
- Chat com IA: sessões persistentes por usuário (`ChatSession`/`ChatMessage`), resposta em **streaming** (SSE), conteúdo em **Markdown** renderizado para HTML no template.

---

## 11. Padrão de commits

- **Atômicos.** Um commit = uma mudança lógica.
- **Mensagens curtas e profissionais**, em inglês, no formato `<tipo>: <descrição>`. Tipos: `feat`, `fix`, `chore`, `docs`, `refactor`, `perf`, `style`.
  - Bom: `feat: add policy generation from proposal`
  - Bom: `fix: enforce tenant filter on insurer list view`
  - Bom: `chore: bump celery to 5.3.6`
  - Ruim: `update stuff` / `WIP` / `aaa`
- **NUNCA** commitar `.env`, credenciais, ou arquivos com segredos.
- **NUNCA** dar `git push` sem aprovação explícita do usuário no chat. O fluxo padrão é: agente faz `git add` + `git commit`, usuário faz `git push`.

---

## 12. Workflow de sprint

1. Leia a sprint correspondente na seção 53 do `@PRD.md`.
2. Leia o bloco `> Decisões de implementação da Sprint N` — são diretrizes obrigatórias.
3. Execute as tasks na ordem listada.
4. Marque cada task com `- [x]` no PRD ao concluir.
5. Atualize `requirements.txt` se adicionar dependência.
6. Atualize `docs/` se a feature for visível ao usuário final.
7. Faça commits atômicos por task ou por grupo coeso de tasks.

---

## 13. Comandos comuns

```bash
# Ambiente local (Docker Compose)
docker compose up -d --build
docker compose exec app python manage.py migrate
docker compose exec app python manage.py createsuperuser
docker compose exec app python manage.py seed_demo

# Direto no host (com .venv ativa)
python manage.py runserver
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput --clear
celery -A core worker -l info
celery -A core beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler

# Docs
mkdocs serve
mkdocs build

# Deploy (apenas na VPS)
bash scripts/deploy.sh                 # ciclo completo
bash scripts/deploy.sh --skip-build    # redeploy de config
```

---

## 14. O que NUNCA fazer

- ❌ Escrever testes automatizados (qualquer framework).
- ❌ Trocar Django, Python, PostgreSQL, Celery, RabbitMQ, Redis, Traefik, OpenAI ou GPT-5.5-mini por alternativas.
- ❌ Migrar para schema-per-tenant ou database-per-tenant.
- ❌ Usar SQLite, MySQL ou qualquer banco que não seja PostgreSQL.
- ❌ Usar `FloatField` para valores monetários ou percentuais.
- ❌ Servir media/anexos sem o middleware/view de proteção.
- ❌ Aceitar `brokerage_id` como entrada (de form, request ou tool de IA).
- ❌ Implementar pagamento ou integração de billing nesta versão.
- ❌ Inventar cor, fonte, componente ou animação fora do `@design_system/design-system.html`.
- ❌ Adicionar `print()`, `pdb`, ou logs de debug em código de produção.
- ❌ Versionar `.env`, chaves, ou qualquer credencial.
- ❌ Dar `git push --force` em `main`.
- ❌ Editar migrations já aplicadas em produção.
- ❌ Pular hooks (`--no-verify`).
- ❌ Ignorar o filtro de tenant em qualquer query de domínio.

---

## 15. Quando perguntar antes de agir

Pergunte ao usuário antes de:

- Adicionar/remover dependência do `requirements.txt`.
- Alterar `settings.py` em modo que afete prod.
- Alterar `docker-stack.yml`, `docker-compose.yml`, `Dockerfile`, entrypoints, scripts de deploy.
- Mudar qualquer regra documentada neste `AGENTS.md` ou no `PRD.md`.
- Criar uma app Django nova que não esteja prevista na lista da seção 5.
- Renomear pastas, models ou campos já existentes.
- Tomar decisão de produto (escopo, prioridade, trade-off).

Para tudo que está claramente coberto pelo PRD, **execute sem perguntar**.
