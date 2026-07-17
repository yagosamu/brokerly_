# Auditoria de isolamento por tenant

Data: 2026-07-17

Esta auditoria revisa as views Django do Brokerly que retornam ou modificam
dados de domínio. O critério é simples: toda query sensível precisa estar
escopada por `brokerage=request.tenant`, diretamente ou via `TenantQuerysetMixin`.

## Resumo

| Resultado | Quantidade |
|---|---:|
| OK | 67 |
| FIXED | 3 |
| N/A | 13 |
| GAP restante | 0 |

Correção aplicada:

- `notifications.views.unread_json`, `mark_read` e `mark_all_read` agora
  bloqueiam usuários sem tenant e filtram sempre por `brokerage=request.tenant`.
  FIXED em `8da5d49 fix: enforce tenant filter on notification views`.

## Checklist

- [x] Todos os arquivos `views.py` foram revisados.
- [x] Views de lista/detalhe usam `TenantQuerysetMixin` ou filtro explícito.
- [x] Views de criação atribuem `form.instance.brokerage = request.tenant`.
- [x] Views de ação usam `get_object_or_404(..., brokerage=request.tenant)`.
- [x] Downloads e uploads de anexos validam tenant do documento e do objeto pai.
- [x] Relatórios e IA recebem o tenant do servidor.
- [x] Não há linha `GAP` restante.

## Critérios de classificação

- `OK`: filtra por tenant via mixin, `get_queryset`, helper ou filtro explícito.
- `FIXED`: gap encontrado e corrigido nesta sprint.
- `N/A`: view pública, autenticação, shell estático, helper sem retorno direto de
  dados sensíveis ou tela sem queryset de domínio.

## Resultado por view

