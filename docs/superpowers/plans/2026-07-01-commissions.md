# Commissions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver tenant-isolated commission generation, split management, workflows, and backfill for Brokerly Sprint 17.

**Architecture:** Add a root Django app whose service and signal create one commission per policy, while forms and tenant-filtered CBVs manage splits and statuses. Enforce beneficiary XOR in PostgreSQL and financial limits in the form layer.

**Tech Stack:** Python 3.13+, Django 6, PostgreSQL 16, Docker Compose

---

### Task 1: Scaffold and register commissions

**Files:** Create `commissions/`; modify `core/settings.py`.

- [ ] Run `docker compose exec app python manage.py startapp commissions`.
- [ ] Remove `commissions/tests.py` and register `'commissions'` after `'partners'`.

### Task 2: Add commission models

**Files:** Create `commissions/models.py`.

- [ ] Implement `Commission` with policy one-to-one, financial fields, workflow dates, indexes, and amount properties.
- [ ] Implement `CommissionSplit` with XOR beneficiary constraint, financial fields, and tenant relationship validation that preserves database constraint enforcement.

### Task 3: Add generation, signal, and backfill

**Files:** Create `commissions/services.py`, `commissions/signals.py`, management package and command; modify `commissions/apps.py`.

- [ ] Implement atomic idempotent commission generation and split amount calculation.
- [ ] Register a `Policy` post-save receiver that acts only on creation.
- [ ] Implement an idempotent `backfill_commissions` command.

### Task 4: Add forms

**Files:** Create `commissions/forms.py`.

- [ ] Implement status and search forms with date widgets.
- [ ] Implement tenant-filtered split form beneficiary validation, optional amount calculation, and accumulated-limit validation with update exclusion.

### Task 5: Add tenant-scoped views and routes

**Files:** Create `commissions/views.py`, `commissions/urls.py`; modify `core/urls.py`.

- [ ] Implement list/detail CBVs with tenant filters and future template names.
- [ ] Produce six conditional aggregate metrics in one query.
- [ ] Implement POST-only split creation/deletion and status update for owner/manager.
- [ ] Register the five prescribed routes under `/comissoes/`.

### Task 6: Register admin

**Files:** Create `commissions/admin.py`.

- [ ] Register both models with the prescribed displays, filters, searches, and ordering.

### Task 7: Migrate and backfill

**Files:** Create `commissions/migrations/0001_initial.py`.

- [ ] Generate and inspect the initial migration, including the XOR check constraint.
- [ ] Apply migrations and run the backfill twice to prove idempotency.
- [ ] Run `manage.py check` and migration consistency verification.

### Task 8: Verify behavior

**Files:** No persistent files.

- [ ] Run shell scenarios for signal calculation/idempotency, valid splits, overflow rejection, XOR database enforcement, tenant detail isolation, and role gates.
- [ ] Verify all five URLs resolve and expected missing templates return 500.
- [ ] Remove temporary records and restore any temporarily moved user.

### Task 9: Complete Sprint 17

**Files:** Modify `PRD.md`.

- [ ] Review acceptance criteria and mark all five Sprint 17 tasks complete.
- [ ] Run fresh migration, system, diff, and behavioral verification.
- [ ] Commit implementation and PRD updates atomically without pushing.
