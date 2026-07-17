# Mídia Protegida

Arquivos enviados ao Brokerly são dados sensíveis. Por isso, a aplicação não
expõe `/media/` publicamente: todo download passa por view autenticada, validação
de tenant e validação do objeto relacionado.

## Objetivo

Proteger documentos de clientes, propostas, apólices e sinistros contra acesso
direto por URL. O caminho físico do arquivo não é uma autorização.

## Modelo

`Document` guarda metadados e usa relação genérica para apontar para o objeto
pai.

| Campo | Função |
|---|---|
| `brokerage` | Tenant dono do arquivo. |
| `content_type` | Tipo do objeto pai. |
| `object_id` | ID do objeto pai. |
| `file` | Arquivo armazenado. |
| `uploaded_by` | Usuário que enviou. |
| `original_name` | Nome para download. |

## Upload

1. Usuário autenticado envia arquivo.
2. View valida role.
3. View resolve `content_type` e `object_id`.
4. Objeto pai é carregado e comparado ao `request.tenant`.
5. Documento é salvo com o tenant atual.

## Download

1. Usuário acessa `/anexos/<id>/baixar/`.
2. View busca `Document(pk=id, brokerage=request.tenant)`.
3. View resolve o objeto pai.
4. Se o pai não pertence ao mesmo tenant, retorna 404.
5. O arquivo é aberto e enviado como anexo.

!!! warning "Sem /media/ público"
    Mapear o diretório de mídia diretamente no proxy quebraria o isolamento por
    tenant. A autorização precisa acontecer no Django.

## X-Accel-Redirect

O PRD prevê uso de `X-Accel-Redirect` como padrão de produção para deixar o proxy
servir bytes depois que Django autoriza. A implementação atual pode usar
`FileResponse`; a regra de segurança é a mesma: autorização primeiro, arquivo
depois.

## Caminhos

O padrão de caminho recomendado é segregado por tenant:

```text
brokerage_<id>/<app>/<uuid>.<ext>
```

## Boas práticas

| Tema | Regra |
|---|---|
| MIME | Guardar o `content_type` do upload quando disponível. |
| Tamanho | Registrar `size_bytes` para auditoria e UI. |
| Nome | Preservar `original_name`, mas não confiar nele para path final. |
| Exclusão | Remover vínculo apenas com permissão apropriada. |
| Auditoria | Usar timestamps de `BaseModel`. |

## Erros

| Situação | Resposta |
|---|---|
| Documento não existe | 404 |
| Documento de outro tenant | 404 |
| Objeto pai de outro tenant | 404 |
| Usuário sem login | Redirect/login |
| Upload inválido | 400 ou form inválido |

## Checklist

- [ ] A view de download exige login?
- [ ] O documento é buscado por `brokerage=request.tenant`?
- [ ] O objeto pai é validado?
- [ ] `/media/` não está exposto publicamente?
- [ ] O proxy só serve arquivo após autorização?
