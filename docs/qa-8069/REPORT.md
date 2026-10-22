# Verifica locale 8069 — 19 ottobre 2026

Ambiente: `http://localhost:8069`, database **torrepulia_cinematic_install**,
Odoo **20.0-20260926**, progetto Compose `torrepulia-20-local-dev`.
Le modifiche sono applicate all'istanza locale, senza deploy in produzione.

## Problemi corretti

1. Il bundle delle opzioni Builder importava un'interazione presente soltanto
   nel frontend. L'inizializzazione dei plugin si interrompeva; gli errori
   `showUi` e `invalidate` erano conseguenze di quell'interruzione.
   Separati opzioni del Builder e interazione dimostrativa nell'iframe usando
   `website.website_builder_assets` e `website.assets_inside_builder_iframe`.
2. Corretti i riferimenti ai metodi negli handler Owl 20 delle opzioni.
   «Gestisci campagna e prodotti» apre il modulo della campagna effettiva,
   inclusa quella predefinita del website. La chiusura non usa elementi rimossi.
3. Le due viste della campagna avevano il contenuto XML subito dopo il tag
   `field`: con `--dev=xml`, il lettore nativo riceveva `field_arch.text=None`.
   Corretta la formattazione e aggiunto un test sul lettore nativo effettivo.
4. Nel layout hover del catalogo, le regole native per pulsanti a icona e quelle
   del tema deformavano e coprivano il pulsante testuale della richiesta.
   Aggiunti stili circoscritti alla modalità richiesta e al relativo pulsante.
   La modalità standard mantiene le regole native.
5. Alcune risposte del salvataggio Builder erano marcate frontend ma prive di
   website: la policy pubblica chiamava un metodo che richiede un solo website,
   causando `Expected singleton: website()`. Il riconoscimento delle superfici
   pubbliche richiede ora un website effettivo. Aggiunta regressione dedicata.
6. Corretto anche il collaudo: Playwright, nascondendo il cursore per gli
   screenshot, scriveva temporaneamente lo stile inline di tutti i campi
   editabili. Il Builder li considerava modificati e tentava di salvarli,
   incontrando gli XPath del footer. Gli screenshot del Builder usano ora
   `caret='initial'`. Le scritture del solo utente QA su viste e menu condivisi
   sono state ripristinate dal backup, conservando i dati editoriali precedenti.
   La gestione campagna apre l'azione backend in una scheda separata, senza
   abbandonare il Builder; l'anteprima si aggiorna dal relativo pulsante.
   Inoltre l'iframe degli editor autorizzati riceve il documento originale:
   non dipende dalla presenza di `enable_editor` nell'URL. Il gruppo resta
   obbligatorio; un pubblico non aggira la policy falsificando l'header iframe.

## Installazione e aggiornamento

Aggiornati i moduli locali mediante Odoo `--stop-after-init`; servizio 8069
riavviato. Versioni attese: `website_torrepulia_request` **20.0.1.6.1**,
`website_torrepulia_request_theme` **20.0.1.1.0**,
`website_torrepulia_request_campaign` **20.0.1.2.1**.
Vedere [log aggiornamento](upgrade-final-log.txt) e audit finale allegato.

Per ripetere l'aggiornamento in un altro ambiente locale, usare il relativo
file di configurazione e database:

```text
odoo -d <database_locale> -u website_torrepulia_request,website_torrepulia_request_theme,website_torrepulia_request_campaign --stop-after-init --no-http --max-cron-threads=0
```

Riavviare il processo web e ricaricare completamente la scheda (`Ctrl+F5`).
Non serve modificare il core né disattivare globalmente la modalità sviluppatore.
Queste correzioni non richiedono una nuova migrazione dei contenuti editoriali.

