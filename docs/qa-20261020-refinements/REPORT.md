# Rifiniture catalogo, conferma e pagina stagionale — 20 ottobre 2026

Applicate su **localhost:8069**, database **torrepulia_cinematic_install**.
Nessun deploy in produzione, invio CRM reale o pagamento durante il collaudo UI.

## Risultato

- Rimosso dalla hero il solo pulsante riconoscibile tramite `data-campaign-scroll`,
  anche dalle traduzioni già salvate nel Builder. Testi e fotografie conservati.
- Il pulsante sotto le card ha **20 px sopra e sotto** e continua a portare al
  modulo nella stessa pagina.
- Il riepilogo usa nome del prodotto/formato, normalizzando `LT` in `L`, e gli
  eventuali attributi realmente scelti. Non ripete descrizioni editoriali come
  «Per il consumo quotidiano» o la dicitura generica «Unità». Il contenuto
  complessivo in litri rimane basato esclusivamente sui dati commerciali configurati.
- Catalogo e snippet formati condividono lo stesso componente: varianti quando
  applicabili, quantità iniziale 1, pulsanti tondi verdi, input bianco centrale
  e **AGGIUNGI ALLA RICHIESTA** sotto il selettore. I pulsanti restano visibili
  anche senza hover. Touch target da 44 px su mobile.
- Le opzioni variante provengono dai record nativi esistenti, senza creare varianti
  filtrato/non filtrato nei prodotti reali. Non viene preselezionata una variante.
  Configurazioni personalizzate/dinamiche, combo, UoM multiple e assortimenti
  oltre 12 varianti conservano il passaggio esplicito alla scheda; la quantità
  scelta viene trasferita al controllo nativo della scheda.
- Il pop-up mostra intestazione con check, prodotto/variante, quantità appena
  aggiunta e subtotale calcolato dal server con quantità, listino, valuta e imposte
  native. Una singola POST contiene prodotto, variante/configurazione e quantità.
  La selezione resta distinta dal carrello e-commerce: non viene creato un ordine.
- **Continua a scegliere** chiude la conferma; **VAI AL RIEPILOGO** usa il percorso
  centralizzato del website. I prezzi restano assenti quando disabilitati.
- La nota è resa come «Importo da pagare oggi: 0,00 €; pagamento al momento della
  spedizione», per distinguere l'assenza di anticipo dal subtotale prodotti.

## Euro e dati commerciali

Configurato il listino nativo **Torrepulia - EUR**, limitato al website e alla sua
azienda. Attivata la valuta EUR; il contesto pubblico usa l'euro in catalogo,
pagina stagionale, riepilogo e conferma. Non è una sostituzione del simbolo `$`.

La conversione usa i tassi già presenti in Odoo. In questo database di sviluppo
il calcolo nativo per 69 unità della valuta aziendale restituisce **69,00 EUR**.
Non sono stati inventati o aggiornati tassi, né riscritti prezzi prodotto,
valuta aziendale, ordini o preventivi esistenti. I preventivi futuri restano
soggetti alla revisione commerciale nativa. Evidenza: `configure-eur.log`.

La configurazione è ripetibile con `configure_eur.py`, esclusivamente sul database
di sviluppo dichiarato. Non viene applicata automaticamente agli altri website.

## Aggiornamento e backup

Versioni installate: richiesta **20.0.1.8.0**, integrazione tema **20.0.1.2.0**,
campagne **20.0.1.3.1**. Aggiornamento effettuato sul progetto Compose reale
`torrepulia-20-local-dev`:

```text
odoo -d torrepulia_cinematic_install -u website_torrepulia_request,website_torrepulia_request_theme,website_torrepulia_request_campaign --stop-after-init --no-http --max-cron-threads=0
```

Log: `upgrade.log`. Prima dell'aggiornamento e della configurazione EUR:

- `C:\Users\salvatore.leone\Downloads\torrepulia_odoo20\backups\torrepulia_before_refinements_20261020.dump`;
- `C:\Users\salvatore.leone\Downloads\torrepulia_odoo20\backups\torrepulia_filestore_before_refinements_20261020.tar.gz`.

