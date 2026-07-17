# Backup

Backup cobre banco PostgreSQL, mídia protegida e segredos operacionais. A meta é
ter restauração testada, retenção definida e cópias fora da VPS. Backup sem teste
de restore é apenas esperança otimista com gzip.

## Escopo

| Item | Estratégia |
|---|---|
| PostgreSQL | Dump em formato custom do `pg_dump`. |
| Mídia | Snapshot compactado do diretório `MEDIA_ROOT`. |
| Segredos | Cópia manual em cofre seguro. |
| Offsite | Object storage com versionamento. |
| Restore | Procedimento destrutivo, confirmado com `--yes`. |

## Scripts versionados

Os scripts ficam em `scripts/`:

- `scripts/backup.sh`
- `scripts/restore.sh`

Eles usam apenas variáveis de ambiente e não imprimem credenciais no output. O
mesmo script roda localmente, em container ou na VPS, desde que `pg_dump`,
`pg_restore` e `tar` estejam disponíveis.

## Variáveis esperadas

| Variável | Obrigatória | Exemplo |
|---|---|---|
| `POSTGRES_USER` | Sim | `brokerly` |
| `POSTGRES_PASSWORD` | Sim | `change-me` |
| `POSTGRES_HOST` | Sim | `db` |
| `POSTGRES_DB` | Sim | `brokerly` |
| `POSTGRES_PORT` | Não | `5432` |
| `BACKUP_DIR` | Não | `/var/backups/brokerly` |
| `MEDIA_ROOT` | Não | `/app/media` |

`BACKUP_DIR` e `MEDIA_ROOT` têm defaults seguros para produção em container:

- `BACKUP_DIR=/var/backups/brokerly`
- `MEDIA_ROOT=/app/media`

## Rodar backup

```bash
POSTGRES_USER=brokerly \
POSTGRES_PASSWORD=change-me \
POSTGRES_HOST=db \
POSTGRES_DB=brokerly \
BACKUP_DIR=/var/backups/brokerly \
MEDIA_ROOT=/app/media \
bash scripts/backup.sh
```

Saídas esperadas:

- `db_YYYYMMDD_HHMMSS.dump`
- `media_YYYYMMDD_HHMMSS.tar.gz`

O dump usa:

```bash
pg_dump --no-owner --no-privileges --format=custom
```

Esse formato preserva flexibilidade para restore com `pg_restore`, sem amarrar o
arquivo ao owner original do banco.

## Rodar restore

Restore é destrutivo por definição. O script exige `--yes` como terceiro
argumento para reduzir acidente operacional.

```bash
POSTGRES_USER=brokerly \
POSTGRES_PASSWORD=change-me \
POSTGRES_HOST=db \
POSTGRES_DB=brokerly \
MEDIA_ROOT=/app/media \
bash scripts/restore.sh \
  /var/backups/brokerly/db_20260717_030000.dump \
  /var/backups/brokerly/media_20260717_030000.tar.gz \
  --yes
```

Para restaurar apenas o banco, omita o tar de mídia, mas mantenha `--yes` como o
segundo argumento real do comando:

```bash
bash scripts/restore.sh /var/backups/brokerly/db_20260717_030000.dump '' --yes
```

## Aviso de restore

!!! warning "Operação destrutiva"
    `restore.sh` executa `pg_restore --clean --if-exists`, removendo objetos do
    schema antes de recriá-los. Faça snapshot do estado atual ou restaure em
    ambiente isolado quando a intenção for apenas investigar dados antigos.

## Agendamento sugerido

Não há cron configurado pelo projeto nesta sprint. Quando a produção estiver
pronta, a sugestão operacional é rodar diariamente às 03h:

```cron
0 3 * * * cd /app && BACKUP_DIR=/var/backups/brokerly bash scripts/backup.sh
```

Em Docker Swarm, prefira executar em um nó com acesso ao banco, às variáveis de
ambiente e ao volume de mídia. Se os segredos estiverem em Docker Secrets, monte
ou exporte os valores antes da chamada.

## Retenção sugerida

| Tipo | Quantidade |
|---|---:|
| Diários | 7 |
| Semanais | 4 |
| Mensais | 12 |

Remova backups antigos somente depois de confirmar que a cópia offsite foi
concluída.

## Offsite

Envie banco e mídia para S3, Backblaze, MinIO ou outro storage com versionamento.
Proteja o bucket contra deleção acidental e use credenciais específicas para
backup.

## Procedimento de restore validado

1. Baixar dump e tar de mídia do storage offsite.
2. Conferir checksum e tamanho dos arquivos.
3. Parar serviços que escrevem no banco e em `MEDIA_ROOT`.
4. Executar `scripts/restore.sh` com `--yes`.
5. Subir app e workers.
6. Rodar `python manage.py check`.
7. Testar login, dashboard e download protegido de anexos.
8. Registrar data, operador, origem do backup e resultado.

## Segredos

Guarde `.env` de produção e Docker Secrets em cofre. Sem eles, restaurar banco e
mídia pode não bastar para voltar o serviço.

## Checklist

- [x] Script de dump PostgreSQL criado.
- [x] Script de snapshot de mídia criado.
- [x] Script de restore com confirmação destrutiva criado.
- [x] Invocações documentadas.
- [x] Cron sugerido documentado.
- [ ] Cron real configurado em produção.
- [ ] Cópia offsite configurada em produção.
- [ ] Teste de restore registrado em ambiente isolado.
