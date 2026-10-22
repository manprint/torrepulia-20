# Vetrina stagionale Torrepulia

Modulo `website_torrepulia_request_campaign`, versione `20.0.1.3.1`.
Dipende dai moduli richiesta, integrazione tema e tema Torrepulia presenti nel
repository. Riutilizza il servizio unico `torrepulia.request` delle issue 1–2.
Non modifica il core o i file del tema originale.

Correzioni Builder del 19 ottobre: opzioni nel bundle del Builder e interazione
dimostrativa nel bundle dell'iframe, handler compatibili con Owl 20, gestione
diretta della campagna esplicita o predefinita in una nuova scheda tramite
l'URL dell'azione backend, preservando lo stack del Builder; dopo il salvataggio
usare «Aggiorna anteprima».
Viste backend compatibili anche
con `--dev=xml`. Aggiornare con `-u website_torrepulia_request_campaign` e
ricaricare completamente il browser. Evidenze su 8069 in
`docs/qa-8069/REPORT.md`.

## Risultato

La pagina `/prenotailtuoolio` contiene uno snippet stagionale configurabile:
hero compatta con fotografia autentica già presente nel tema, griglia fotografica
dei formati e lo stesso modulo di revisione/invio della pagina La tua richiesta.
La revisione del 20 ottobre è richiesta esplicitamente dal gestore: invio anche
dalla pagina stagionale, con prodotti e recapiti a sinistra e chiusura a destra.
Le immagini
prodotto sono quelle delle varianti Odoo (`object-fit: contain`), senza ritagli.
Due/tre colonne desktop e una colonna mobile, controlli da almeno 48 px.

Ogni controllo imposta la quantità totale di quella configurazione. Non incrementa
la quantità già selezionata e non elimina prodotti esterni alla campagna. Le
varianti sono righe indipendenti; UoM o configurazioni commerciali differenti non
vengono sommate nello stesso controllo. Il riepilogo distingue confezioni della
campagna, intera richiesta e altre configurazioni/prodotti. Il collegamento
«Completa la tua prenotazione» porta al modulo nella stessa pagina; senza
JavaScript conserva il collegamento centrale al riepilogo. Il clic non invia
dati a CRM: occorre completare il modulo e confermare esplicitamente l'invio.

Prezzi e riferimento per unità provengono esclusivamente da `_get_combination_info`
e `format_amount` nel contesto commerciale corrente. Il prezzo al litro compare
quando l'unità base L e il relativo conteggio sono realmente configurati nel
prodotto e il prezzo di riferimento è abilitato nel website. Nessuna deduzione
dei litri dalle descrizioni editoriali. Prezzi nascosti: nessun importo è incluso
nel frammento pubblico e nessuno spazio prezzo viene riservato.

Stato aperta/chiusa e periodo limitano la sola vetrina. Il catalogo e la richiesta
restano disponibili. La pagina ricontrolla la campagna al ritorno/focus e alle
scadenze temporali configurate. Chiusa: messaggio del gestore e accesso al catalogo;
il conteggio della selezione esistente rimane distinto e nessuna riga è cancellata.

Per attributi personalizzati/senza variante o composizioni che richiedono un
ulteriore passaggio, la scheda rinvia esplicitamente alla configurazione prodotto:
non assegna valori commerciali arbitrari. Le normali varianti selezionate dal
gestore hanno ciascuna il proprio controllo quantità.

## Configurazione dall'interfaccia

1. Aprire Website → Sito → **Campagne olio nuovo**. Impostare nome, riferimento, website,
   stato, eventuali date e periodo indicativo di consegna, testo editoriale e
   messaggio di chiusura.
2. Nella lista **Prodotti e varianti**, selezionare prodotti esistenti dal picker
   Odoo. Usare la maniglia per riordinare. Contenuto confezione e descrizione sono
   editoriali: non cambiano UoM, attributi, prezzi o quantità disponibili.
3. Aprire `/prenotailtuoolio` in Website Builder e selezionare lo snippet
   **Richiesta del nuovo raccolto**. Scegliere la campagna dal picker, senza ID
   manuali. **Gestisci campagna e prodotti** apre la gestione nativa; **Aggiorna
   anteprima** rilegge la configurazione. Senza selezione esplicita si usa la
   campagna predefinita creata per quel website.
4. Modificare titolo, introduzione e fotografia direttamente nella pagina.
   Impostare due/tre colonne e l'anteprima dimostrativa zero/uno/più prodotti.
5. Aprire la campagna quando l'assortimento è pronto e la modalità richiesta è
   configurata nel website. Per l'allestimento iniziale scegliere i prodotti
   filtrati già configurati dal gestore; non vengono create varianti artificiali.

L'installazione crea una campagna **chiusa e senza prodotti**, evitando di
attribuire autonomamente filtrazione o raccolto a prodotti esistenti. La lettura
del catalogo locale `odoo_dev` ha trovato quattro formati La Regina e nessun
attributo nativo di filtrazione. Occorre quindi la selezione editoriale del gestore
prima di aprire la campagna; il codice non interpreta i vecchi campi del form come
varianti. Se vengono selezionate entrambe le varianti reali, restano richiedibili
contemporaneamente con quantità indipendenti.

