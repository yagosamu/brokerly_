# Notifications and Celery Results Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add database-backed Celery results, persistent user notifications, polling endpoints, and async password reset email delivery.

**Architecture:** Keep Celery/RabbitMQ execution as-is while switching task results to `django-db`. Add a tenant-aware `notifications` app with JSON endpoints and a reusable email task. Wire Django's native password reset view to an async form that enqueues a serializable Celery task.

**Tech Stack:** Django 6, Celery, RabbitMQ, django-celery-beat, django-celery-results, PostgreSQL, existing Brokerly tenant middleware.

---

### Task 1: Dependencies and settings

**Files:**
- Modify: `requirements.txt`
- Modify: `core/settings.py`

- [ ] Add `django-celery-results==2.6.0`.
- [ ] Try `dj-celery-panel==0.4.0`; keep it only if it installs and passes `manage.py check` under Django 6.
- [ ] Register `django_celery_results`.
- [ ] Set Celery result backend default to `django-db`, with extended result metadata and cache backend.

### Task 2: Notifications app

**Files:**
- Create: `notifications/`
- Modify: `core/settings.py`
- Modify: `core/urls.py`

- [ ] Scaffold app via `manage.py startapp notifications`.
- [ ] Remove `notifications/tests.py`.
- [ ] Add the app to `INSTALLED_APPS`.
- [ ] Add notification URLs under `/notifications/`.

### Task 3: Notification model, admin, views, URLs

**Files:**
- Create: `notifications/models.py`
- Create: `notifications/views.py`
- Create: `notifications/urls.py`
- Create: `notifications/admin.py`

- [ ] Implement tenant-aware `Notification`.
- [ ] Implement unread polling JSON with count computed before slicing.
- [ ] Implement mark-one-read and mark-all-read endpoints scoped by user and tenant.
- [ ] Implement list view without adding templates.
- [ ] Register admin.

### Task 4: Async password reset email

**Files:**
- Create: `notifications/tasks.py`
- Modify: `accounts/forms.py`
- Modify: `accounts/urls.py`

- [ ] Implement serializable email Celery tasks.
- [ ] Add `AsyncPasswordResetForm`.
- [ ] Wire `PasswordResetView` to the async form.

### Task 5: Migrations, verification, PRD, commits

**Files:**
- Create: `notifications/migrations/0001_initial.py`
- Modify: `PRD.md`

- [ ] Run dependency install.
- [ ] Run migrations for `django_celery_results` and notifications.
- [ ] Restart Celery worker and beat.
- [ ] Run `manage.py check`, shell validation, worker log validation, and migration dry-run.
- [ ] Mark Sprint 19 complete and document any `dj-celery-panel` decision.
- [ ] Commit atomically without pushing.
