# Permissões

As permissões do Brokerly combinam autenticação por usuário, vínculo com
corretora e role operacional. O objetivo é restringir ações críticas sem quebrar
o fluxo diário de corretores, produtores, gerentes e back-office.

## Roles

| Role | Perfil | Acesso típico |
|---|---|---|
| `owner` | Administrador da corretora | Gestão completa do tenant. |
| `manager` | Gerente | Equipe, CRM, relatórios e operação comercial. |
| `broker` | Corretor | Clientes, propostas, apólices, sinistros e negociações. |
| `agent` | Agente | Operação de produção vinculada e acompanhamento. |
| `producer` | Produtor | Negociações e propostas próprias. |
| `operational` | Back-office | Anexos, endossos e suporte operacional. |

## Regras gerais

1. Rotas internas exigem autenticação.
2. Usuários autenticados precisam estar vinculados a uma corretora.
3. A role define ações permitidas.
4. O tenant define o conjunto de dados visível.
5. Dados sensíveis de produtividade são restritos a `owner` e `manager`.

## Mixins

`RoleRequiredMixin` centraliza autenticação, vínculo com corretora e checagem de
roles em CBVs. Para listas e detalhes, `TenantQuerysetMixin` restringe o
queryset.

```python
class ClientUpdateView(RoleRequiredMixin, UpdateView):
    allowed_roles = ('owner', 'manager', 'broker', 'agent')
```

## Tabela resumida

| Área | owner | manager | broker | agent | producer | operational |
|---|---|---|---|---|---|---|
| Dashboard | Sim | Sim | Sim | Sim | Sim | Sim |
| Clientes | Sim | Sim | Sim | Sim | Parcial | Parcial |
| Apólices | Sim | Sim | Sim | Sim | Parcial | Parcial |
| CRM | Sim | Sim | Sim | Sim | Sim | Não |
| Comissões | Sim | Sim | Visualização restrita | Restrito | Restrito | Não |
| Relatórios | Sim | Sim | Sim | Não | Não | Não |
| Produtividade | Sim | Sim | Não | Não | Não | Não |
| Usuários | Sim | Sim | Não | Não | Não | Não |

!!! warning "Permissão não substitui tenant"
    Mesmo quando a role permite uma ação, a query ainda precisa filtrar por
    `request.tenant`.

## Autenticação

O usuário customizado usa e-mail como identificador. Fluxos de login, registro e
reset de senha são públicos; o restante do app é privado.

## Onboarding

Depois do cadastro, o usuário cria ou vincula sua corretora, recebe uma
assinatura Free e passa a ter `brokerage`. Sem corretora, rotas privadas devem
retornar bloqueio.

## Relatórios

Relatórios CSV/PDF são acessíveis a `owner`, `manager` e `broker`, exceto o
relatório de produtividade, que é sensível e fica apenas para `owner` e
`manager`.

## IA

Resumos por IA podem ser disparados por perfis operacionais definidos nas views.
O chat é por usuário e sessão; histórico de outro usuário ou tenant retorna 404.

## Mídia

Downloads de anexos validam usuário autenticado, tenant do documento e tenant do
objeto pai. Se qualquer validação falhar, a resposta não revela existência do
arquivo.

## Checklist de revisão

- [ ] A view usa `LoginRequiredMixin` ou equivalente?
- [ ] Há `allowed_roles` quando a ação muda estado?
- [ ] Queryset é filtrado por tenant?
- [ ] Erros cross-tenant retornam 404 quando expor existência seria risco?
- [ ] Relatórios sensíveis bloqueiam producer, agent e operational?
