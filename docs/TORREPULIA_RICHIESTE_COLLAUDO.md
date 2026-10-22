# Collaudo trasversale Torrepulia — issue 9

**Aggiornamento successivo sulla 8069:** installazione e prove reali con Chromium
headless documentate in [qa-8069/REPORT.md](qa-8069/REPORT.md), inclusi screenshot
e correzioni del Website Builder. La matrice qui sotto rimane lo storico della
precedente sessione: i limiti del browser non descrivono il collaudo successivo.

Consegna: 19 ottobre 2026. Questa matrice distingue verifiche HTTP/ORM, JavaScript
simulato e controlli che richiedono un browser. **Un esito automatico non certifica
i clic del visitatore, l'accessibilità completa o la resa visiva.**

Esiti: **74 test Odoo superati**, ripetizione finale dei **12 test degli addon
modificati**, **29 test JavaScript**, **8 scenari concorrenti PostgreSQL**.
Migrazione e smoke HTTP superati sulla copia del database storico; parsing
Python/XML superato su **66 file**. I dettagli e i limiti sono riportati sotto.

## Ambiente e dati

Odoo effettivo **20.0-20260926**, PostgreSQL 17, codice nativo nel container
`/usr/lib/python3/dist-packages/odoo/`. Moduli funzionali dipendenti da
`website_sale`, `sale_crm`, tema Torrepulia e relativa integrazione. QA su
`torrepulia_request_test`, provider `payment_demo` non live, contatti `.invalid`,
SMTP intercettato, cron disabilitati nei processi di prova. Nessun pagamento reale.

Inventario browser attuale: `apps: [], browsers: []`. Non sono disponibili
screenshot, test a viewport reale o interazioni manuali con il Website Builder.

Lettura SQL **soltanto lettura** di `odoo_dev`: tema registrato alla versione
`20.0.3.1.2`, nuovi addon non installati; la pagina `/prenotailtuoolio` pubblicata
contiene ancora un form precedente e nessun selettore nuovo. La pagina
`/richiesta-inviata` è pubblicata con `website_indexed=False`. Il manifest del tema
nel repository è `20.0.3.6.0`; in QA è installata questa versione.

È stata anche ripristinata una copia PostgreSQL temporanea di `odoo_dev`,
`torrepulia_migration_test`, con cron/email disabilitati e provider non live.
Installazione, migrazione ripetuta e pagine/API pubbliche sono state verificate
su questa copia, mantenendo la versione registrata del tema `20.0.3.1.2`.
Il confronto di conteggi e fingerprint dei campi commerciali conferma invariati
CRM, ordini/righe, prezzi, stock, pagamenti e fatture. Il database originale non
è stato aggiornato. Il filestore originale non è stato copiato: questa prova
copre documenti HTML e API, non download e resa di immagini/asset.

La prima prova HTTP sulla copia ha rilevato colonne di navigazione del tema
assenti nel vecchio schema. Il bridge ora include il modello `website.menu`
nell'inizializzazione ORM, senza ridefinire campi o riprovisionare pagine del tema.
Dopo l'aggiornamento del bridge, shop, prodotto reale, pagina stagionale,
riepilogo e vecchia pagina di ringraziamento rispondono 200; due prodotti del
catalogo esistente sono selezionabili, con tre confezioni nel riepilogo e prezzi
nascosti. Il vecchio POST è rifiutato. I redirect linguistici nativi sono mantenuti.
Non dichiarare il sito locale/staging originale già migrato.

## Evidenze riproducibili

I file `T-*` sotto indicati sono relativi a `custom/website_torrepulia_request/`:

| Sigla | Evidenza |
| --- | --- |
| J | `custom/website_torrepulia_request_campaign/tests/test_journey.py` — percorso HTTP/ORM completo e ringraziamento |
| C | `custom/website_torrepulia_request_campaign/tests/test_campaign.py`, `tests/test_http.py` — campagne, varianti, permessi e migrazione |
| B | `custom/website_torrepulia_request_campaign/tests/test_campaign.mjs` — simulazione interazioni/cleaner Builder |
| T-S | `tests/test_selection.py`, `tests/test_selection_http.py`, `tests/test_request_store.mjs` |
| T-C | `tests/test_commerce.py`, `tests/test_commerce.mjs`, test del bridge tema |
| T-R | `tests/test_review.py`, `tests/test_review.mjs` |
| T-I | `tests/test_submission.py`, `tools/review_concurrency_qa.py` |
| T-Q | `tests/test_quotation.py`, `tests/test_quotation_portal.py`, `tests/test_quotation_accounting.py`, `tools/quotation_concurrency_qa.py` |
| T-X | `tests/test_checkout_policy.py` |
| M | `custom/website_torrepulia_request_campaign/tools/migration_qa.py`, `tools/migration_http_qa.py` — copia del DB storico, confronto dati e smoke HTTP |
| LOG | [Comandi ed esiti effettivi](../custom/website_torrepulia_request_campaign/journey-test-results.txt) |

