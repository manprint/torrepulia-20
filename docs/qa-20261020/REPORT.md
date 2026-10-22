# Aggiornamento locale 20 ottobre 2026

Applicato a **http://localhost:8069**, database **torrepulia_cinematic_install**.
Odoo installato: **20.0-20260926**. Nessun deploy in produzione.

## Modifiche

- **Website → Sito → Campagne olio nuovo**: corretta la collocazione del menu
  usando il riferimento nativo `website.menu_site`.
- Dopo l'invio confermato si apre immediatamente la conferma. Il componente non
  pubblica prima una nuova selezione vuota e ignora risposte di riepilogo tardive.
- Nel catalogo ogni pulsante di richiesta dispone della quantità da aggiungere.
  I prodotti configurabili continuano a richiedere la scelta esplicita della
  configurazione; non viene scelta una variante arbitraria.
- Card stagionali su fondo bianco, immagini intere, disposizione editoriale a
  due colonne, quota immagine del 44% sulla card orizzontale desktop, pulsanti
  tondi più/meno e tre indicazioni con icone SVG accessibili.
- Rimossa la vecchia sezione «Come prosegue» e il titolo isolato «La tua selezione».
  Il collegamento sotto le card porta al modulo nella stessa pagina.
- Come richiesto nella precisazione successiva, **anche la pagina stagionale può
  inviare la richiesta**. Riutilizza esattamente il componente, il servizio e
  l'endpoint protetto della pagina La tua richiesta; nessun secondo flusso CRM.
- Layout 60/40 su desktop: prodotti compatti e recapiti a sinistra; box
  `tp-review-order-summary`, fondo `#fcfbf9`, bordo e padding 30 px a destra.
  Su mobile passa a una colonna. Nome/email affiancati, telefono a metà riga,
  note a larghezza piena e altezza ridotta.
- Privacy, indicazione «Totale da pagare oggi: 0,00 €», nota spedizione e pulsante
  **CONFERMA LA MIA PRENOTAZIONE** nel box destro. Resta esplicito che l'invio
  non conferma un ordine e non richiede un pagamento.
- I controlli quantità attendono la risposta autorevole e impediscono clic
  ripetuti durante il salvataggio. Quantità e prodotti delle altre superfici
  restano condivisi; i recapiti digitati non vengono cancellati.

## Installazione e migrazione

Aggiornati e verificati come installati:

| Modulo | Versione |
|---|---|
| `website_torrepulia_request` | 20.0.1.7.0 |
| `website_torrepulia_request_campaign` | 20.0.1.3.0 |
| `website_torrepulia_request_theme` | 20.0.1.1.0, invariata |

Comando di aggiornamento: `odoo -d torrepulia_cinematic_install -u website_torrepulia_request,website_torrepulia_request_campaign --stop-after-init --no-http --max-cron-threads=0`.
È stato usato il Compose reale `torrepulia-20-local-dev`, poi riavviato il servizio
che pubblica la 8069. Log: [aggiornamento](upgrade-final.log).

Prima delle modifiche al database sono stati creati dump e filestore in
`C:\Users\salvatore.leone\Downloads\torrepulia_odoo20\backups`:

- `torrepulia_before_ui_20261020.dump`;
- `torrepulia_filestore_before_ui_20261020.tar.gz`.

La migrazione riguarda solo le pagine `/prenotailtuoolio` dei website Torrepulia
abilitati e tutte le loro traduzioni salvate. Rimuove il blocco riconosciuto
`tp-campaign-next`, aggiunge il contenitore dinamico del modulo e applica una
sola volta la disposizione editoriale a due colonne. Sostituisce solo
l'introduzione standard riconosciuta e rimuove solo il paragrafo standard sul
pagamento, ora rappresentato dall'icona. Titoli/testi personalizzati, immagini,
URL, HTTPS e impostazioni SEO restano conservati. Il marcatore
`data-editorial-layout="2"` permette successive scelte del gestore senza
riapplicare la disposizione a ogni aggiornamento.

Le tre nuove note della campagna sono modificabili dal backend, nel gruppo
**Indicazioni commerciali approvate**. Le frasi fornite dal gestore sono state
compilate solo dove mancanti nella campagna corrente. Stato, prodotti, varianti
e relativo ordine di presentazione non sono stati sostituiti.

Il modulo stagionale viene caricato a runtime con risposta privata `no-store`.
Nel Builder rimane un segnaposto; il pulitore di salvataggio rimuove anche un
eventuale modulo materializzato. Nessun recapito, prezzo o quantità personale
deve diventare contenuto editoriale salvato.

## Matrice dei controlli effettivamente eseguiti

