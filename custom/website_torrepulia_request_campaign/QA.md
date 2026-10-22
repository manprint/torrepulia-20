# Issue 4 — consegna pagina stagionale

## File aggiunti

Tutti sotto `custom/website_torrepulia_request_campaign`:

- `__init__.py`, `__manifest__.py`: registrazione e dipendenze/asset.
- `models/__init__.py`, `models/campaign.py`: campagne, righe con varianti native,
  ordine, date, editoriali, vincoli website/azienda e proiezione pubblica.
- `models/page.py`: migrazione idempotente con backup per lingua.
- `controllers/__init__.py`, `controllers/campaign.py`: contenuto pubblico e
  anteprima editor autenticata; blocco del vecchio invio CRM.
- `security/ir.access.csv`: accessi editor/commerciale e isolamento aziendale.
- `views/campaign.xml`: gestione nativa con picker prodotti e righe riordinabili.
- `views/snippet.xml`: snippet, contenuto dinamico e sostituzione nella palette.
- `data/page.xml`: aggiornamento circoscritto delle pagine stagionali.
- `static/src/js/campaign.js`: quantità impostate col servizio condiviso,
  conteggi separati, lettura autorevole, timer e protezione risposte obsolete.
- `static/src/js/campaign_options.js`, `static/src/xml/campaign_options.xml`:
  opzioni Builder, gestione prodotti, anteprima isolata e pulizia per salvataggio.
- `static/src/scss/campaign.scss`: palette/tipografia ereditate, griglia responsive
  e fotografie confezioni non ritagliate.
- `tests/__init__.py`, `tests/test_campaign.py`, `tests/test_http.py`,
  `tests/test_campaign.mjs`.
- `README.md`, `QA.md`, `test-results.txt`.

Aggiornato inoltre `custom/website_torrepulia_request/README.md` per documentare
la disponibilità dell'addon stagionale. Nessun file del tema originale o del core
è modificato. Gli addon delle issue precedenti erano già non tracciati nel workspace.

## Verifiche

Ambiente effettivo: Odoo 20.0-20260926 nel container, PostgreSQL 17. Verificati
moduli installati, sorgenti controller Website Form, prezzi prodotto e Website
Builder. Sicurezza Odoo 20 tramite `ir.access`, non ACL API di versioni precedenti.

Test Odoo: vincoli e ordinamento righe/varianti, campagna aperta/chiusa/intervallo,
accessi pubblico/portale/commerciale e azienda, isolamento website, migrazione e
seconda esecuzione, conservazione editoriale/fotografia/SEO, contenuto HTTP,
prezzo e prezzo/L nativi, visibilità prezzi, impostazione 2 → 3 senza duplicazione,
conservazione prodotti estranei, nessuna creazione CRM/ordini/contatti, vecchio form
respinto, editor autenticato senza quantità personali. Regressioni issue 1–3.

Test Node: sei verifiche aggiuntive su conteggi zero/uno/più, identità varianti/UoM/
custom, integrazione add/set col servizio condiviso, risposte campagne fuori ordine,
anteprima senza accesso alla selezione reale e pulizia del salvataggio duplicato.
Le dipendenze/DOM simulati non verificano il runtime completo del browser.

Il detector impeccable restituisce `[]`. Esiti numerici finali e comandi in
`test-results.txt`.
Esito finale: **41 test Odoo e 22 test JavaScript superati**, nessun errore.

## Controlli non eseguibili / dati da configurare

L'inventario CUA restituisce `apps: [], browsers: []`: screenshot desktop/mobile
con zero, uno e più prodotti e collaudo visivo dell'editor non eseguibili qui.
Non sono stati sostituiti con mockup o dichiarati superati.

Il catalogo locale non contiene attributi di filtrazione nativi. Il gestore deve
selezionare i prodotti reali, ordinarli e aprire la campagna dall'interfaccia.
Il default chiuso/vuoto evita di introdurre varianti o condizioni commerciali.
L'installazione non è stata applicata al sito `odoo_dev`: soltanto al database
isolato di test. Nessuna produzione coinvolta.