## Matrice funzionale

| Scenario | Risultato | Evidenza | Limite o problema residuo |
| --- | --- | --- | --- |
| Catalogo: aggiungere lattina e Bag in Box e aprire riepilogo | Eseguito via HTTP: pagine shop/prodotto disponibili; prodotti e quantità esatti nel servizio e nel riepilogo server | J, T-C, T-S | Prodotti sintetici; clic e fotografie dell'assortimento reale non collaudati |
| Catalogo → stagionale → riepilogo, da 2 a 3 | Eseguito: `set_configuration` produce 3, non 5; totale condiviso coerente | J, C, B | Idratazione nel browser verificata solo con DOM/dipendenze simulati |
| Bottiglie fuori campagna | Eseguito: quattro confezioni restano presenti dopo la modifica della lattina; tre righe con quantità 3, 1, 4 | J, C | Nessuna attribuzione commerciale a prodotti reali |
| Varianti diverse simultanee | Eseguito: configurazioni native distinte, quantità e righe indipendenti | C, T-S, T-Q | Il catalogo reale va configurato dal gestore; nessuna variante artificiale installata |
| Invio valido senza account | Eseguito: una richiesta inviata, una opportunità, recapiti e righe corretti | J, T-R, T-I | CAPTCHA reale esterno non interrogato; usati i meccanismi/test nativi locali |
| Dati mancanti/non validi | Eseguito: 422, campi pertinenti, selezione mantenuta; nessun CRM creato | J, T-R | Focus e messaggi testati in codice/simulazione, non con lettore schermo |
| Errore CRM durante invio | Eseguito: errore intercettato nella fixture, rollback completo, otto confezioni conservate, nuovo tentativo valido | J, T-I | Errore indotto, non guasto infrastrutturale reale |
| Doppio clic/ritentativo dopo risposta persa | Eseguito: replay HTTP restituisce stesso riferimento; JavaScript riusa lo stesso tentativo dopo errore di trasporto | J, T-R, T-I, LOG | L'interruzione fisica della rete nel browser non è stata eseguita |
| Concorrenza invio/modifica e preparazione preventivo | Superati otto scenari PostgreSQL: replay, conflitti, inizializzazione, invio, notifiche e preventivi/revisioni | T-I, T-Q, LOG | Fixture sintetiche; non è un test di carico |
| Accesso alla richiesta di un altro visitatore | Eseguito: ricevuta 404 nonostante ID nella query; la vecchia pagina mostra testo neutro | J, T-R, T-S | Nessun accesso aggiuntivo concesso a pubblico/portale |
| Una opportunità, righe esatte, nessun ordine all'invio | Eseguito: conteggi e mappatura prodotti/quantità verificati prima e dopo invio | J, T-I | La coda notifiche è distinta dall'invio SMTP |
| Preparazione preventivo | Eseguito: bozza nativa, righe esatte; ripetizione apre lo stesso documento; fotografia originale immutata | J, T-Q | Il wizard non è stato percorso a mano nel browser |
| Accettazione manuale | Eseguito: nota sintetica nel chatter, conferma nativa; regressione contabile/stock nativa | J, T-Q | Nessuna vera email cliente usata |
| Accettazione online standard | Eseguito: firma HTTP nativa e pagamento Demo/post-processing, nessuna seconda approvazione | T-Q | PDF sostituito nella prova firma; nessun circuito reale e nessuna verifica grafica del PDF |
| Prezzi visibili/nascosti | Eseguito su proiezioni pubbliche, frammenti, markup economico, riepilogo e ricevuta; prezzi backend invariati | C, T-C, T-R, T-I | La presenza di vuoti grafici richiede ancora screenshot reali |
| Standard/richiesta, due website | Eseguito: site B standard opera mentre A blocca checkout; impostazioni e selezioni isolate | T-S, T-C, T-X | Non rappresenta un collaudo su domini staging pubblici |
| Campagna aperta, chiusa e intervalli | Eseguito: vetrina chiusa senza disabilitare catalogo o cancellare prodotti scelti | C | Scadenze e aggiornamento UI simulati, non una sessione browser continuativa |
| Ripristino standard | Eseguito: stesso carrello valido ripreso, nessuna fusione o perdita di richieste inviate | T-X | Le transazioni già avviate e le email già in coda richiedono gestione operativa nativa |

## Migrazione dei contenuti salvati