La migrazione della hero è circoscritta e idempotente. Non richiede il reset della
pagina o la reinstallazione del tema. Nessuna modifica a core, HTTPS, dominio o SEO.
Ricaricare completamente il browser con **Ctrl+F5**.

## Verifiche

| Scenario | Esito | Evidenza |
|---|---|---|
| Catalogo: default 1, due clic su più, aggiunta di 3 | Passato | Una sola mutazione, quantità server 3, `checks.json` |
| Conferma dinamica in EUR | Passato | Testo quantità 3, subtotale identico alla risposta server, nessun `$` |
| Seconda aggiunta di 2 sullo stesso prodotto | Passato | Totale richiesta 5; pop-up quantità 2 e subtotale solo delle ultime 2 |
| Continua a scegliere / Vai al riepilogo | Passato | Chiusura senza navigazione; collegamento e quantità 5 nel riepilogo |
| Pulsanti senza hover | Passato | Opacità 1 e trasformazione assente su tutte le azioni della griglia |
| 360 e 390 px | Passato | Nessun overflow della pagina o dei selettori rispetto alle card |
| Riepilogo uniforme | Passato | Senza descrizione marketing e dicitura ridondante UoM |
| Hero e margini CTA | Passato | Assenza pulsante hero, margini calcolati 20/20 px |
| Quantità nel passaggio alla scheda | Passato | Il controllo nativo carica la quantità desiderata 7 |
| JavaScript | **34/34 passati** | `js-tests.log` |
| Odoo backend/HTTP | 25 eseguiti: 24 passati, 1 failure dello snippet | `odoo-tests.log`, database separato `torrepulia_request_test` |
| Ripetizione dopo correzione snippet QWeb | **1/1 passato**, zero errori | `odoo-theme-retest.log` |
| Snippet reale sulla 8069 | Passato | RPC nativa con controlli condivisi e prezzi EUR, `snippet-live.log` |
| Analisi statica design | Nessun rilievo | `design-detect.json` |

Il collaudo UI non invia il modulo finale: le bozze anonime seguono la pulizia
ordinaria configurata. I test HTTP sul database separato verificano invece
quantità aggiunta rispetto alla quantità cumulativa, prezzi nascosti, varianti
native distinte, invio protetto, ACL e comportamento standard disattivato.

La failure iniziale era il contesto `product` non disponibile nel template
condiviso dello snippet. In QWeb 20 l'assegnazione viene ora eseguita prima della
chiamata al template. Il test coinvolto è stato ripetuto con successo e la RPC
reale verificata anche sul database della 8069. Non si dichiara una seconda
esecuzione completa dei 25 test: le restanti 24 verifiche erano già passate.

Non è stato ripetuto un ciclo completo di modifica/salvataggio nel Builder in
questa rifinitura; la migrazione è coperta dal test di idempotenza e dalla verifica
della pagina reale. Il ciclo Builder della revisione precedente è documentato
in `../qa-20261020/REPORT.md`.

Screenshot desktop/mobile e script riproducibile sono in questa cartella.
`checks.json` registra le verifiche effettive e l'assenza di errori JavaScript.

## File modificati

`custom/website_torrepulia_request/`:

- `__manifest__.py`, `README.md`;
- `models/commerce.py`, `models/review.py`, `controllers/selection.py`;
- `views/commerce.xml`;
- `static/src/js/commerce.js`, `static/src/js/review.js`;
- `static/src/scss/commerce.scss`;
- `tests/test_commerce.py`, `tests/test_commerce.mjs`.

`custom/website_torrepulia_request_theme/`:

- `__manifest__.py`, `README.md`, `views/commerce.xml`, `tests/test_commerce.py`.

`custom/website_torrepulia_request_campaign/`:

- `__manifest__.py`, `README.md`, `models/page.py`, `views/snippet.xml`;
- `static/src/scss/campaign.scss`, `tests/test_campaign.py`.

Documentazione: `docs/TORREPULIA_RICHIESTE_GUIDA.md` e questa cartella.
