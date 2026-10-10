# syntax=docker/dockerfile:1

ARG ODOO_VERSION=20.0
FROM odoo:${ODOO_VERSION}

# Config esterna (config/odoo.conf). Root-owned, leggibile dal gruppo odoo:
# l'utente runtime non puo' modificarla.
COPY --chown=root:odoo --chmod=0640 config/odoo.conf /etc/odoo/odoo.conf

# Addon fuori dai path VOLUME dichiarati dalla base (/mnt/extra-addons, /var/lib/odoo):
# un volume anonimo stale non puo' oscurare il codice baked nell'immagine.
# Questi path devono combaciare con addons_path in config/odoo.conf.
COPY contrib/ /opt/odoo/extra-addons/contrib/
COPY custom/ /opt/odoo/extra-addons/custom/

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD ["curl", "-fsS", "-o", "/dev/null", "http://localhost:8069/web/health"]
