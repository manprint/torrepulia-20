> Nota del 20/10/2026: questo documento descrive il collaudo storico.
> La politica di esaurimento del catalogo è stata aggiornata: ora rispetta
> «Vendi quando esaurito», mantenendo il preorder stagionale separato.
> Consultare [il report aggiornato](../../docs/qa-20261020-stock/REPORT.md).

# Consegna servizio condiviso — 18 ottobre 2026

Addon `website_torrepulia_request`, versione **20.0.1.1.0**.
Protocollo HTTP con CSRF, servizio frontend unico e binding riutilizzabile per
catalogo, prodotto, stagionale, header e riepilogo. Specifica e aggiornamento in
[SELECTION.md](SELECTION.md); i layout del tema non vengono riscritti da questa issue.

## Implementazione

- Lettura, incremento, impostazione totale per riga/configurazione, rimozione e clear esplicito.
- Chiave canonica di variante/UoM/PTAV/testi personalizzati; origini editoriali escluse.
- Revisione e identità della selezione, registro di idempotenza, lock e retry nativi Odoo.
- Stato autorevole condiviso, letture iniziali coalescenti, notifiche fra tab,
  rilettura a pageshow/focus/visibilità e gestione di risposte superate.
- Operazione di rete incerta conservata nel tab per verificarla senza duplicarla.
- Quantità e limiti per website, validazione nativa di configurazione/catalogo/UoM.
- Prodotti diventati inaccessibili conservati con avviso e rimozione esplicita.
- Nessuna scrittura personale negli attributi dello snippet; cleanup dei valori runtime.
- Migrazione delle identità legacy prima dei vincoli NOT NULL/UNIQUE.

## File rispetto alla consegna base

Modificati:

- `__init__.py`, `__manifest__.py`;
- `models/__init__.py`, `models/website.py`, `models/request.py`;
- `security/ir.access.csv`;
- `views/settings.xml`;
- `tests/__init__.py`, `tests/test_request.py` (fixture comuni riusate);
- `README.md`, `QA.md` (quest’ultimo contrassegnato come report storico).

Aggiunti:

- `controllers/__init__.py`, `controllers/selection.py`;
- `models/selection.py`;
- `static/src/js/request_store.js`, `static/src/js/request_service.js`, `static/src/js/request_binding.js`;
- `migrations/20.0.1.1.0/pre-selection.py`;
- `tests/test_selection.py`, `tests/test_selection_http.py`, `tests/test_request_store.mjs`;
- `tools/concurrency_qa.py`;
- `SELECTION.md`, `QA-selection.md`, `selection-test-results.txt`.

Nessun file core, del tema, di configurazione HTTPS/dominio/indicizzazione o del
Builder modificato. Il modulo è ancora non versionato nell’indice Git come nella
consegna precedente; non sono stati creati commit o deploy.

## Verifiche effettive

Ambiente locale: **Odoo 20.0-20260926**, PostgreSQL 17, Node 18.19.1.
Database dedicato `torrepulia_request_test`; `odoo_dev` non aggiornato.
CRM/Vendite/eCommerce verificati nel container e sui moduli installati.
API lette anche in `http/dispatcher.py`, `http/session.py`, `http/retrying.py`,
`uom/models/uom_uom.py` e Interaction/service frontend nativi Odoo 20.

- **25 test Odoo: zero fallimenti/errori**, inclusi i 13 casi della base.
- **9 test JavaScript: zero fallimenti/errori**, eseguiti con Node sullo store reale
  e sul binding importato con shim del framework.
- **3 scenari PostgreSQL realmente concorrenti superati** con cursor distinti:
  stesso incremento applicato una sola volta; modifiche distinte con un conflitto
  e riapplicazione esplicita; inizializzazione con una sola bozza/sessione.
- Suite Odoo eseguita sia senza sia con `stock`/`website_sale_stock`; verifica del
  prodotto stoccabile senza giacenza con vendita fuori stock disabilitata.
- Test HTTP reale: cookie di due visitatori, rifiuto CSRF, ritentativo duplicato,
  campi manipolati e login nativo con rotazione SID e selezione preservata.
- Test di migrazione: identità legacy corretta, identità valida e dati richiesta preservati.
- Compilazione Python, parsing dei tre XML e controllo whitespace Git completati.
- Asset JS/CSS generati da Odoo durante la suite senza errori di compilazione.

Il riepilogo Odoo può indicare anche i passaggi di setup nelle statistiche: il
numero dei casi applicativi si legge nella riga `odoo.tests.result`.
I messaggi SQL di serializzazione/unicità durante il test concorrente sono
collisioni provocate intenzionalmente e recuperate dal retry nativo.
Il controllo finale dello script conferma assenza di fixture `Concurrency QA …`.

## Aggiornamento e limiti di verifica

Installare il nuovo addon (`-i`) oppure aggiornare la base precedente (`-u`) in
sviluppo, con backup ordinario, poi riavviare Odoo. La migrazione inclusa aggiunge
solo identità tecniche individuali; nessuna migrazione di pagine o prezzi.
I comandi completi e il contratto dei consumer sono in [SELECTION.md](SELECTION.md).

Browser controllabile non disponibile (`cua.listBrowsers()` vuoto): niente
screenshot o verifica visiva/interattiva nel Website Builder. La non persistenza
dei valori personali è coperta dal test di lifecycle del binding con DOM simulato;
resta da verificare sul Builder reale quando saranno integrati i layout delle pagine.

Questa issue fornisce servizio e binding: non applica attributi/controlli ai layout
esistenti del tema, non sostituisce il vecchio form stagionale e non realizza il
modulo contatti finale o il generatore preventivi. Il passaggio visivo completo
fra le pagine esistenti resta quindi da verificare nelle rispettive issue UI;
la condivisione delle quantità è verificata su protocollo e consumer del servizio.

Nessun test di carico eseguito. Nessuna dipendenza mancante per il servizio.
La libreria opzionale `markdown2` è assente nel container: warning nativo non
pertinente alla selezione. Nessun messaggio reale, pagamento o deploy in produzione.
