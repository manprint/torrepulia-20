# torrepulia-20: stack Odoo 20 + PostgreSQL 17

## Struttura

- `Dockerfile`: immagine `odoo:20.0` ufficiale + config + addon.
- `docker-compose.yml`: servizi `db` (postgres:17) e `odoo`.
- `config/odoo.conf`: config Odoo, montata in `/etc/odoo` (read-only); l'immagine ne contiene una copia di default.
- `contrib/` e `custom/`: addon Odoo, copiati in `/opt/odoo/extra-addons/`.
- `.env`: credenziali (non versionato). Partire da `.env.example`.

## Immagine pubblicata (GHCR)

La CI (`.github/workflows/docker-publish.yml`) builda, testa e pubblica l'immagine su GHCR
a ogni push su `main` e a ogni tag `v*`. I test installano i moduli dummy su PostgreSQL 17
e verificano l'healthcheck prima del push.

```bash
docker pull ghcr.io/manprint/torrepulia-20:latest
```

Tag pubblicati: `latest` (solo `main`), nome del branch, `sha-<commit>`, `vX.Y.Z` per i tag.

## Primo avvio

```bash
cp .env.example .env              # poi imposta POSTGRES_PASSWORD
mkdir -p odoo/postgres odoo/data  # directory dei dati su disco
docker compose build
docker compose up -d db

# Prima installazione: crea il DB odoo_dev (se manca) e installa i moduli
docker compose run --rm odoo -d odoo_dev -i base,dummy_contrib,dummy_custom --stop-after-init

docker compose up -d
```

Web: http://localhost:8069 (porta modificabile con `ODOO_PORT` in `.env`; pubblicata solo su 127.0.0.1).

## Dati su disco

- I dati stanno in `./odoo/postgres` (PostgreSQL) e `./odoo/data` (Odoo: filestore, sessioni).
- Docker li gestisce come named volume `db-data` e `odoo-data` (`docker volume ls`), con bind sulle directory sopra.
- `docker compose down -v` rimuove solo i riferimenti dei volumi, NON i file su disco.
  Per cancellare i dati elimina le directory a mano: sono di proprietà uid 999 (postgres) e 100 (odoo), serve root o un container.
- `odoo/` è in `.gitignore` e `.dockerignore`: i dati non finiscono nel repo né nell'immagine.

## Modifiche

- `config/odoo.conf` cambiato: `docker compose restart odoo`, nessun rebuild.
- Codice addon cambiato: rebuild, poi `docker compose up -d`.
  Gli addon vivono nell'immagine, non in un volume: senza rebuild le modifiche non arrivano.
- Aggiornare un modulo nel DB:
  `docker compose run --rm odoo -d odoo_dev -u <modulo> --stop-after-init`

## Note

- Master password (`admin_passwd`) non impostata nel config: il default di Odoo 20 è `admin`. Impostarla prima di esporre la porta su rete.
- `list_db` attivo: la login page mostra l'elenco DB. Per nasconderlo, decommentare in `config/odoo.conf`.
- PostgreSQL minimo per Odoo 20 è 16 (`MIN_PG_VERSION` nel sorgente).