Backup precedenti alle modifiche, fuori dal repository:
`C:\Users\salvatore.leone\Downloads\torrepulia_odoo20\backups\`

- `torrepulia_cinematic_before_builderfix_20261019.dump`
- `torrepulia_cinematic_filestore_before_builderfix_20261019.tar.gz`

## Matrice delle verifiche effettive

| Scenario | Risultato | Evidenza / limite |
|---|---|---|
| Aggiornamento moduli sul database richiesto | Superato | Log aggiornamento e audit finale |
| Suite Odoo su database isolato | 75 superati, zero errori | [Log](odoo-tests.log), include regressione lettore XML |
| Regressione commerciale finale, incluso contesto Builder senza website | 8 superati, zero errori | [Log sintetico](commerce-final-tests.log) |
| Suite JavaScript | 31 superati, zero errori | [Log](javascript-tests.txt) |
| Parsing finale Python/XML | 71 file validi | Tutti e tre gli addon, compresi gli script QA |
| Apertura Builder sulla pagina stagionale originale | Superato nel browser | Screenshot e risultati Builder |
| Apertura modulo della campagna predefinita in nuova scheda, uscita dal Builder | Superato nel browser | Nessun errore JS/RPC/console nei passaggi registrati |
| Scelta prodotti dal campo nativo e riordinamento con trascinamento | Superato nel browser | Anteprima verifica l'ordine letto dal server |
| Duplicazione snippet, modifica titolo, salvataggio e ricaricamento | Superato nel browser | [Risultati Builder](builder-results.json); successiva riapertura/uscita senza errori |
| Contenuto salvato senza prodotti, prezzi o quantità dell'anteprima | Superato | Verifica dell'architettura salvata nella lingua effettiva del Builder |
| Catalogo: aggiunta di due prodotti senza reindirizzamento | Superato nel browser | [Risultati storefront](storefront-results.json) |
| Riepilogo: quantità da 1 a 3, altra riga conservata, contatore 4 | Superato nel browser | Risultati e screenshot riepilogo |
| Modulo vuoto: focus sul nome senza invio | Superato nel browser | Risultati storefront |
| Rimozione righe, selezione vuota e contatore zero | Superato nel browser | Risultati storefront |
| Riepilogo a 360, 390, 768, 1440 px | Superato per assenza di overflow orizzontale | Chromium headless; screenshot allegati |
| Pagamenti/email reali | Non eseguiti | Nessun invio finale sul database operativo locale |
| Screen reader, dispositivi fisici, Safari/Firefox | Non eseguiti | Non certificati dalle prove Chromium |

Le prove CRM, idempotenza, isolamento e accettazione dei preventivi della suite
restano prove automatiche su database isolato. Non sono presentate come invii
manuali o transazioni effettuate sul database locale storico.

Screenshot: [catalogo](screenshots/catalog-request-buttons.png),
[Builder](screenshots/builder-options-fixed.png),
[prodotti e riordinamento](screenshots/campaign-products-picker-reorder.png),
[pagina salvata e ricaricata](screenshots/builder-saved-reloaded.png),
[riepilogo 360 px](screenshots/review-360.png),
[riepilogo desktop](screenshots/review-1440.png).

## Dati e configurazione

Le prove editoriali usano una pagina temporanea **non pubblicata e non indicizzata**,
due campagne QA e un utente temporaneo con indirizzo `.invalid`.
Non modificano la campagna originale per simulare un assortimento approvato.
La campagna originale «Nuovo raccolto» era **chiusa e senza prodotti**: per
pubblicare una vetrina aperta occorre scegliere i prodotti reali e aprirla dal
backend. La campagna chiusa non impedisce la richiesta dal catalogo.

Nessun server SMTP attivo è stato aggiunto; nessuna email reale o pagamento.
I confronti di impronte e conteggi verificano CRM storico, ordini e righe,
prezzi di catalogo, giacenze, transazioni e fatture. L'audit finale registra anche
la conservazione di tutte le traduzioni della pagina originale e delle
impostazioni del website. Nessuna modifica a dominio, HTTPS o indicizzazione.

[Audit finale](final-audit.json): confermati anche tema condiviso e menu storici
uguali al backup, URL e pubblicazione delle pagine originali, direttive robots e
URL base invariati. Ripristinata anche la precedente architettura di una vista
toccata dal collaudo. Pagina e campagne QA eliminate; utente QA disattivato con
password ruotata e file privato delle credenziali eliminato. La copia temporanea
del database usata per il confronto è stata rimossa; i backup persistenti restano
nella cartella indicata sopra.

## File interessati da questa correzione

- `custom/website_torrepulia_request/__manifest__.py`
- `custom/website_torrepulia_request/views/commerce.xml`
- `custom/website_torrepulia_request/models/commerce.py`
- `custom/website_torrepulia_request/models/public_policy.py`
- `custom/website_torrepulia_request/tests/test_commerce.py`
- `custom/website_torrepulia_request/static/src/scss/commerce.scss`
- `custom/website_torrepulia_request/README.md`
- `custom/website_torrepulia_request_campaign/__manifest__.py`
- `custom/website_torrepulia_request_campaign/views/campaign.xml`
- `custom/website_torrepulia_request_campaign/static/src/js/campaign_options.js`
- `custom/website_torrepulia_request_campaign/static/src/js/campaign.edit.js`
- `custom/website_torrepulia_request_campaign/static/src/xml/campaign_options.xml`
- `custom/website_torrepulia_request_campaign/tests/test_campaign.py`
- `custom/website_torrepulia_request_campaign/tests/test_campaign.mjs`
- `custom/website_torrepulia_request_campaign/tools/*builder*.py`
- `custom/website_torrepulia_request_campaign/tools/restore_qa_shared_views.py`
- `custom/website_torrepulia_request_campaign/tools/storefront_browser_qa.py`
- `custom/website_torrepulia_request_campaign/README.md`
- `docs/TORREPULIA_RICHIESTE_GUIDA.md`, `docs/TORREPULIA_RICHIESTE_COLLAUDO.md`
  e questa cartella di evidenze.

Gli script browser richiedono Playwright/Chromium e il file privato di fixture
creato per questa sessione. Le credenziali non sono incluse nel repository.
Playwright è isolato in `/tmp/torrepulia-builder-python`, senza sostituire le
dipendenze Python di Odoo. La [guida operativa](../TORREPULIA_RICHIESTE_GUIDA.md)
descrive le configurazioni commerciali e la gestione quotidiana.
