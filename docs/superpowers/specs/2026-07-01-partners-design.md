# Partners Design

## Scope

Implement Sprint 16 as defined by PRD sections 14.14, 14.15, 29, and 53. The
`partners` Django app will manage the brokerage commercial hierarchy through
tenant-scoped `Agent` and `Producer` records. Commission calculation, HTML
templates, sidebar changes, attachments, and invitations are excluded.

## Data Model

Both models inherit `TenantAwareModel` and enforce document uniqueness within
each brokerage. `Agent` represents a person or company and can optionally link
to a platform user. `Producer` has the same entity variants and optional user
link, plus an optional protected foreign key to `Agent`; a null agent represents
a producer linked directly to the brokerage. Both models store a default
commission rate without calculating commissions.

## Forms and Validation

Model forms receive the brokerage from the server. User and agent choice
querysets are restricted to that brokerage, with only active agents available
to producers. Documents are normalized to digits, validated as CPF or CNPJ with
`validate-docbr`, masked for storage, and checked for tenant-local uniqueness.
Producer validation also rejects an agent from another brokerage as defense in
depth. Search forms expose query, entity type, status, and, for producers, a
tenant-filtered agent selector.

## Views and URLs

Eight class-based views provide list, create, update, and detail operations for
agents and producers. Every view uses `TenantQuerysetMixin`. List and detail are
available to authenticated brokerage users; create and update require the
`owner` or `manager` role. Forms receive `request.tenant`, and create views set
the model brokerage from the request rather than accepting it as input.

The routes use the `/agentes/` and `/produtores/` prefixes prescribed in the
sprint request. Views reference the future templates but do not create or alter
HTML or static assets in this sprint.

## Administration and Integration

Both models are registered in Django Admin with the requested displays,
filters, search fields, and ordering. The app is registered after `claims` and
its URLs are included at the root URL configuration. A new initial migration
creates both models and their indexes and constraints.

## Verification

Automated tests are prohibited by the project contract. Verification uses
`makemigrations`, `migrate`, `check`, and the supplied Django shell scenarios.
The shell covers valid and invalid documents, tenant-local duplication,
producers with and without agents, cross-tenant rejection, tenant-scoped detail
access, missing-template responses, and role gates. If a sample CPF is rejected
by the installed validator, a mathematically valid alternative will be used and
reported.

## Delivery

After verification, all Sprint 16 checklist entries in PRD section 53 are marked
complete. Changes are committed atomically without pushing.