| Controllo | Risultato | Evidenza | Limite |
| --- | --- | --- | --- |
| Identificazione form precedente | Eseguito su codice e lettura del DB locale; vecchi campi di quantità individuati | `website_torrepulia_theme/views/snippets/s_forms.xml`, lettura `odoo_dev` sopra | Nessuna scrittura nel DB locale |
| Sostituzione con selettore stagionale | Eseguita nelle fixture e sulla copia del DB storico: un selettore, nessun vecchio form, pagine/API funzionanti | C, J, M, `models/page.py` dell'addon campagna | Applicazione al database originale locale/staging non eseguita |
| Form rinominati o con soli vecchi campi lattina/Bag in Box | Eseguito: tutti i marcatori riconosciuti; rimosso solo il form in sezioni sconosciute, conservati testo circostante e form contatti | C, test `test_renamed_legacy_forms_preserve_surrounding_editorial_and_contact_form` | Strutture senza marcatori stagionali riconoscibili richiedono controllo editoriale |
| Storico CRM | Eseguito: record/descrizione delle fixture e fingerprint dei campi storici sulla copia invariati | J, M; nessuna scrittura CRM nel migratore | Non migrati o convertiti gli storici |
| Vecchi POST non duplicano il flusso | Eseguito: marcatore e ciascuno dei quattro campi quantità rifiutati; contatti generali ancora validi | J, C | Le altre form CRM generiche rimangono intenzionalmente native |
| Ringraziamento aperto direttamente | Eseguito: testo neutro, nessun dato dalla query, `private/no-store` | J, nuova route `/richiesta-inviata` | Non è una ricevuta pubblica per ID |
| Ringraziamento dopo richiesta inviata | Eseguito: 303 alla ricevuta protetta della stessa sessione; altro visitatore senza ricevuta | J | Ricevuta soggetta alle protezioni/scadenze del flusso |
| Ringraziamento contatti e scadenza | Verificato dal test dedicato in LOG: riscontro generico entro 15 minuti, poi neutro; sito senza tema usa pagina nativa | J, LOG | Nessuna PII mostrata neppure nella conferma generica |
| URL, SEO, immagini, personalizzazioni compatibili | Eseguito su fixture e copia: URL, indicizzazione, pubblicazione, sezioni esterne e riferimenti foto preservati; backup delle architetture originali per lingua | C, M; nuova pagina mantiene scelta `noindex` della pagina precedente | Non è una revisione visiva/manuale di tutti gli editoriali e delle fotografie |
| Aggiornamento ripetuto | Eseguito: nessun nuovo selettore duplicato, nuovi testi conservati, backup originale mantenuto | C | Aggiornare i moduli dopo backup ordinario DB/filestore |

Il migratore dati è invocato da `data/page.xml` durante installazione/aggiornamento
dell'addon campagna. Agisce solo sui website Torrepulia abilitati e sulla pagina
stagionale del website; scrive `arch_db` tradotto, `arch_fs=False`,
`arch_updated=True` soltanto quando cambia il contenuto. Il backup tecnico
`website.torrepulia_campaign_page_backup` è riservato agli amministratori. Una
struttura `wrap` ambigua interrompe la transazione. Non cambia pubblicazione,
dominio, HTTPS o direttive di indicizzazione salvate.

La vecchia pagina di ringraziamento rimane nel database; il nuovo controller
evita di renderizzare la precedente conferma generica sui siti Torrepulia.
Il form contatti usa il risultato **già commesso** dal controller Odoo per
registrare in sessione soltanto il momento di ricezione, isolato per website.
Non sono introdotte letture CRM pubbliche o ricerche per email.

## Website Builder

| Controllo | Risultato | Evidenza | Limite |
| --- | --- | --- | --- |
| Scelta prodotti, cambio campagna, riordino | ORM/API eseguiti; campi e picker nativi presenti, ordine proiettato correttamente | C, viste `campaign.xml`, opzioni `campaign_options.xml` | Picker e trascinamento reali non eseguiti |
| Titolo, introduzione e foto modificabili | Struttura editor verificata da codice; migrazione ripetuta preserva testo modificato | C, snippet e opzioni | Modifica manuale e salvataggio UI non eseguiti |
| Anteprima zero/uno/più senza selezione personale | Eseguito via HTTP autenticato e simulazione JS; nessuna chiamata al servizio reale in edit | C, B | Il runtime completo del Builder non è stato avviato nel browser |
| Duplicazione, spostamento, salvataggio e ricarica | Cleaner eseguito ripetutamente su istanze simulate, senza ID generati o quantità/prezzi salvati | B | Duplicazione/salvataggio/ricaricamento tramite UI non eseguiti |

## Controlli visivi e accessibilità

