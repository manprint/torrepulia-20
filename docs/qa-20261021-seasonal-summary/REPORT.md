# Prenota il tuo olio: form e riepilogo unico — 21/10/2026

Installato su **localhost:8069**, database **torrepulia_cinematic_install**.
Addon richiesta **20.0.1.12.0**, campagna **20.0.1.4.0**.
[Moduli installati](modules.txt), [aggiornamento riuscito](upgrade.log).

## Risultato

La pagina segue la sequenza **Scelta formati → I tuoi recapiti + Riepilogo
Prenotazione**. Eliminati il blocco prodotti a sinistra con miniature, prezzo
unitario, quantità e Rimuovi, e il pulsante intermedio «Completa la tua
prenotazione». L'eliminazione avviene nel markup stagionale, non nascondendo il
vecchio carrello con il CSS.

Il modulo stagionale mantiene nome/email sulla prima riga, telefono/località
sulla seconda e note a tutta larghezza. Telefono e CAP o Città sono obbligatori
nel browser e sul percorso server stagionale. Il campo geografico resta libero
e confluisce nelle note CRM; non introduce controlli rigidi di indirizzo.

A destra, un unico box `#fcfbf9` contiene titolo Caslon, prodotti/configurazioni
con quantità e subtotali server, separatori, nota spedizioni, totale da pagare
oggi, privacy e invio. Non contiene altre miniature o controlli quantità.
Il layout è 60/40 su desktop e tablet, a colonna singola sotto 768 px.

La selezione rimane quella condivisa della richiesta, separata dal carrello
ecommerce: nessun `sale.order` viene creato durante la composizione. I pulsanti
nelle card impostano la quantità totale e aggiornano il riepilogo con i dati
della preview server, senza ricaricare la pagina. Nessun motore prezzi client.
Il riepilogo comprende anche prodotti e configurazioni esterni alla campagna.

La pagina estesa `/la-tua-richiesta` conserva quantità modificabili e rimozione;
telefono e località lì restano facoltativi. Il nuovo ingresso stagionale
`/torrepulia/campaign/submit` richiede quei due campi e delega allo stesso servizio
transazionale/idempotente per validazioni, captcha, snapshot, CRM e ricevuta.
Non invia o conferma ordini, pagamenti o fatture. Quando i prezzi sono nascosti,
non compaiono subtotali o zero monetario: «Nessun pagamento richiesto oggi».

## Matrice dei controlli effettivamente eseguiti

| Scenario | Esito | Evidenza / limite |
| --- | --- | --- |
| Un solo form stagionale | Superato | Browser: un solo `data-tp-review-form` |
| Rimozione del carrello testuale a sinistra | Superato | Assenti `data-review-lines`, miniature e controlli nel blocco recapiti |
| Rimozione CTA intermedia | Superato | Assenti `data-campaign-review` e testo precedente; test HTTP e browser |
| Layout desktop 60/40 | Superato | A 1440 px: 768 px + 512 px, rapporto 0,6; [screenshot](form-1440.png) |
| Tablet, mobile e assenza overflow | Superato | Browser 768, 390 e 360 px, [misure](checks.json) |
| Selezione vuota | Superato | [Pagina vuota](empty-1440.png), nessun modulo di invio attivo |
| Un prodotto | Superato | [Pagina con un prodotto](one-product-1440.png) |
| Più prodotti | Superato | [Desktop](page-1440.png), [mobile](page-390.png) |
| Card quantità 1 → 2 e secondo prodotto 1 | Superato | Riepilogo 2 righe, quantità complessiva 3, subtotali uguali alla preview |
| Aggiornamento senza reload | Superato | Zero navigazioni della pagina durante le modifiche |
| Conservazione recapiti digitati | Superato | Nome e altri campi mantenuti dopo gli aggiornamenti |
| Prodotti esterni alla campagna e configurazioni | Superato | Suite HTTP campagna e test JS: tutte le righe conservate nel riepilogo compatto |
| Prezzi nascosti | Superato | Test JS senza importi e suite HTTP prezzi; non attivato/disattivato sul database reale durante il browser QA |
| Telefono e CAP o Città obbligatori | Superato | HTML required, focus browser su telefono mancante; POST server 422 senza creazioni CRM |
| Invio stagionale valido e retry | Superato | Database isolato: una sola opportunità, nessun ordine, area nelle note CRM; SMTP intercettato |
| Errore invio con dati conservati | Superato | Browser con POST intercettato: focus email, recapiti e selezione mantenuti |
| Riepilogo esteso precedente | Superato | Suite TestRequestReview, inclusi campi facoltativi, privacy, retry e immutabilità |
| Migrazione idempotente e testi editoriali conservati | Superato | Test modello su architettura con vecchi pulsanti riconoscibili |
| Preview Builder senza selezione personale | Superato | Test HTTP esistente della campagna |
| Salvataggio interattivo Builder | Non rieseguito in questa correzione | Nessuna modifica al ciclo di pulizia; il modulo continua a essere caricato privatamente fuori dal contenuto salvato |
| Console JavaScript | Superato | Nessun errore nel browser QA |
| Email, destinatari e pagamenti reali | Non utilizzati | Invio browser intercettato; invio vero solo nel DB di test con indirizzo `.invalid` e SMTP mock |