| View | Status | Justificativa |
|---|---|---|
| `accounts/views.py:RegisterView` | N/A | Cadastro inicial; não lista dados de domínio de corretoras existentes. |
| `accounts/views.py:EmailLoginView` | N/A | Login. |
| `accounts/views.py:ProfileView` | OK | Atualiza apenas `request.user`. |
| `accounts/views.py:MemberListView` | OK | `User.objects.filter(brokerage=request.tenant)`. |
| `accounts/views.py:MemberCreateView` | OK | Injeta `brokerage=request.tenant` no form. |
| `accounts/views.py:MemberUpdateView` | OK | `get_queryset()` filtra por `brokerage=request.tenant`. |
| `ai_agents/views.py:trigger_summary` | OK | `_tenant_or_forbidden()` + `_get_entity(entity_type, pk, tenant)`. |
| `ai_agents/views.py:summary_status` | OK | `_tenant_or_forbidden()` + `_get_entity(entity_type, pk, tenant)`. |
| `ai_agents/views.py:ChatPageView` | N/A | Renderiza shell do chat; não retorna dados de domínio. |
| `ai_agents/views.py:ChatSessionListCreateView` | OK | Lista/cria `ChatSession` com `brokerage=tenant` e `user=request.user`. |
| `ai_agents/views.py:ChatSessionMessagesView` | OK | Usa `_session_or_404()` com `brokerage=tenant`. |
| `ai_agents/views.py:ChatSessionRenameView` | OK | Usa `_session_or_404()` com `brokerage=tenant`. |
| `ai_agents/views.py:ChatSessionDeleteView` | OK | Usa `_session_or_404()` com `brokerage=tenant`. |
| `ai_agents/views.py:ChatMessageStreamView` | OK | Usa `_session_or_404()` e `build_chat_agent(session.brokerage)`. |
| `claims/views.py:ClaimListView` | OK | `TenantQuerysetMixin` filtra `Claim` por tenant. |
| `claims/views.py:ClaimCreateView` | OK | `TenantQuerysetMixin` + `form.instance.brokerage=request.tenant`. |
| `claims/views.py:ClaimUpdateView` | OK | `TenantQuerysetMixin` filtra o objeto editado. |
| `claims/views.py:ClaimDetailView` | OK | `TenantQuerysetMixin`; anexos filtrados por tenant. |
| `clients/views.py:ClientListView` | OK | Query explícita `Client.objects.filter(brokerage=request.tenant)`. |
| `clients/views.py:ClientCreateView` | OK | Injeta tenant no form e no objeto. |
| `clients/views.py:ClientUpdateView` | OK | `get_queryset()` filtra por tenant. |
| `clients/views.py:ClientDetailView` | OK | `get_queryset()` e anexos filtrados por tenant. |
| `commissions/views.py:CommissionListView` | OK | `TenantQuerysetMixin` filtra `Commission`. |
| `commissions/views.py:CommissionDetailView` | OK | `TenantQuerysetMixin`; splits vêm da comissão tenant-scoped. |
| `commissions/views.py:CommissionSplitCreateView` | OK | Busca comissão com `brokerage=request.tenant`. |
| `commissions/views.py:CommissionSplitDeleteView` | OK | Busca split com `brokerage` e `commission__brokerage`. |
| `commissions/views.py:CommissionStatusUpdateView` | OK | Busca comissão com `brokerage=request.tenant`. |
| `core/views.py:LandingView` | N/A | Landing pública e redirect de usuário autenticado. |
| `crm/views.py:PipelineListView` | OK | `TenantQuerysetMixin`. |
| `crm/views.py:PipelineFormSetMixin` | N/A | Mixin auxiliar; persistência feita nas views tenant-scoped. |
| `crm/views.py:PipelineCreateView` | OK | `TenantQuerysetMixin` + `form.instance.brokerage=request.tenant`. |
| `crm/views.py:PipelineUpdateView` | OK | `TenantQuerysetMixin` filtra o pipeline editado. |
| `crm/views.py:DealListView` | OK | `TenantQuerysetMixin` filtra `Deal`. |
| `crm/views.py:DealCreateView` | OK | Injeta tenant no negócio e histórico. |
| `crm/views.py:DealUpdateView` | OK | `TenantQuerysetMixin` filtra o objeto editado. |
| `crm/views.py:DealDetailView` | OK | `TenantQuerysetMixin`; histórico parte do deal tenant-scoped. |
| `crm/views.py:KanbanView` | OK | Filtra `Pipeline`, `Stage` e `Deal` por `brokerage=tenant`. |
| `crm/views.py:DealMoveStageView` | OK | Busca deal e target stage com `brokerage=request.tenant`. |
| `dashboard/views.py:DashboardView` | OK | Todos os serviços recebem `tenant`; sem tenant não carrega dados. |
| `documents/views.py:get_tenant_content_object` | OK | Valida `brokerage_id` do objeto pai ou o próprio `Brokerage`. |
| `documents/views.py:ProtectedDocumentDownloadView` | OK | Busca `Document` por `pk` e `brokerage=tenant` e valida objeto pai. |
| `documents/views.py:DocumentUploadView` | OK | Valida objeto pai por tenant e cria `Document` com tenant. |
| `documents/views.py:DocumentDeleteView` | OK | `get_queryset()` filtra `Document` por tenant. |
| `insurance/views.py:ProposalListView` | OK | Query explícita por `brokerage=request.tenant`. |
| `insurance/views.py:ProposalFormsetMixin` | N/A | Mixin auxiliar; itens recebem tenant no fluxo da view. |
| `insurance/views.py:ProposalCreateView` | OK | Define tenant na proposta e nos itens cobertos. |
| `insurance/views.py:ProposalUpdateView` | OK | `get_queryset()` filtra por tenant. |
| `insurance/views.py:ProposalDetailView` | OK | `get_queryset()` e anexos filtrados por tenant. |
| `insurance/views.py:PolicyListView` | OK | `TenantQuerysetMixin`. |
| `insurance/views.py:PolicyCreateView` | OK | Define tenant no objeto criado. |
| `insurance/views.py:PolicyUpdateView` | OK | `TenantQuerysetMixin`. |
| `insurance/views.py:PolicyDetailView` | OK | `TenantQuerysetMixin`; anexos filtrados por tenant. |
| `insurance/views.py:GeneratePolicyFromProposalView` | OK | Busca proposta com `brokerage=request.tenant`. |
| `insurance/views.py:EndorsementListView` | OK | `TenantQuerysetMixin`. |
| `insurance/views.py:EndorsementCreateView` | OK | Define tenant no objeto criado. |
| `insurance/views.py:EndorsementUpdateView` | OK | `TenantQuerysetMixin`. |
| `insurance/views.py:EndorsementDetailView` | OK | `TenantQuerysetMixin`; anexos filtrados por tenant. |
| `insurers/views.py:InsurerListView` | OK | Query explícita por `brokerage=request.tenant`. |
| `insurers/views.py:InsurerCreateView` | OK | Injeta tenant no form e no objeto. |
| `insurers/views.py:InsurerUpdateView` | OK | `get_queryset()` filtra por tenant. |
| `insurers/views.py:LineOfBusinessListView` | OK | Query explícita por `brokerage=request.tenant`. |
| `insurers/views.py:LineOfBusinessCreateView` | OK | Injeta tenant no form e no objeto. |
| `insurers/views.py:LineOfBusinessUpdateView` | OK | `get_queryset()` filtra por tenant. |
| `notifications/views.py:unread_json` | FIXED | Agora exige tenant e filtra por `brokerage=tenant`. |
| `notifications/views.py:mark_read` | FIXED | Agora exige tenant e filtra por `brokerage=tenant`. |
| `notifications/views.py:mark_all_read` | FIXED | Agora exige tenant e filtra por `brokerage=tenant`. |
| `notifications/views.py:NotificationListView` | OK | Filtra por `user=request.user` e `brokerage=request.tenant`. |
| `partners/views.py:AgentListView` | OK | `TenantQuerysetMixin`. |
| `partners/views.py:AgentCreateView` | OK | Define tenant no objeto criado. |
| `partners/views.py:AgentUpdateView` | OK | `TenantQuerysetMixin`. |
| `partners/views.py:AgentDetailView` | OK | `TenantQuerysetMixin`. |
| `partners/views.py:ProducerListView` | OK | `TenantQuerysetMixin`. |
| `partners/views.py:ProducerCreateView` | OK | Define tenant no objeto criado. |
| `partners/views.py:ProducerUpdateView` | OK | `TenantQuerysetMixin`. |
| `partners/views.py:ProducerDetailView` | OK | `TenantQuerysetMixin`. |
| `renewals/views.py:RenewalListView` | OK | `TenantQuerysetMixin`. |
| `renewals/views.py:RenewalDetailView` | OK | `TenantQuerysetMixin`. |
| `renewals/views.py:RenewalUpdateView` | OK | `TenantQuerysetMixin`. |
| `renewals/views.py:RenewPolicyActionView` | OK | Busca renovação com `brokerage=request.tenant`. |
| `reports/views.py:ReportPermissionMixin` | N/A | Mixin de permissão; não consulta domínio diretamente. |
| `reports/views.py:ReportMenuView` | N/A | Lista registro estático de relatórios. |
| `reports/views.py:ReportDetailView` | N/A | Exibe metadados estáticos e parâmetros. |
| `reports/views.py:ReportCsvView` | OK | Passa `tenant` para o gerador CSV. |
| `reports/views.py:ReportPdfRequestView` | OK | Cria `ReportJob` com `brokerage=tenant`. |
| `reports/views.py:ReportPdfStatusView` | OK | `_job_or_404()` filtra por tenant e usuário. |
| `reports/views.py:ReportPdfDownloadView` | OK | `_job_or_404()` filtra por tenant e usuário. |
| `tenants/views.py:BrokerageOnboardingView` | N/A | Criação inicial da corretora do próprio usuário. |
| `tenants/views.py:MyPlanView` | OK | Lê `request.tenant` diretamente. |

## Observações

- A auditoria não encontrou gaps críticos de vazamento entre corretoras.
- O gap corrigido em notificações era uma inconsistência de defesa em camadas:
  usuários normais continuavam restritos por `user=request.user`, mas a ausência
  de tenant não deve retornar nem alterar dados tenant-scoped.
- Relatórios e agentes de IA seguem o padrão do PRD: o tenant é resolvido no
  servidor e passado para serviços/tools; o usuário ou modelo nunca escolhe
  `brokerage_id`.