## Website Builder e sicurezza

Usa le API della versione installata: `BaseOptionComponent`, `BuilderMany2One`,
`dataAttributeAction`, plugin `clean_for_save_processors` e
`public.interactions.edit`. L'anteprima autenticata non legge né modifica la
richiesta del visitatore e non contiene prezzi o quantità personali. Le quantità
dimostrative vivono solo nella proprietà runtime `input.value`.

Prima del salvataggio i contenuti dinamici diventano un placeholder. Il cleanup
dell'interazione ripristina il contenuto originale, rimuove listener, observer,
timer e subscription. Nessun ID DOM viene generato: duplicazione e spostamento
non richiedono rinumerazioni. Ogni istanza mantiene il proprio caricamento e
ignora le risposte obsolete.

Pubblico e portale non hanno accesso ORM alle campagne o alle righe. Commerciali
ed editor del website gestiscono i record nelle aziende consentite. L'endpoint
pubblico espone solo il frammento editoriale e le configurazioni del website/
azienda corrente. L'elevazione è limitata a questa lettura e alla campagna
predefinita; i prodotti sono riletti nell'ambiente del visitatore con dominio
catalogo nativo, pubblicazione e accessi. La selezione usa CSRF, validazioni,
revisioni e idempotenza del servizio condiviso; nessun nuovo endpoint di scrittura
o accesso alle richieste per ID numerico.

## Installazione e migrazione, solo sviluppo/staging

Effettuare un backup ordinario DB/filestore. Con i moduli delle issue precedenti
presenti, aggiornare il modulo funzionale e installare quello stagionale:

```sh
odoo -d <database_sviluppo> -u website_torrepulia_request,website_torrepulia_request_theme \
  -i website_torrepulia_request_campaign --stop-after-init
```

Riavviare Odoo per caricare i controller. Il bridge tema viene installato come
dipendenza se assente. **Non serve aggiornare il tema originale**. Per successivi
aggiornamenti della versione 20.0.1.1.0 usare
`-u website_torrepulia_request_theme,website_torrepulia_request_campaign`,
per inizializzare anche lo schema menu del tema storico tramite il bridge.

Una funzione dati idempotente agisce solo sui website Torrepulia abilitati e sulle
rispettive pagine `/prenotailtuoolio`. Sostituisce le sezioni stagionali note e
riconosce il vecchio form tramite i suoi campi. Conserva le altre sezioni Builder,
le traduzioni e l'eventuale fotografia della vecchia hero. Una struttura ambigua
interrompe la transazione. Il contenuto precedente è conservato per ogni vista/
lingua in `website.torrepulia_campaign_page_backup`, leggibile soltanto dagli
amministratori tecnici. Questo backup integra, senza sostituirlo, il backup DB.
Un secondo aggiornamento preserva lo snippet già modificato dal gestore.
Se la pagina manca, viene creata per quel website. Le pagine esistenti conservano
pubblicazione, metadati SEO, indicizzazione, dominio e HTTPS.

Il vecchio snippet non è più nel pannello di inserimento. Il controller rifiuta
gli invii del vecchio form riconosciuti da marcatore, campi quantità o oggetto,
anche da una pagina aperta prima dell'aggiornamento; il form contatti generale
continua il flusso nativo. Non vengono migrati vecchi lead né richieste inviate.
L'invio pubblico finale e i recapiti sono implementati in
`website_torrepulia_request`; questo modulo non aggiunge un invio intermedio.
La gestione protetta della precedente pagina `/richiesta-inviata`, compreso il
modulo contatti generale, è descritta nella matrice aggiornata dell'issue 9.

## Consegna e verifiche

Guida aggiornata per i gestori: [TORREPULIA_RICHIESTE_GUIDA.md](../../docs/TORREPULIA_RICHIESTE_GUIDA.md).
Matrice trasversale, aggiornamenti della pagina di ringraziamento e limiti:
[TORREPULIA_RICHIESTE_COLLAUDO.md](../../docs/TORREPULIA_RICHIESTE_COLLAUDO.md).

Elenco file e risultati effettivi in [QA.md](QA.md) e
[test-results.txt](test-results.txt). Verifiche soltanto su
`torrepulia_request_test`; `odoo_dev` è stato soltanto letto. Nessun deploy in
produzione, email reale, pagamento o modifica alle giacenze/prezzi reali.

Browser non disponibile nella sessione: non sono stati prodotti screenshot né
verificata visivamente la pagina a dimensioni desktop/mobile. Gli stati zero,
uno e più prodotti sono verificati automaticamente e disponibili come anteprime
isolate nel Builder; questo non sostituisce i sei screenshot richiesti.


## Collegamento alla prenotazione dal catalogo — 21/10/2026

