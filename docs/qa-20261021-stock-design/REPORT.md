# Disponibilità unificata e correzione Website Builder — 21/10/2026

Consegnato su **localhost:8069**, database **torrepulia_cinematic_install**.
Versioni installate: richiesta **20.0.1.11.0**, bridge tema **20.0.1.3.1**,
campagna **20.0.1.3.2**. [Moduli](modules.txt), [aggiornamento](upgrade-final.log).
Le date dei log tecnici sono UTC e possono riportare il 20/10, mentre la data
locale della consegna è il 21/10 (Europe/Rome).

## Risultato

Catalogo, snippet «Scegli il formato» e dettaglio prodotto mostrano lo stesso
schema: stato discreto color terracotta, testo del campo nativo **Messaggio per
esaurito**, pulsante verde **PRENOTA IL NUOVO RACCOLTO**. Eliminati sfondo rosso,
cornice e pulsanti annidati a pillola. La CTA occupa la larghezza disponibile,
ha altezza minima 52 px e angoli 3 px, coerenti con l'aggiunta alla richiesta.

Il campo HTML originale non viene riscritto. La proiezione server separa testo
e collegamenti, eliminando gli stili inline dalla presentazione e senza
trasformare il grassetto in asterischi visibili. I link informativi diversi dalla
prenotazione restano disponibili. Il vecchio link alla pagina stagionale non
viene duplicato accanto alla nuova CTA.

La CTA dipende dalla campagna predefinita **aperta** del website, verificata sul
server con stato, date e isolamento website/azienda. Compare anche se nel campo
messaggio non è stato inserito un pulsante HTML; senza campagna, con campagna
chiusa, futura o scaduta, non compare. Nessuna nuova lista di prodotti ammessi
al catalogo; la pagina stagionale conserva la propria selezione editoriale.

Il dettaglio riceve la stessa proiezione nella risposta nativa della combinazione.
Il template frontend viene esteso nell'addon, conservando il percorso standard
quando la modalità richiesta è disattivata. Stock, varianti, flag **Vendi quando
esaurito** e quantità rimangono nativi. Se la CTA stagionale è disponibile, il
pulsante di notifica stock viene nascosto per evitare una seconda azione primaria.

## Difetto specifico dell'editor

Gli stili precedenti dipendevano dagli attributi del body aggiunti alla risposta
pubblica. Nell'editor quella condizione poteva mancare e riemergeva il
posizionamento nativo delle azioni sopra l'immagine, con dimensioni e forme
inadatte al componente richiesta. Gli stili ora dipendono dalla presenza del
componente: valgono anche nell'iframe Builder, mentre le pagine standard senza
componente mantengono gli stili nativi.

Verificato sull'editor reale dello shop, prima e dopo hover, e sullo snippet in
una copia temporanea della homepage. Nessun pulsante sopra la fotografia.
Salvataggio e ricaricamento della copia riusciti; i frammenti runtime e le
quantità personali non vengono registrati nell'architettura della pagina.

## Matrice dei controlli effettivamente eseguiti

