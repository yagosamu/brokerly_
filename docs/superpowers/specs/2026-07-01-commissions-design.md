# Commissions Design

## Scope

Implement Brokerly Sprint 17 according to PRD sections 14.16, 14.17, 29, and
53. The root-level `commissions` Django app will create one commission per
policy, manage agent and producer splits, expose tenant-isolated workflows, and
backfill existing policies. Templates, static assets, reports, notifications,
reversals, and automatic partner-rate suggestions are excluded.

## Domain Model

`Commission` belongs one-to-one to a policy and records the net premium,
insurer commission rate, calculated insurer amount, reference date, workflow
status, and receipt/payment dates. `CommissionSplit` belongs to a commission
and targets exactly one agent or producer. A database check constraint enforces
the beneficiary XOR rule.

Tenant relationships are validated on write so policies, commissions, agents,
and producers cannot cross brokerages. Database validation remains responsible
for the XOR constraint, preserving an `IntegrityError` for invalid direct
inserts.

## Generation and Backfill

`generate_commission_for_policy()` atomically returns an existing commission or
creates one from `Policy.net_premium * Policy.commission_rate`, rounded to two
decimal places. A `Policy` post-save signal invokes it only when `created=True`.
The `backfill_commissions` management command processes policies without a
commission, making repeated executions safe and idempotent.

## Forms and Business Validation

The status form edits status and workflow dates. The split form receives the
server-selected brokerage and commission, filters active beneficiaries by
tenant, enforces the beneficiary type, optionally calculates a zero amount from
a positive rate, and rejects a final accumulated split total greater than the
commission insurer amount. Updates exclude the current split from the existing
sum before validation.

## Views and Routes

Five class-based views provide list, detail, split creation/deletion, and status
updates. Every object lookup and mutation is tenant-scoped. All authenticated
brokerage roles can list and view; only owners and managers can mutate status or
splits. Mutation endpoints accept POST only.

The list supports policy/client search, status, and reference-date filters. One
conditional aggregate produces amount and count metrics for pending, received,
and paid commissions under these context names:

- `total_pending_amount` and `total_pending_count`
- `total_received_amount` and `total_received_count`
- `total_paid_amount` and `total_paid_count`

Views reference future commission templates but create no HTML.

## Verification and Delivery

Automated tests are prohibited by the project contract. Verification uses
Django migration checks, two backfill executions, system checks, and the
supplied shell scenarios for signal idempotency, calculations, split limits,
database XOR enforcement, tenant isolation, missing-template responses, and
role gates. Temporary validation records and any temporarily reassigned user
are restored afterward.

After verification, all Sprint 17 checklist entries in PRD section 53 are
marked complete. Changes are committed atomically without pushing.
