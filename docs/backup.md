# Backup

Backup cobre banco PostgreSQL, mídia protegida e segredos operacionais. A meta é
ter restauração testada, retenção definida e cópias fora da VPS. Backup sem teste
de restore é apenas esperança otimista com gzip.

## Escopo

| Item | Estratégia |
|---|---|
| PostgreSQL | `pg_dump` diário compactado. |
| Mídia | Cópia do volume `media_data`. |
| Segredos | Cópia em cofre seguro. |
| Offsite | Object storage com versionamento. |
| Restore | Procedimento testado periodicamente. |

## Dump do banco

```bash
DB=$(docker ps --filter name=brokerly_db -q | head -n1)
docker exec "$DB" pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" \
  | gzip > "/backups/brokerly_$(date +%F).sql.gz"
```

## Retenção sugerida

| Tipo | Quantidade |
|---|---:|
| Diários | 7 |
| Semanais | 4 |
| Mensais | 12 |

## Backup de mídia

Use `tar`, `rsync` ou snapshot de volume. O importante é preservar caminhos,
permissões e consistência com os registros do banco.

```bash
tar -czf /backups/brokerly_media_$(date +%F).tar.gz /var/lib/docker/volumes/...
```

## Offsite

Envie banco e mídia para S3, Backblaze, MinIO ou outro storage com versionamento.
Proteja o bucket contra deleção acidental e use credenciais específicas para
backup.

## Restore do banco

```bash
DB=$(docker ps --filter name=brokerly_db -q | head -n1)
gunzip -c /backups/brokerly_2026-05-28.sql.gz \
  | docker exec -i "$DB" psql -U "$POSTGRES_USER" "$POSTGRES_DB"
```

!!! warning "Restore destrutivo"
    Restaurar sobre uma base existente pode sobrescrever dados. Faça snapshot ou
    restore em ambiente isolado antes de operar em produção.

## Restore de mídia

1. Parar serviços que escrevem mídia.
2. Restaurar volume ou diretório.
3. Conferir dono/permissões.
4. Subir app.
5. Testar download protegido de anexos.

## Teste periódico

| Frequência | Verificação |
|---|---|
| Semanal | Dump existe, tamanho plausível e upload offsite ok. |
| Mensal | Restore em ambiente separado. |
| Trimestral | Simulação de perda total. |

## Segredos

Guarde `.env` de produção e Docker Secrets em cofre. Sem eles, restaurar banco e
mídia pode não bastar para voltar o serviço.

## Checklist

- [ ] Dump diário configurado.
- [ ] Retenção aplicada.
- [ ] Cópia offsite testada.
- [ ] Restore documentado.
- [ ] Mídia protegida incluída.
- [ ] Segredos salvos fora da VPS.
- [ ] Teste de restore registrado.
