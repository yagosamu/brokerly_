# Brokerly: Sistema Multi-Tenant para Corretoras de Seguros

[![Python](https://img.shields.io/badge/Python-3.13+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-6.0-092E20?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Celery](https://img.shields.io/badge/Celery-RabbitMQ%20%2B%20Redis-37814A?logo=celery&logoColor=white)](https://docs.celeryq.dev/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--5.5--mini-412991?logo=openai&logoColor=white)](https://openai.com/)

Brokerly é uma plataforma SaaS para gestão de corretoras de seguros no Brasil.
Ela cobre a operação ponta a ponta: corretoras, usuários, clientes, seguradoras,
propostas, apólices, sinistros, parceiros, comissões e documentos protegidos.

O produto usa arquitetura multi-tenant em schema compartilhado: todo registro
sensível de domínio pertence a uma corretora, e as views privadas sempre limitam
os dados ao tenant do usuário autenticado.

> English version available at [README.md](README.md).

---

## Índice

- [Funcionalidades](#funcionalidades)
- [Tecnologias](#tecnologias)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Instalação e Execução Local](#instalação-e-execução-local)
- [Papéis e Permissões](#papéis-e-permissões)
- [Agentes de IA](#agentes-de-ia)
- [Fonte de Verdade do Produto](#fonte-de-verdade-do-produto)

---

## Funcionalidades

### Cadastros

- **Corretoras e assinaturas**: cadastro do tenant, planos e assinaturas
- **Usuários**: modelo customizado com login por e-mail e acesso por papel
- **Clientes**: pessoas físicas e jurídicas com contato, endereço e documentos
- **Seguradoras**: cadastro com código SUSEP, contatos e ramos de atuação
- **Parceiros**: agentes e produtores vinculados à corretora, usuários e hierarquia comercial

### Operação de Seguros

- **Propostas**: fluxo comercial antes da emissão da apólice
- **Apólices**: vigência, prêmios, parcelas, itens segurados e documentos protegidos
- **Sinistros**: abertura, acompanhamento de status, dados do evento e documentação
- **Endossos e renovações**: módulos de domínio previstos para o ciclo de vida da apólice
- **Mídia protegida**: anexos servidos por views autenticadas e isoladas por tenant

### Comissões

- **Comissões**: geração a partir de apólices com prêmio base, prêmio líquido, percentual,
  valor da seguradora, status e datas de referência
- **Repasses**: divisão de valores para agentes e produtores, com validação de tenant e
  restrição de beneficiário
- **Backfill**: comando seguro e repetível para gerar comissões ausentes de apólices existentes
- **Resumo financeiro**: soma e contagem por status de comissão para cards de dashboard

### Administração e UI

- Registros no Django Admin para gestão operacional
- Django Templates server-rendered
- Design system baseado no DuralUX
- WhiteNoise para arquivos estáticos
- Labels, validações e mensagens em Português Brasileiro

### Agentes de IA

- Agentes LangChain/LangGraph isolados por tenant
- OpenAI GPT-5.5-mini como modelo obrigatório
- Resumos de entidades e tools de chat com escopo de corretora injetado pelo servidor
- Execução em background planejada com Celery

---

## Tecnologias

| Camada | Tecnologia |
|---|---|
| Linguagem | Python 3.13+ |
| Backend | Django 6.0+ |
| Banco de dados | PostgreSQL 16 |
| Jobs assíncronos | Celery |
| Broker | RabbitMQ 3 |
| Cache / result backend | Redis 7 |
| IA / LLM | LangChain 1.0+, LangGraph, OpenAI GPT-5.5-mini |
| PDF | ReportLab, PyPDF, xhtml2pdf |
| Frontend | Django Templates, Bootstrap, design system DuralUX |
| Arquivos estáticos | WhiteNoise com arquivos comprimidos |
| Produção | Docker Swarm, Traefik v3, Gunicorn |
| Ambiente | django-environ |

---

## Estrutura do Projeto

```text
brokerly/
├── accounts/          # Usuários, login por e-mail, papéis e perfil
├── base/              # Models, mixins, managers e helpers compartilhados
├── claims/            # Sinistros
├── clients/           # Clientes, pessoas físicas e jurídicas
├── commissions/       # Comissões e repasses
├── core/              # Settings, URLs raiz, Celery, WSGI/ASGI
├── design_system/     # Referência visual e assets DuralUX
├── docs/              # Documentação do projeto
├── documents/         # Anexos protegidos
├── insurance/         # Propostas, apólices, itens, parcelas, endossos e renovações
├── insurers/          # Seguradoras e ramos
├── partners/          # Agentes e produtores
├── static/            # Assets estáticos customizados
├── templates/         # Templates Django
├── tenants/           # Corretoras, planos, assinaturas e middleware de tenant
├── manage.py
├── requirements.txt
├── docker-compose.yml
├── docker-stack.yml
└── PRD.md
```

---

## Instalação e Execução Local

O ambiente local padrão usa Docker e Docker Compose.

```bash
git clone https://github.com/yagosamu/brokerly.git
cd brokerly
cp .env.example .env
docker compose up -d --build
docker compose exec app python manage.py migrate
docker compose exec app python manage.py createsuperuser
```

Acesse `http://localhost:8000` e entre com o superusuário criado.

### Comandos úteis

```bash
docker compose exec app python manage.py check
docker compose exec app python manage.py makemigrations
docker compose exec app python manage.py migrate
docker compose exec app python manage.py backfill_commissions
```

Se executar o Django diretamente no host, use a `.venv` na raiz do projeto e
mantenha PostgreSQL, RabbitMQ e Redis disponíveis conforme os valores do `.env`.

---

## Papéis e Permissões

O Brokerly usa views por papel e querysets isolados por tenant. Um usuário só
acessa registros da própria corretora.

O modelo atual de papéis inclui:

- **Owner**: administração completa da corretora
- **Manager**: gestão operacional dentro da corretora
- **Broker**: atuação comercial e operacional no escopo da corretora
- **Agent**: acesso de parceiro comercial
- **Producer**: acesso de produtor
- **Operational**: acesso de back-office

As permissões são aplicadas por autenticação Django, mixins de papel, middleware
de tenant, querysets filtrados, forms tenant-aware e validações no model.

---

## Agentes de IA

A camada de IA do Brokerly é desenhada em torno de isolamento por tenant. As
tools recebem a corretora por factories no servidor e nunca devem aceitar
`brokerage_id` vindo do modelo ou da entrada do usuário.

Configure estas variáveis no `.env` para habilitar recursos de IA:

```env
OPENAI_API_KEY=<openai-api-key>
OPENAI_MODEL=gpt-5.5-mini
```

Sem essas variáveis, o restante da aplicação continua operacional.

---

## Fonte de Verdade do Produto

[PRD.md](PRD.md) é a fonte autoritativa para escopo de produto, arquitetura,
modelagem de domínio, escolhas de stack, sequência de sprints e decisões de
implementação.

Agentes e contribuidores do projeto também devem ler [AGENTS.md](AGENTS.md)
antes de alterar código.
