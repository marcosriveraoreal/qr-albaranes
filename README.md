# QR Albarán

Servicio en Docker que reconstruye el albarán en PDF al escanear su código QR.

```
QR → GET /api/albaran/pdf?n=<nº albarán>&s=<firma>
     1. Verifica la firma "s" (HMAC) → 403 si no es válida
     2. SELECT TOP 1 ... FROM receptions WHERE <nº albarán> = ?   (consulta parametrizada, solo lectura)
     3. Genera el PDF con la misma maquetación que el albarán original (logo, datos, pesadas y QR)
```

## Puesta en marcha

1. Rellenar `.env` (plantilla en `.env.example`): `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`.
   Usar un usuario de SQL Server **solo con permiso SELECT** sobre `receptions`.
2. Revisar los nombres de columna en `app/db.py` → diccionario `COLUMNS` (ver abajo).
3. Arrancar:

```bash
docker compose up -d --build
docker compose logs -f
```

4. Probar: `http://<host>:9094/api/albaran/pdf?n=2608743&s=<firma>`

## Columnas de la tabla `receptions`

Todo el mapeo está en `app/db.py` → `COLUMNS` (campo del albarán → columna real).
Para ver las columnas reales:

```sql
SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'receptions';
```

El peso neto se calcula como bruto − tara. Los datos de la empresa emisora (Atalaya Riotinto) son fijos
en `app/pdf.py` (`ISSUER_NAME`, `ISSUER_LINES`).

## Firma del QR (parámetro `s`)

Impide que alguien descargue otros albaranes cambiando el número en la URL.

`s = base64url_sin_relleno( HMAC-SHA256(QR_SIGNING_SECRET, número)[:16] )` → 22 caracteres.

- Si los QR ya impresos los genera **otro sistema**, `QR_SIGNING_SECRET` y el algoritmo deben ser
  los mismos que usa ese sistema; si no, todos devolverán 403.
- `QR_SIGNATURE_REQUIRED=false` desactiva la comprobación (solo para pruebas).

## Variables de entorno

| Variable | Descripción |
|---|---|
| `DB_HOST`, `DB_PORT`, `DB_NAME` | Servidor y base de datos SQL Server |
| `DB_USER`, `DB_PASSWORD` | Credenciales (usuario de solo lectura) |
| `DB_ENCRYPT`, `DB_TRUST_SERVER_CERTIFICATE` | TLS de la conexión (`yes`/`no`) |
| `OPENSSL_CONF` | `/app/openssl-legacy.cnf` solo si SQL Server no soporta TLS 1.2 (SQL Server 2012 sin parches) |
| `QR_BASE_URL` | URL que se imprime en el QR del PDF reconstruido |
| `QR_SIGNING_SECRET` | Secreto HMAC, mínimo 32 caracteres |
| `APP_PORT` | Puerto publicado en el host (por defecto 9094) |
| `DOCS_ENABLED` | `true` para habilitar Swagger en `/docs` |

## Respuestas

| Código | Motivo |
|---|---|
| 200 | PDF del albarán (`inline`, se abre en el navegador del móvil) |
| 403 | Firma del QR ausente o no válida |
| 404 | No existe el albarán |
| 422 | Parámetros con formato no válido (`n` solo dígitos, `s` 22 caracteres) |
| 503 | SQL Server no disponible |

`GET /health` → healthcheck del contenedor.

## Tests

```bash
pip install -r requirements-dev.txt
python -m pytest
```
