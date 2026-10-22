# Disponibilità del catalogo e avviso di esaurimento — 20/10/2026

Installato su **localhost:8069**, database **torrepulia_cinematic_install**.
Odoo **20.0-20260926**; addon `website_torrepulia_request` **20.0.1.10.0**,
bridge `website_torrepulia_request_theme` **20.0.1.2.2**. Verifica installazione:
[modules.txt](modules.txt). Aggiornamenti conclusi: [upgrade-final.log](upgrade-final.log).

## Comportamento consegnato

- Catalogo, dettaglio prodotto, formati del tema, formato promosso e pulsanti dei
  prodotti dinamici rispettano il flag nativo **Vendi quando esaurito**.
- Per prodotti con inventario tracciato, senza il flag e senza disponibilità,
  l'aggiunta dal catalogo viene nascosta e rifiutata anche dal servizio server.
- Il **Messaggio per esaurito** HTML configurato compare direttamente nella card,
  con gli stessi colori rossi del dettaglio (`text-bg-danger`: sfondo effettivo
  `rgb(252,235,236)` nel tema corrente). Testo e pulsante vanno a capo; il pulsante
  rimane visibile senza hover e dentro la card, anche alle larghezze ridotte.
- Le varianti mantengono disponibilità indipendente. Selezionando una variante
  esaurita, il regolatore e l'aggiunta scompaiono; torna il messaggio pertinente.
- La campagna **/prenotailtuoolio** mantiene il percorso di prenotazione del nuovo
  raccolto, senza disponibilità fisica e senza riserve di magazzino.
- Le richieste esistenti non vengono cancellate. Non cambia il comportamento
  nativo dello shop quando la modalità richiesta è disattivata.

La fonte della disponibilità è `_is_sold_out()` nativo di Odoo 20, che utilizza
il magazzino del website con `website_sale_stock` installato. Non sono stati
aggiunti nuovi campi di disponibilità né modificati core, tema originale, prezzi,
giacenze, flag prodotto, dominio, HTTPS o indicizzazione.
Il vecchio carrello non viene sottratto alla disponibilità della selezione
separata. La risposta a un retry già riuscito resta idempotente anche se in
seguito cambia la disponibilità. L'operazione catalogo `add` è distinta dalla
quantità totale `set_configuration` del preorder stagionale e dalle modifiche
nel riepilogo: non viene introdotto un blocco stock globale delle prenotazioni.

Il link alla campagna proviene dal messaggio configurato dal gestore: non viene
inventato o aggiunto automaticamente. Alla chiusura della campagna occorre
aggiornare i testi del prodotto se non più pertinenti.

## Matrice delle verifiche effettivamente eseguite

| Scenario | Risultato | Evidenza / limite |
| --- | --- | --- |
| Esaurito senza flag: card senza aggiunta, messaggio e link visibili | Superato | HTTP e browser; [shop desktop](shop-1440.png), [mobile](shop-390.png) |
| Messaggio rosso e pulsante contenuto nella card | Superato | Browser 360, 390, 768, 1440 px; [checks.json](checks.json) |
| Scheda prodotto esaurito: native hide non sovrascritto | Superato | [desktop](product-1440.png), [mobile](product-390.png), unit test JS |
| Scegli i formati: esaurito senza aggiunta, messaggio presente | Superato | HTTP e [desktop](formats-1440.png), [mobile](formats-390.png) |
| Formato promosso esaurito | Superato | HTTP bridge, messaggio presente e nessun comando di aggiunta |
| Flag attivo: aggiunta disponibile anche a stock zero | Superato | Test HTTP, senza cambiare i flag dei prodotti reali |
| Aggiunta diretta incompatibile a stock zero | Superato | HTTP 422, selezione invariata |
| Varianti reali con stock distinto | Superato | HTTP e test JS del cambio radio |
| Giacenza disponibile solo in altro magazzino | Superato | HTTP: il magazzino del website resta l'autorità |
| Catalogo → link configurato → campagna → quantità 1 | Superato | Browser, preorder accettato; [campagna](campaign-1440.png) |
| Altri prodotti, incremento/impostazione, retry, revisioni concorrenti | Superato | Suite TestSelection |
| Isolamento sessione, website e login | Superato | Suite TestSelection e TestCommerceHttp |
| Prezzi nascosti, risoluzione configurazioni, modalità standard | Superato | Suite TestCommerceHttp e bridge |
| Nessun ordine/CRM/contatto/email durante la selezione | Superato | TestSelection e controlli HTTP; nessun invio finale eseguito nel browser |
| Console JavaScript e scorrimento orizzontale | Superato | Nessun errore JS; nessun overflow nei controlli registrati |
| Contenuto Builder non scritto dalla selezione pubblica | Superato | Test HTTP esistente; nessuna pagina editoriale modificata |
| Apertura, modifica e salvataggio interattivo nel Website Builder | Non rieseguito | Questa correzione non cambia opzioni, struttura o ciclo di salvataggio degli snippet |
| Accettazione preventivi, email, pagamenti | Non rieseguito | Fuori dall'ambito della disponibilità; nessun destinatario o pagamento reale usato |

**Test JavaScript:** 40/40 passati, [node-tests.log](node-tests.log).
**Test Odoo:** 20 scenari distinti passati: 8/8 HTTP catalogo/bridge
[odoo-tests.log](odoo-tests.log), 11/11 TestSelection
[selection-tests.log](selection-tests.log), 1/1 varianti/magazzino
[variant-tests.log](variant-tests.log).
La prima esecuzione combinata di TestSelection e del nuovo test magazzino aveva
11 passaggi e 1 errore nella preparazione del test: nel database di prova il
website non aveva un magazzino assegnato. La fixture ora crea e assegna due
magazzini esclusivamente nel test; il nuovo test è stato rieseguito e superato.
Il log iniziale è conservato, senza presentarlo come interamente riuscito.

## File modificati per questa correzione

Nel modulo `custom/website_torrepulia_request/`:

- `__manifest__.py`
- `models/selection.py`
- `views/commerce.xml`
- `static/src/js/commerce.js`
- `static/src/scss/commerce.scss`
- `tests/test_commerce.py`
- `tests/test_commerce.mjs`
- `tests/test_selection.py`
- `README.md`, `QA-commerce.md`, `QA-selection.md` (note sull'aggiornamento della politica)

Nel bridge `custom/website_torrepulia_request_theme/`:

- `__manifest__.py`
- `views/commerce.xml`
- `tests/test_commerce.py`

Documentazione: `docs/TORREPULIA_RICHIESTE_GUIDA.md` e questa cartella di evidenze,
che include lo script riproducibile `browser_qa.py`.

## Aggiornamento e migrazione

Backup del database prima dell'intervento:
`../backups/torrepulia_before_stock_20261020.dump` (fuori repository).
Nessuna nuova tabella, colonna o migrazione di contenuti. Nessuna riscrittura
massiva di pagine salvate nel Builder e nessun aggiornamento del tema originale.
Sul solo ambiente di sviluppo, con il processo web fermo durante l'aggiornamento:

```sh
odoo -d torrepulia_cinematic_install \
  -u website_torrepulia_request,website_torrepulia_request_theme \
  --stop-after-init --no-http --max-cron-threads=0
```

Riavviare il servizio web. Gli asset frontend vengono rigenerati da Odoo; un
browser già aperto può richiedere un ricaricamento completo. Non servono
interventi manuali su prodotti, giacenze o contenuti salvati. Nessuna dipendenza
mancante nell'ambiente locale; nessun deploy in produzione.