| Scenario | Esito | Evidenza |
| --- | --- | --- |
| Catalogo a 360, 390, 768, 1440 px | Superato | [Misure](checks.json), nessun overflow orizzontale |
| CTA a tutta larghezza e allineate in basso | Superato | Asserzioni sui rettangoli delle card; [desktop](shop-1440.png), [mobile](shop-390.png) |
| Messaggio senza sfondo/cornice rossa | Superato | Bordi zero, testo e azione separati |
| Snippet desktop e mobile | Superato | [desktop](formats-1440.png), [mobile](formats-390.png) |
| Dettaglio prodotto desktop e mobile | Superato | [desktop](product-1440.png), [mobile](product-390.png); nuova presentazione e aggiunta nativa nascosta per esaurito |
| Campagna aperta/chiusa/futura/scaduta e altro website | Superato | Test Odoo del collegamento stagionale |
| Campo messaggio vuoto e grassetto HTML | Superato | CTA con campagna aperta anche senza HTML; nessun asterisco generato dal grassetto |
| Altri link informativi configurati | Superato | Test della proiezione server, URL e didascalia conservati |
| API nativa combinazioni con dati della presentazione | Superato | Test HTTP sul prodotto esaurito |
| Modalità standard, stock, varianti, prezzi nascosti | Superato | Regressione TestCommerceHttp e TestThemeRequestCommerce |
| Builder shop e hover | Superato | [Screenshot](builder-shop.png), misure prima/dopo hover e azioni sotto le immagini |
| Builder snippet | Superato | [Screenshot](builder-formats.png), salvataggio e ricaricamento su copia temporanea |
| Assenza di contenuti personali salvati | Superato | Architettura riletta dal server: assenti `tp-request-stock-message` e CTA runtime |
| Nessuna modifica alla selezione dal Builder | Superato | Zero chiamate `/torrepulia/request/update` durante il collaudo editor |
| Errori JavaScript e RPC | Superato | Nessun errore nel percorso conclusivo |
| Pulizia dei dati temporanei | Superato | [cleanup-checks.json](cleanup-checks.json): pagina/view rimosse, utente archiviato e password ruotata, credenziali private eliminate |
| Email, pagamenti, invio CRM, accettazione preventivi | Non rieseguiti | Fuori dall'ambito della presentazione; nessun invio o pagamento reale |

**42/42 test JavaScript passati:** [node-tests.log](node-tests.log).
**17 scenari Odoo distinti passati:** 9 in [odoo-tests.log](odoo-tests.log),
8 in [detail-tests.log](detail-tests.log). Dopo l'ultima correzione al testo e
alla CTA, i due test coinvolti sono stati rieseguiti: **2/2 passati** in
[notice-tests-final.log](notice-tests-final.log), senza sommarli ai 17 distinti.
Scansione UI senza rilievi: [design-detect.json](design-detect.json).

Il primo controllo automatico del salvataggio confrontava la traduzione errata
della vista; il test è stato corretto per rileggere la lingua dell'editor e
rieseguito con esito positivo. Un avvio browser immediatamente dopo il riavvio
ha trovato il servizio non ancora pronto; l'esecuzione conclusiva è partita
dopo la verifica di disponibilità HTTP. Questi tentativi non sono presentati
come collaudi riusciti. Script riproducibile: [browser_qa.py](browser_qa.py).

## File modificati

`custom/website_torrepulia_request/`:

- `__manifest__.py`
- `models/commerce.py`
- `views/commerce.xml`
- `static/src/scss/commerce.scss`
- `static/src/js/commerce.js`
- nuovo `static/src/xml/availability.xml`
- `tests/test_commerce.py`
- `README.md`

`custom/website_torrepulia_request_theme/`:

- `__manifest__.py`
- `views/commerce.xml`
- `tests/test_commerce.py`
- `README.md`

`custom/website_torrepulia_request_campaign/`:

- `__manifest__.py`
- `models/campaign.py`
- `tests/test_campaign.py`
- `README.md`

Documentazione: `docs/TORREPULIA_RICHIESTE_GUIDA.md` e questa cartella QA.

## Aggiornamento e dati

Backup del database prima dell'intervento, fuori repository:
`../backups/torrepulia_before_stock_design_20261021.dump`.
Non sono necessarie migrazioni di schema o riscritture delle pagine del gestore.
Sono stati aggiornati esclusivamente gli addon dedicati. Nessuna modifica al
core o al tema originale, a prezzi, giacenze, flag prodotto, dominio, HTTPS o
indicizzazione. I nastri e i badge editoriali salvati restano configurazioni del
gestore: non vengono cancellati né corretti automaticamente.

Sul solo ambiente di sviluppo, a processo web fermo:

```sh
odoo -d torrepulia_cinematic_install \
  -u website_torrepulia_request,website_torrepulia_request_theme,website_torrepulia_request_campaign \
  --stop-after-init --no-http --max-cron-threads=0
```

Riavviare Odoo e ricaricare gli asset nel browser. La lettura della campagna
riutilizza l'elevazione circoscritta già presente, con filtro website/azienda;
nessuna ACL pubblica CRM o richieste viene aggiunta. Nessuna dipendenza mancante
nell'ambiente locale. Nessun deploy in produzione.
