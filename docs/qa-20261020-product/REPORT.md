# Shop, formati e scheda prodotto — 20/10/2026

Installazione locale su **localhost:8069**, database **torrepulia_cinematic_install**.
Moduli installati: `website_torrepulia_request` **20.0.1.10.1** e
`website_torrepulia_request_theme` **20.0.1.3.0**.
[Installazione](modules.txt), [aggiornamento riuscito](upgrade.log).
Il tema originale e il core Odoo non sono stati modificati.

## Interventi

1. **16 px** effettivi fra selettore quantità e pulsante, sia nello shop sia
   nello snippet. **20 px** prima di «Scegli le opzioni e scopri il prodotto».
2. Avviso rosso con larghezza adattata al contenuto e limite alla larghezza della
   card. Arrotondamento nativo uguale al dettaglio (`800 px` nel tema corrente).
   Testo e pulsante vanno a capo; contenuto allineato a sinistra.
3. Nello shop l'avviso esaurito è allineato in basso al pulsante delle altre card.
   Corretto il ritorno a capo del contenitore flex nativo che spostava le azioni
   lateralmente; titolo, quantità e azioni ora hanno lo stesso allineamento.
4. Ripristinati i nastri nello snippet richiesta, nell'anteprima fotografica e
   nella riga del formato. Usa `_get_ribbon()` nativo: `website_ribbon_id`, colori,
   assegnazioni automatiche e priorità. I badge editoriali restano separati.
5. **Gli altri formati** esclude il prodotto corrente sul server, sia in modalità
   richiesta sia in modalità shop. Lo snippet generico mantiene la selezione
   completa del gestore. Nessun ID viene rimosso dai dati salvati nel Builder.
6. Il titolo «La Regina», prima scritto direttamente nel template, diventa un
   campo per prodotto: **Titolo della scheda Torrepulia**. Il valore iniziale
   mantiene «La Regina»; se il campo viene svuotato, appare il nome prodotto.
7. Tre nuovi campi HTML traducibili, sanitizzati dai meccanismi nativi Odoo:
   **Il Profilo Sensoriale**, **Abbinamenti in Cucina**, **Spedizione e
   Conservazione**. Producono sezioni espandibili native `details/summary` sotto
   il prezzo. Le sezioni senza contenuto, anche HTML vuoto, non sono mostrate.

Configurazione in **Prodotti → prodotto → Torrepulia → Scheda prodotto sul sito**.
I testi forniti per profilo e abbinamenti sono esempi nei campi backend: non
sono stati applicati indistintamente ai prodotti reali. Le condizioni di
spedizione rimangono da compilare con informazioni approvate per il formato.
Nessuna modifica a prezzi, giacenze, flag di disponibilità o richieste raccolte.

## Matrice dei controlli eseguiti

| Scenario | Esito | Evidenza / limite |
| --- | --- | --- |
| Distanza quantità / aggiunta shop | Superato | 16 px a 1440 e 390 px, [misure](checks.json) |
| Distanza quantità / aggiunta snippet | Superato | 16 px; [desktop](formats-1440.png), [mobile](formats-390.png) |
| Distanza link ai dettagli | Superato | 20 px in entrambi i formati e viewport |
| Avviso compatto e round nativo | Superato | Desktop: 309 px su spazio disponibile 419/611 px; raggio uguale al dettaglio |
| Allineamento inferiore shop | Superato | Stesso bordo inferiore fra avviso e pulsante; [desktop](shop-1440.png), [mobile](shop-390.png) |
| Allineamento sinistro e contenimento nella card | Superato | Asserzioni browser sui rettangoli, nessuna uscita laterale |
| Nastri manuali e prezzi nascosti | Superato | Test HTTP: nastro in riga e anteprima, senza importi pubblici |
| Nastri configurati sul database locale | Superato | Browser: frammenti nativi presenti in riga e anteprima |
| Prodotto corrente escluso dagli altri formati | Superato | HTTP in modalità shop/richiesta e browser desktop/mobile |
| Titolo configurato e fallback al nome | Superato | Test HTTP con prodotto dedicato; il titolo reale resta «La Regina» |
| Tre sezioni con contenuti configurati | Superato | Test HTTP: titolo e contenuti resi correttamente; HTML vuoto escluso |
| Visualizzazione browser delle sezioni compilate | Non eseguita su prodotti reali | I nuovi contenuti reali sono lasciati vuoti; nessun testo commerciale inventato |
| Fallback shop, prezzi visibili/nascosti, stock | Superato | Test HTTP esistente del bridge, aggiornato con le nuove funzionalità |
| Errori JavaScript e overflow orizzontale | Superato | Nessun errore JS, nessun overflow nelle pagine controllate |
| Salvataggio interattivo Website Builder | Non rieseguito | Il ciclo nativo di caricamento generico rimane invariato, verificato dal test JS; nessuna pagina salvata è stata riscritta |
| 360 px e tablet | Non rieseguiti in questa correzione | Verifica browser attuale limitata a 390 e 1440 px |
| Invio CRM, email, pagamento e accettazione preventivi | Non rieseguiti | Non coinvolti da questa modifica; nessun invio reale o pagamento |

**42/42 test JavaScript passati:** [node-tests.log](node-tests.log).
**3/3 test Odoo HTTP passati**, su `torrepulia_request_test`:
[odoo-tests.log](odoo-tests.log). La suite comprende titolo/sezioni/esclusione,
nastri con prezzi nascosti e regressione del frammento formati.
Scansione statica UI senza rilievi: [design-detect.json](design-detect.json).
Script browser riproducibile: [browser_qa.py](browser_qa.py).

## File modificati e aggiunti

`custom/website_torrepulia_request/`:

- `__manifest__.py`
- `static/src/scss/commerce.scss`

`custom/website_torrepulia_request_theme/`:

- `__manifest__.py`
- `models/__init__.py`, nuovo `models/product.py`
- `controllers/commerce.py`
- `views/commerce.xml`, nuovo `views/product.xml`
- nuovi `static/src/js/formats.js`, `static/src/scss/product.scss`
- `tests/test_commerce.py`, nuovo `tests/test_formats.mjs`
- `README.md`

Documentazione: `docs/TORREPULIA_RICHIESTE_GUIDA.md` e questa cartella QA.

## Aggiornamento e migrazione

Backup preliminare fuori repository:
`../backups/torrepulia_before_product_20261020.dump`.
L'aggiornamento ORM aggiunge quattro colonne a `product.template`. Il titolo
riceve il valore predefinito «La Regina»; i tre campi editoriali restano vuoti.
Nessuna migrazione manuale, conversione di richieste o modifica alle pagine
Website Builder. Non aggiornare il tema originale per questo intervento.

Con processo web fermo, solo in ambiente sviluppo/staging:

```sh
odoo -d torrepulia_cinematic_install \
  -u website_torrepulia_request,website_torrepulia_request_theme \
  --stop-after-init --no-http --max-cron-threads=0
```

Riavviare Odoo e ricaricare la pagina per ricevere gli asset aggiornati.
Non sono state modificate configurazioni di dominio, HTTPS o indicizzazione.
Nessuna dipendenza mancante nell'ambiente locale. Nessun deploy in produzione.