Versione 20.0.1.3.2: il servizio `_request_preorder_url()` abilita la CTA della
presentazione stock solo se la campagna predefinita di questo website è aperta
secondo stato e date native del modello. Riutilizza la lettura pubblica
circoscritta per website/azienda già esistente, senza nuove ACL pubbliche.
Non limita il catalogo, non modifica le righe e non crea documenti commerciali.


## Form e riepilogo integrato — 21/10/2026, versione 20.0.1.4.0

La pagina segue la sequenza formati → recapiti e riepilogo integrato. Rimosso il
pulsante «Completa la tua prenotazione». Il riepilogo stagionale non duplica le
miniature, i controlli quantità o il comando Rimuovi: elenca nome/configurazione,
quantità e subtotale server nel box destro, con privacy e invio. Per modificare
le quantità si usano le card in alto; il riepilogo esteso resta disponibile
nell'header per gestire tutti i prodotti e le configurazioni della selezione.

Il layout è 60/40 su desktop, a colonna singola sotto 768 px. Telefono e CAP o
Città sono obbligatori in questa pagina; `/torrepulia/campaign/submit` li valida
prima di delegare al servizio condiviso di invio. Nessuna creazione ordini,
nuovo calcolo prezzi o variazione ai controlli di sessione, captcha e idempotenza.

L'aggiornamento rimuove dalle pagine salvate solo eventuali elementi riconosciuti
dall'attributo obsoleto `data-campaign-review`, tramite la migrazione circoscritta
e idempotente già esistente. Non sostituisce hero, fotografie o testi del gestore.
Il riepilogo personale rimane caricato privatamente e non fa parte del contenuto
salvato nel Builder. [Report](../../docs/qa-20261021-seasonal-summary/REPORT.md).


## Copy e visual bullet — 21/10/2026, versione 20.0.1.5.0

Sopra i prodotti compare una sola lista di tre icone SVG outline: prezzo bloccato,
filiera protetta, zero anticipo. La lista è orizzontale da 768 px, verticale e
centrata sotto tale soglia, con margini verticali di 24 px. Rimosse le rassicurazioni
ripetute nelle singole card e il paragrafo aggiuntivo del periodo di consegna.
I campi delle vecchie indicazioni rimangono nel database senza perdita di dati.

Aggiornare solo `website_torrepulia_request_campaign` con `-u`, quindi riavviare
Odoo e ricaricare gli asset. La migrazione interessa esclusivamente i website
Torrepulia e `/prenotailtuoolio`: sostituisce una volta il paragrafo della hero
riconosciuto dalla classe `tp-campaign-intro` e il testo editoriale della campagna
predefinita, incluse le traduzioni già salvate. Non cambia titolo, foto, colonne,
prodotti, SEO o altri testi Builder. I contenuti precedenti sono conservati nella
copia di sicurezza amministrativa `torrepulia_campaign_page_backup`.

Il marcatore `data-visual-bullets="1"` protegge le successive modifiche alla hero;
la chiave `visual_bullets_copy_v1` protegge quelle al testo della campagna.
Il testo sotto H2 resta modificabile in Website → Campagne olio nuovo → Testo
editoriale; il riferimento 2026/2027 va adattato per la prossima campagna.
Le affermazioni commerciali sono il copy approvato: non bloccano tecnicamente
prezzi e non modificano le condizioni dei preventivi nativi.

Evidenze e limiti: [report](../../docs/qa-20261021-seasonal-bullets/REPORT.md).


### Banner garanzie — versione 20.0.1.5.1

Le tre icone sono racchiuse in `.tp-campaign-benefits-banner`: fondo #f4f2ee,
max 900 px, centrato con margine laterale, padding 20/40 px e raggio 8 px.
Icone outline verdi 32 px; «Zero anticipo» usa una spunta cerchiata. Disposizione
orizzontale da 768 px e verticale centrata sui telefoni. La descrizione dista
32 px dal banner, che precede le card di 40 px. Hero: margine inferiore del
titolo 24 px e interlinea 1.2; H2 formati: margine inferiore 20 px.

Aggiornare `website_torrepulia_request_campaign` con `-u` e riavviare Odoo/asset.
Non richiede altre migrazioni dei contenuti: il banner viene renderizzato a
runtime; gli stili della hero si applicano anche ai blocchi già salvati.
Copy, prodotti e personalizzazioni editoriali restano quelli configurati.
[Report e screenshot](../../docs/qa-20261021-seasonal-banner/REPORT.md).


## Modalità mista — 22/10/2026, versione 20.0.1.6.0

La vetrina si apre in modalità `request` e nella nuova modalità mista `hybrid`.
In modalità mista `_torrepulia_preorder_product_url()` restituisce
`/prenotailtuoolio` per i prodotti e le varianti della campagna predefinita aperta:
il catalogo mostra «Prenota» al posto dell'aggiunta al carrello e la selezione
accetta solo quelle configurazioni. Chiusa la campagna, i prodotti tornano al
comportamento nativo e le bozze già composte non sono più inviabili.
`_request_preorder_url()` restituisce un collegamento solo quando il website usa
una modalità con selezione attiva. Test: `tests/test_hybrid.py`.