| Controllo | Risultato | Evidenza | Limite/prossima prova |
| --- | --- | --- | --- |
| 360 px, zero/uno/più prodotti | **Non eseguito** | Browser assente | Screenshot stagionale e riepilogo, verifica overflow e controlli |
| 390 px, zero/uno/più prodotti | **Non eseguito** | Browser assente | Stesse prove, includendo menu mobile e tastiera a schermo |
| Tablet, 768 px | **Non eseguito** | Browser assente | Griglia, riepilogo, modulo e assenza sovrapposizioni |
| Desktop, 1440 px | **Non eseguito** | Browser assente | Due/tre colonne, immagini e header |
| Tastiera, ordine del focus, ritorno dopo rimozione/aggiornamento | **Non eseguito nel browser** | Focus ring e gestione focus nel codice; simulazioni JS parziali | Percorrere senza mouse catalogo, campagne, riepilogo, invio e portale |
| Nomi dei controlli quantità | Verifica statica: label include nome prodotto; riepilogo crea label associata per annidamento | `snippet.xml`, `review.js` | Verifica con albero accessibilità e lettore schermo non eseguita |
| Annunci, errori e invio in corso | Verifica statica/JS: `role=status/alert`, `aria-live`, `aria-invalid`, `aria-busy`, prevenzione doppio invio | B, T-R, template riepilogo | Annuncio effettivo e focus dopo errore da provare nel browser |
| Immagini confezioni | Verifica statica: `object-fit: contain`, dimensioni contenute, caricamento differito | SCSS campagna/riepilogo | Proporzioni e immagini reali non ispezionate in viewport |
| Contrasto, leggibilità, zoom 200%, assenza scroll orizzontale | **Non eseguito** | Breakpoint e `minmax(0,1fr)` presenti nel codice | Servono rendering e misurazioni reali |

Audit tecnico `impeccable`: detector meccanico sulla nuova vista di ringraziamento
restituisce `[]`. Non equivale a conformità WCAG. Le dimensioni accessibilità,
prestazioni, tema e responsive sono valutate solo a livello di codice: nessun
punteggio complessivo o promozione visuale è attribuito senza browser. Coerenza
implementativa: riuso del layout e dei token Torrepulia, nessuna nuova promessa
commerciale e nessuna immagine sintetica. Non sono state riscontrate dal detector
violazioni deterministiche nel nuovo template.

## Consegna e aggiornamento

[Guida operativa](TORREPULIA_RICHIESTE_GUIDA.md) per attivazione, prezzi, team,
campagne, snippet, CRM, preventivi, conferme e ripristino.

File della issue:

- `custom/website_torrepulia_request_campaign/__manifest__.py`: 20.0.1.1.0 e nuova vista.
- `custom/website_torrepulia_request_campaign/__init__.py` e
  `custom/website_torrepulia_request_theme/__init__.py`: test scoperti dal loader
  nativo senza importarli dal codice applicativo durante avvii ordinari.
- `custom/website_torrepulia_request_theme/__manifest__.py`, `README.md`, nuovi
  `models/__init__.py` e `models/menu.py`: bridge 20.0.1.1.0, inizializzazione
  circoscritta dello schema menu del tema storico tramite ORM.
- `custom/website_torrepulia_request_campaign/models/page.py`: riconoscimento dei
  vecchi campi e conservazione degli editoriali nelle sezioni rinominate.
- `custom/website_torrepulia_request_campaign/controllers/campaign.py`: gestione
  sicura della vecchia pagina di ringraziamento e riscontro del modulo contatti.
- Nuovo `custom/website_torrepulia_request_campaign/views/legacy_receipt.xml`.
- `custom/website_torrepulia_request_campaign/tests/__init__.py`,
  `tests/test_campaign.py`, nuovo `tests/test_journey.py`.
- `custom/website_torrepulia_request_campaign/README.md`, nuovo
  `journey-test-results.txt`; `custom/website_torrepulia_request/README.md`.
- Nuovi `custom/website_torrepulia_request_campaign/tools/migration_qa.py` e
  `tools/migration_http_qa.py`: verifiche limitate alla copia temporanea nominata.
- Nuovi `docs/TORREPULIA_RICHIESTE_GUIDA.md` e questo documento.

Con addon già installati aggiornare **bridge e campagna**, oppure tutti e tre gli
addon come indicato nella guida; se assenti installare
`website_torrepulia_request_campaign` con le sue dipendenze. Riavviare Odoo.
Nessun aggiornamento automatico del tema originale, nessun core modificato,
nessun intervento su prezzi/stock e nessun deploy in produzione.

Restano necessari prima di dichiarare il rilascio collaudato: verifica editoriale
dell'assortimento reale, controllo del filestore e controlli browser/Builder
riportati come non eseguiti. La copia migrata è stata eliminata a fine prova;
`odoo_dev` è rimasto invariato. Nessuna email inviata durante la prova della copia.
Nessun controllo mancante è sostituito da mockup o screenshot inventati.