| Scenario | Risultato | Evidenza / limite |
|---|---|---|
| Aggiornamento moduli sulla 8069 | Passato | `upgrade-final.log`, `audit-live.log` |
| Menu nel Website | Passato | Padre verificato tramite XML ID nativo |
| Viste campagna form/list con modalità XML | Passato | Chiamata nativa `get_view`, audit finale |
| Catalogo: scegliere 2 e aggiungere una volta | Passato | `checks.json`, `catalog-desktop-quantity.png` |
| Catalogo 2 → stagionale 3 | Passato | Quantità 3 anche nel modulo; non 5 |
| Aggiunta del secondo prodotto | Passato | Due righe conservate, riepilogo condiviso |
| Riepilogo: più/meno | Passato | Quantità aggiornata anche nella selezione comune |
| Clic ripetuto durante aggiornamento | Passato | `review_controls_qa.py`: un solo cambiamento, note conservate |
| Invio → conferma rallentata | Passato | Risposta simulata, navigazione ritardata 1,2 s, osservatore DOM: nessun flash vuoto |
| Card, icone, riepilogo desktop | Passato | Screenshot in questa cartella; conferma dopo correzione della specificità CSS del tema |
| 360, 390 e 820 px | Passato | Screenshot stagionale/riepilogo, nessun overflow orizzontale |
| Builder: apertura, opzioni, isolamento | Passato | `builder-isolated.png`, quantità disabilitate, nessun campo contatti caricato |
| Builder: modifica titolo, salva, ricarica | Passato | Pagina temporanea, titolo riletto dopo il salvataggio; nessun errore JS |
| Builder: contenuto salvato senza dati personali | Passato | `cleanup.log`, controllo di tutte le traduzioni salvate |
| Test JavaScript | **34/34 passati** | `js-tests.log` |
| Suite Odoo completa | 77 eseguiti: inizialmente 74 passati, 2 failure e 1 errore | `odoo-tests.log`; tre fixture/assert aggiornati per nuova struttura, CTA e segnaposto |
| Ripetizione delle tre classi coinvolte | **18/18 passati**, zero errori | `odoo-retest.log`; include invio, contatti, privacy, prezzi, migrazione e isolamento |
| Controllo statico design | Nessun rilievo | `design-detect.json` |

La suite completa comprende sicurezza e isolamento, idempotenza/concorrenza,
prezzi nascosti, blocco checkout, CRM, preparazione preventivo e accettazione
nativa. Non si dichiara una seconda esecuzione completa verde: dopo le correzioni
sono state ripetute le 18 verifiche delle classi coinvolte. I test backend sono
stati eseguiti esclusivamente sul database separato `torrepulia_request_test`.

Il controllo visivo dell'invio sulla 8069 usa una risposta simulata: non crea
un'opportunità o una ricevuta email nel database di lavoro. L'invio reale e i
ritentativi sono invece verificati dai test HTTP Odoo sul database di prova.
Nessun pagamento o destinatario reale utilizzato.

Non sono stati ripetuti oggi il trascinamento dei prodotti, la duplicazione dello
snippet o un audit completo con lettore di schermo: rimangono distinti dai
controlli Builder eseguiti e dalle evidenze del 19 ottobre.

## File modificati per questa revisione

Nel modulo `custom/website_torrepulia_request/`:

- `__manifest__.py`, `README.md`;
- `controllers/review.py`;
- `static/src/js/commerce.js`, `static/src/js/review.js`;
- `static/src/scss/commerce.scss`, `static/src/scss/review.scss`;
- `views/commerce.xml`, `views/review.xml`;
- `tests/test_review.py`, `tests/test_review.mjs`.

Nel modulo `custom/website_torrepulia_request_campaign/`:

- `__manifest__.py`, `README.md`;
- `models/campaign.py`, `models/page.py`;
- `static/src/js/campaign.js`, `static/src/js/campaign_options.js`;
- `static/src/scss/campaign.scss`;
- `views/campaign.xml`, `views/snippet.xml`;
- `tests/test_campaign.py`, `tests/test_campaign.mjs`, `tests/test_http.py`.

Documentazione: `docs/TORREPULIA_RICHIESTE_GUIDA.md` e questa cartella di
script, log e screenshot. Il core Odoo e il tema originale non sono modificati.

## Note operative

- Ricaricare completamente il browser, **Ctrl+F5**, per i nuovi asset.
- L'ambiente mostra attualmente prezzi in **USD**, secondo il listino nativo:
  non è stata cambiata la valuta commerciale. Il testo «0,00 €» segue la copy
  esplicitamente richiesta e indica soltanto l'assenza di addebiti oggi.
- «Prezzo bloccato garantito» è la nota approvata dal gestore: non congela
  tecnicamente i prezzi dei futuri preventivi Odoo. Il commerciale continua
  a verificare listino, imposte e condizioni nel preventivo.
- La pagina/view temporanea di collaudo è stata eliminata. L'account di prova
  è stato archiviato, la password ruotata e il file credenziali cancellato.
- La guida aggiornata descrive menu, indicazioni commerciali, selezione quantità
  e invio da entrambe le pagine. Non occorre reinstallare il tema.
