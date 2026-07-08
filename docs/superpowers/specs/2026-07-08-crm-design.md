# CRM Sprint 18 Design

## Context

Sprint 18 starts Phase 4 and implements PRD §14.18, §30, and §53 Sprint 18:
tenant-aware CRM pipelines, stages, deals, deal stage history, grid and Kanban
server-side views, and an AJAX endpoint for moving cards between stages.

The user-provided sprint brief is treated as the approved design. No templates,
static files, sidebar changes, JavaScript, or new dependencies are in scope.

## Architecture

The `crm` Django app owns four tenant-aware domain models:

- `Pipeline`: brokerage-scoped sales pipelines.
- `Stage`: ordered pipeline stages with color and won/lost flags.
- `Deal`: commercial opportunity linked to producer and optionally to client,
  agent, line of business, insurer, and proposal.
- `DealStageHistory`: immutable transition log for stage moves.

Business behavior lives in `crm/services.py`:

- `seed_default_pipeline(brokerage)` creates the default `Negociações` pipeline
  and six default stages idempotently.
- `move_deal_to_stage()` validates tenant and pipeline, creates history, moves
  the deal, and synchronizes `status` to `open`, `won`, or `lost`.

`post_save(Brokerage)` seeds new brokerages, and a backfill command guarantees
the default pipeline for existing brokerages.

## Views and Forms

Pipelines have owner/manager CRUD with inline stage formsets. Deals have
brokerage-scoped grid CRUD, a server-rendered Kanban context, and a JSON move
endpoint using standard Django session/CSRF behavior.

All foreign-key form fields are filtered by `request.tenant`. Model-level
validation prevents cross-tenant FK assignment even outside forms.

## Acceptance

Completion requires migrations, backfill, `manage.py check`, the provided shell
scenario, Sprint 18 PRD checkboxes marked as complete, and atomic commits. HTML
templates are intentionally absent, so template-backed views are expected to
return HTTP 500 until Claude adds the templates.