**43/43 test JavaScript passati:** [node-tests.log](node-tests.log).
**14 scenari Odoo distinti passati:** esecuzione iniziale con 13 passaggi e
1 fallimento della fixture telefono, che usava un numero non valido per il
validatore nativo. La fixture ora usa il numero fittizio riservato
`+1 202-555-0123`; lo scenario completo è stato rieseguito e superato.
Log conservati: [suite iniziale](odoo-tests.log),
[invio stagionale corretto](seasonal-submit-tests.log).
Nessun controllo nativo del telefono è stato indebolito per far passare il test.

Scansione statica UI: [design-detect.json](design-detect.json).
Script browser riproducibile: [browser_qa.py](browser_qa.py).
La selezione anonima del collaudo è stata svuotata; nessun invio reale è arrivato
al server del database locale dal browser.

## File modificati

`custom/website_torrepulia_request/`:

- `__manifest__.py`
- `controllers/review.py`
- `views/review.xml`
- `static/src/js/review.js`
- `static/src/scss/review.scss`
- `tests/test_review.mjs`
- `README.md`

`custom/website_torrepulia_request_campaign/`:

- `__manifest__.py`
- `controllers/campaign.py`
- `views/snippet.xml`
- `static/src/js/campaign.js`
- `static/src/scss/campaign.scss` (rimozione dello stile del pulsante eliminato)
- `models/page.py`
- `tests/test_http.py`
- `tests/test_campaign.py`
- `README.md`

Documentazione: `docs/TORREPULIA_RICHIESTE_GUIDA.md` e questa cartella QA.

## Aggiornamento e migrazione

Backup preliminare del database fuori repository:
`../backups/torrepulia_before_seasonal_summary_20261021.dump`.
Nessuna nuova tabella o colonna. La migrazione dei contenuti già esistente
rimuove anche eventuali pulsanti salvati con `data-campaign-review`, mantenendo
hero, foto, testi compatibili e traduzioni. La stessa operazione ripetuta non
crea duplicati; i backup editoriali esistenti restano disponibili.

Con processo web fermo e solo in sviluppo/staging:

```sh
odoo -d torrepulia_cinematic_install \
  -u website_torrepulia_request,website_torrepulia_request_campaign \
  --stop-after-init --no-http --max-cron-threads=0
```

Riavviare Odoo e ricaricare la pagina per ottenere gli asset aggiornati. Nessuna
modifica al core, al tema originale, a prezzi, stock, dominio, HTTPS o direttive
di indicizzazione. Nessuna dipendenza mancante nell'ambiente locale e nessun
deploy in produzione.
