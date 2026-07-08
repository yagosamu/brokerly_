# AI Summaries Sprint 21 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add tenant-scoped LangGraph summary agents for clients, policies, proposals, claims, and CRM deals.

**Architecture:** Create a dedicated `ai_agents` app with tenant-scoped LangChain tools, prompt definitions, LangGraph ReAct agent factory, synchronous service core, Celery task wrapper, and JSON endpoints for trigger/status polling. No templates or UI are created.

**Tech Stack:** Django 6, Celery, LangChain 1.x, LangGraph 1.x, langchain-openai, OpenAI GPT-5.5-mini, existing Brokerly tenant middleware and notification system.

---

### Task 1: App scaffold and settings

**Files:**
- Create: `ai_agents/`
- Modify: `core/settings.py`
- Modify: `core/urls.py`

- [x] Run `docker compose exec app python manage.py startapp ai_agents`.
- [x] Remove `ai_agents/tests.py`.
- [x] Register `'ai_agents'` after `'renewals'`.
- [x] Add `OPENAI_API_KEY` and `OPENAI_MODEL`.
- [x] Include `path('ai/', include('ai_agents.urls'))`.

### Task 2: Tools, prompts, agent, service

**Files:**
- Create: `ai_agents/tools.py`
- Create: `ai_agents/prompts.py`
- Create: `ai_agents/agent.py`
- Create: `ai_agents/services.py`

- [x] Implement tenant-scoped tools for each entity type.
- [x] Add Portuguese Markdown prompts.
- [x] Build LangGraph ReAct agent with ChatOpenAI timeout.
- [x] Implement summary persistence and notification creation.
- [x] Ensure error path sets `ai_summary_status='error'` and short message.

### Task 3: Celery task and HTTP endpoints

**Files:**
- Create: `ai_agents/tasks.py`
- Create: `ai_agents/views.py`
- Create: `ai_agents/urls.py`

- [x] Add `ai_agents.summarize` Celery task.
- [x] Add POST trigger endpoint with tenant/entity/role validation.
- [x] Add GET status endpoint with tenant/entity validation.
- [x] Return JSON only.

### Task 4: Verification, PRD, commits

**Files:**
- Modify: `PRD.md`

- [x] Run `makemigrations ai_agents`, `migrate`, `check`, worker restart.
- [x] Run one real OpenAI summary validation attempt.
- [x] Verify cross-tenant 404 and operational 403.
- [x] Mark Sprint 21 tasks complete.
- [x] Commit atomically without pushing.

**Validation note:** the OpenAI call reached the worker and failed with HTTP 401 because
`OPENAI_API_KEY` is not configured in the container environment. The task persisted
`ai_summary_status='error'` as expected.
