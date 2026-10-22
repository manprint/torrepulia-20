# Issue 5 — revisione e invio pubblico

## Risultato

`/la-tua-richiesta` usa il titolo e l'introduzione del brief, mostra tutte le righe
con miniatura, nome, formato quando disponibile, attributi/varianti e testi
personalizzati, UoM, quantità modificabile, rimozione, contenuto e importi quando
abilitati. Non replica il catalogo: «Aggiungi altri prodotti» apre `/shop`.
Le modifiche usano esclusivamente il servizio condiviso con revisioni e
idempotenza; header e pagina stagionale ricevono lo stato autorevole.

Il form richiede solo nome, email e la presa visione privacy già presente nel
tema. Telefono e note sono facoltativi. Nessuna registrazione, fatturazione,
indirizzo o consenso marketing. I recapiti del partner autenticato vengono
precompilati e restano verificabili/modificabili. Informativa e link
`/privacy-policy` conservati senza cambiarne il testo approvato.

Stato vuoto: messaggio e pulsante richiesti, form nascosto/disabilitato. Invio:
stato comprensibile, controlli bloccati contro il doppio clic. Errori: messaggio,
focus sul campo o sull'avviso, valori del form conservati. Un esito di rete incerto
mantiene in memoria lo stesso payload e identificatore; «Riprova invio» verifica
quello stesso invio. I recapiti non vengono memorizzati in sessionStorage/localStorage.

Solo una risposta positiva del server apre `/la-tua-richiesta/conferma`, con titolo
di successo, riferimento, fotografia immutabile delle righe e passaggio successivo,
senza promesse di tempi. Nessun recapito o identificativo della richiesta in URL.
La conferma richiede la capacità della sessione originaria, limitata al website e
all'azienda, e resta consultabile per 24 ore. La scadenza limita la consultazione
pubblica; non cancella richiesta, opportunità o preventivi.

## Prezzi e contenuti commerciali

La proiezione del riepilogo usa `_get_combination_info`, la sua valuta, quantità,
UoM, listino e posizione fiscale correnti, con `format_amount`. «Totale prodotti»
è distinto dal trasporto ancora da definire. Se una riga non è più valida o non
può mostrare un prezzo nativo, non presenta una somma parziale come totale completo.
Con prezzi nascosti non trasmette campi economici e non crea contenitori vuoti.

Nuovo campo commerciale esplicito per variante: `torrepulia_request_liters`,
«Litri per unità di vendita». Si configura dalla scheda prodotto per una sola
variante oppure dalla scheda di ciascuna variante. Zero significa sconosciuto;
valori negativi/non finiti sono rifiutati. La quantità selezionata è convertita
all'UoM di vendita con `_compute_quantity(..., round=False)` nativo prima di
calcolare il contenuto. Il totale in litri compare solo se tutte le righe valide
hanno tale contenuto configurato. Non legge nomi, descrizioni, peso o volume
logistico. Nessun valore viene dedotto o assegnato automaticamente ai prodotti
esistenti. Aggiornando l'UoM di vendita, il gestore deve verificare anche questo
dato commerciale per la nuova unità.

## Confine di invio e sicurezza

POST `/torrepulia/request/submit`: CSRF nativo, payload con whitelist e limiti,
validazione server di nome/email/privacy e della revisione, nuova validazione
commerciale completa delle righe. Nessun prezzo, team, azienda, proprietario o
indirizzo di fatturazione accettato dal client. Usa il metodo CRM `_submit` già
implementato, senza creare ordini, contatti anonimi, pagamenti, fatture o riserve.

La sessione conserva un segreto distinto dalla selezione che può ruotare dopo
l'invio. Solo il suo hash viene associato alla richiesta, con ricerca elevata
strettamente circoscritta a capacità + website + azienda + stato + scadenza e,
per i ritentativi, identità della selezione. Nessuna ACL pubblica/portale aggiunta.
Le elevazioni CRM restano quelle già validate dal metodo finale esistente.

Identificatore e impronta del payload normalizzato rendono idempotente il
ritentativo identico; un payload diverso per una richiesta già inviata viene
rifiutato. Il lock della richiesta serializza modifica e invio. Se la revisione
è superata, il visitatore deve ricontrollare la selezione. Un savepoint comprende
contenuto della conferma, timestamp privacy, recapiti, fotografie delle righe e
creazione CRM: un errore annulla l'intero invio senza perdere la bozza.

