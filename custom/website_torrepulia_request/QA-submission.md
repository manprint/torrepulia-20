# Issue 6 — Invio persistente, CRM e notifiche

## Implementazione

L'unico ingresso pubblico resta il POST finale con CSRF e CAPTCHA nativo,
capacità riservata alla sessione e controllo website/azienda. Vengono rivalidati
catalogo, variante, configurazione e quantità; nome/email sono obbligatori,
email normalizzata con Odoo e telefono facoltativo normalizzato tramite il
servizio nativo `phone_validation`. Il paese è quello del contatto autenticato
autorizzato, se disponibile, altrimenti dell'azienda; con numeri esteri indicare
il prefisso internazionale. Un telefono non valido produce un errore sul campo.
Non vengono cercati account o contatti per email.

Blocco riga PostgreSQL, revisione e identificativo di invio proteggono la
transizione. Fotografie delle righe, dati di invio, opportunità, collegamento,
stato inviato, due notifiche persistenti e nuova selezione vuota fanno parte
della stessa transazione/savepoint. Un errore ripristina la bozza e le righe.
Il token della sessione live non viene ruotato prima del commit: la lettura
successiva risolve deterministicamente la nuova bozza già preparata.

Lo stesso invio restituisce lo stesso riferimento senza duplicare opportunità
o notifiche, anche dopo la scadenza della pagina di conferma (24 ore). La chiave
di deduplicazione non scade. Una nuova selezione ha un nuovo identificativo e
può essere inviata intenzionalmente. Un replay precedente non la svuota.

L'opportunità usa website, azienda, team e assegnatario server, recapiti,
note HTML con escaping e righe strutturate collegate. `torrepulia_website_id`
e `torrepulia_request_origin` sono nuovi campi del modulo, non API native.
L'origine CRM è «Richiesta sito web». La sorgente UTM omonima è usata quando
non esiste una sorgente già raccolta; il mixin nativo `utm.mixin` raccoglie i
cookie UTM standard all'apertura della bozza. Campagna, mezzo e sorgente UTM
presenti nella richiesta sono conservati. La vetrina stagionale è un modello editoriale
distinto da `utm.campaign`: non si inventa un'attribuzione solo perché un prodotto
compare nella campagna o perché essa è configurata sul website.

Nelle impostazioni del website è disponibile la fase iniziale CRM. Se non scelta,
al primo invio viene creata «Richiesta web ricevuta», aperta e limitata al team
destinatario; nessuna fase/opportunità preesistente viene modificata. Una fase
vinta o non accessibile al team viene rifiutata. L'opportunità resta aperta.

## Email e recupero errori

Ogni richiesta ricevuta crea due record `torrepulia.request.notification` con
vincolo univoco `(request_id, kind)`. Il cron di preparazione gira ogni cinque
minuti, prende al massimo 100 record e usa `FOR UPDATE SKIP LOCKED` e savepoint
per record. Genera `mail.mail` con `mail.template.send_mail(force_send=False)`;
non apre connessioni SMTP. Non crea né associa contatti destinatari.

La ricevuta cliente contiene riferimento, prodotti, varianti/configurazioni,
quantità e indicazione che non è un ordine confermato. Usa la fotografia del
riepilogo, senza ricalcolare prezzi sul catalogo modificabile. Gli importi
compaiono solo se visibili sia all'invio sia alla preparazione: «Totale prodotti
della richiesta», con consegna da definire. Nessun importo quando nascosti.
Il messaggio interno contiene anche recapiti e note; i destinatari sono membri,
responsabile e assegnatario attivi, interni e abilitati all'azienda della richiesta.
Nessun testo promette tempi non configurati.

I template sono dati `noupdate` modificabili dall'amministratore. Errori di
template/destinatari restano registrati nella scheda «Notifiche» della richiesta,
con un nuovo tentativo dopo un'ora, massimo cinque tentativi. Correggere email
del team, mittente aziendale o template. Dopo cinque errori, l'amministratore
può riprogrammare i soli record falliti tramite ORM (`attempts=0`, `retry_at=now`):
non riprogrammare record già in coda. Gli utenti commerciali hanno sola lettura,
con gli stessi limiti di team e azienda della richiesta; pubblico/portale nessun
accesso. Nessun endpoint pubblico espone la coda.

Quando il record è in coda, non viene mai generata una seconda email dal cron,
anche se l'email è poi cancellata. `auto_delete=False` conserva la traccia.
Errori SMTP sono gestiti dalla coda email nativa e si ritentano lì, senza
riaprire la richiesta. Come per qualsiasi SMTP, non si promette consegna
«exactly once» quando il server remoto riceve il messaggio ma perde la risposta;
la protezione applicativa impedisce duplicati da doppio clic/replay/concorrenza.

## Aggiornamento e migrazione

Nessun deploy eseguito. Solo sviluppo/staging, con backup DB/filestore e SMTP
intercettato o configurato esclusivamente su destinatari di prova:

```sh
odoo -d <database_sviluppo> -u website_torrepulia_request --stop-after-init
```

Riavviare Odoo per caricare il nuovo modello. `website_sale`, `sale_crm` e le
relative dipendenze devono essere installati. Il pacchetto Python `phonenumbers`
è ora esplicito nel manifest; presente nell'ambiente verificato (8.12.57).
Sono stati letti i sorgenti nativi Odoo 20 installati: `crm.stage.team_ids`,
template mail con `find_or_create_partners=False`, queue e gestione errori SMTP.

L'ORM aggiunge i nuovi campi, la tabella notifiche e il vincolo univoco. Nessun
aggiornamento del tema originale o dei contenuti Builder. Le richieste già inviate
non vengono riscritte né ricevono email retroattive; nessuna migrazione automatica
di fasi, opportunità o contatti storici. Impostazioni standard restano inattive
finché il website non abilita la modalità richiesta. Non cambiano dominio,
HTTPS, indicizzazione, prezzi, giacenze o politiche di disponibilità.

## File modificati in questa issue

Tutti sotto `custom/website_torrepulia_request/`:

- `__manifest__.py`: versione 20.0.1.4.0, dipendenza Python, nuovi dati.
- `models/__init__.py`, nuovo `models/submission.py`: fase, origine/website CRM,
  validazione telefono, modello notifiche e cron di preparazione.
- `models/request.py`: elaborazione CRM e intenzioni di notifica atomiche.
- `models/review.py`: nuova bozza transazionale e deduplicazione senza scadenza.
- Nuovo `data/notification_data.xml`: sorgente, template e cron.
- `security/ir.access.csv`: accessi e isolamento della coda.
- `views/settings.xml`, `views/request.xml`: fase iniziale e stato notifiche.
- `tests/__init__.py`, nuovo `tests/test_submission.py`.
- `tools/review_concurrency_qa.py`: verifica anche preparazione concorrente email.
- `README.md`, nuovo `QA-submission.md`, nuovo `submission-test-results.txt`.

## Verifiche

Risultati effettivi e comandi in [submission-test-results.txt](submission-test-results.txt).
Esito finale: **55 test Odoo, 29 test JavaScript e 3 scenari PostgreSQL superati**.
Le prove usano solo `torrepulia_request_test`, email `.invalid`, preparazione
senza SMTP e connessione SMTP intercettata per l'errore simulato. Nessuna email
reale e nessun pagamento. Il database `odoo_dev` e la produzione non sono aggiornati.

Browser non disponibile: inventario `apps: [], browsers: []`. Screenshot delle
nuove impostazioni e schede CRM non eseguibili; viste validate dall'aggiornamento
Odoo, ma verifica visiva nel browser ancora da eseguire nell'ambiente collegato.