Riutilizza la verifica nativa `_verify_request_recaptcha_token('website_form')`
e il generatore reCAPTCHA. Il form conserva `data-captcha` per l'interazione
Turnstile nativa, se installata/configurata; soltanto la submit sincrona reCAPTCHA
di questo form è sostituita dall'invio AJAX. Gli altri form conservano il metodo
nativo. Un replay già autorizzato e confermato non deve superare un secondo CAPTCHA.
Nei test non sono usati servizi esterni di verifica né inviati messaggi reali.

Le pagine e le risposte hanno `private, no-store` e `Vary: Cookie`; niente dati
personali in query string. Il documento contiene solo recapiti dell'utente
autenticato corrente. La pagina applicativa non è un contenuto Builder salvabile:
nessuna migrazione o riscrittura di pagine editoriali. Portale preventivi,
accettazione online nativa e backend restano nei rispettivi flussi autorizzati.

## File di questa issue

Sotto `custom/website_torrepulia_request`:

- `__manifest__.py`: versione 20.0.1.3.0, viste e asset.
- `models/__init__.py`, nuovo `models/review.py`: proiezione, dati commerciali
  in litri, capacità di conferma e invio idempotente.
- `controllers/__init__.py`, nuovo `controllers/review.py`: riepilogo, anteprima,
  invio e conferma privata.
- Nuovo `views/review.xml`: pagina/modulo, conferma e configurazione litri nelle
  viste native prodotto/variante.
- Nuovi `static/src/js/review.js` e `static/src/scss/review.scss`.
- `static/src/js/request_store.js`: rilettura autorevole e notifica agli altri
  componenti dopo conferma dell'invio.
- `tests/__init__.py`, nuovi `tests/test_review.py`, `tests/test_review.mjs`.
- Nuovo `tools/review_concurrency_qa.py`: concorrenza reale PostgreSQL, bloccato
  su ogni database diverso da quello isolato di test.
- `README.md`, `QA-review.md`, `review-test-results.txt`.

Nessun file del core o del tema originale modificato. Gli addon delle issue
precedenti erano già non tracciati nel workspace; nessun commit/deploy eseguito.

## Aggiornamento e migrazione

Con backup DB/filestore e recapiti/SMTP di prova, solo sviluppo o staging:

```sh
odoo -d <database_sviluppo> -u website_torrepulia_request --stop-after-init
```

Riavviare Odoo per i nuovi controller/modelli e gli asset. Nessuna nuova dipendenza
esterna: `google_recaptcha` è già dipendenza del Website installato. Nessun
aggiornamento del tema richiesto. L'ORM aggiunge i campi di invio e contenuto;
nessuna migrazione di lead, richieste inviate, prezzi, stock o contenuti Builder.
Le richieste inviate prima di questa versione conservano i dati precedenti, senza
ricevere retroattivamente una capacità di consultazione pubblica.
La destinazione pronta è `/la-tua-richiesta`; un'eventuale pagina personalizzata
configurata come destinazione deve integrare il nuovo componente/template.

## Test e limiti

Comandi ed esiti effettivi in [review-test-results.txt](review-test-results.txt).
Esito finale: **47 test Odoo, 29 test JavaScript e 2 scenari PostgreSQL superati**.
Test HTTP: pubblico senza account, CSRF, privacy/campi, dati manipolati, successo,
replay dopo rotazione della selezione, chiamate obsolete, altri visitatori/website,
scadenza della conferma, precompilazione autenticata, errore CAPTCHA/CRM con rollback,
prezzi nascosti, litri completi/incompleti, varianti/custom e conversione UoM.
Node: doppio clic, esito incerto, correzione dati, nessuna navigazione su errore,
conferma solo server, aggiornamento condiviso e regressioni delle altre superfici.
Due scenari PostgreSQL paralleli reali verificano duplicazione e corsa modifica/invio.

Browser non disponibile (`apps: [], browsers: []`): screenshot, collaudo visivo
desktop/mobile, focus nel browser e verifica con CAPTCHA reali non eseguibili qui.
I test Node simulano DOM/dipendenze e non sostituiscono queste prove. I test e le
fixture sintetiche commesse dal tool di concorrenza restano soltanto in
`torrepulia_request_test`; le richieste inviate non sono cancellate aggirando le
protezioni di immutabilità. Nessuna modifica a `odoo_dev` o produzione.
