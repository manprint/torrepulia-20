# Issue 7 — Prepara preventivo

## Comportamento consegnato

Il pulsante «Prepara preventivo» è disponibile nelle richieste inviate e nella
tabella Richieste website dell'opportunità. I preventivi collegati rimangono
visibili nella richiesta e negli smart button nativi CRM. Il preventivo espone
la richiesta originale e l'eventuale preventivo precedente nella nuova scheda
«Richiesta originale».

Al primo utilizzo si apre un wizard con cliente obbligatorio, azienda e recapiti
ricevuti. Il cliente predefinito è solo quello già qualificato sull'opportunità
o il contatto autenticato originario. Per richieste anonime senza qualificazione
non c'è associazione automatica per email. Il widget Contatti permette di
scegliere o creare esplicitamente un cliente con i permessi nativi; i recapiti
ricevuti sono proposti come valori modificabili durante la creazione.

«Prepara e rivedi» crea un `sale.order` nativo in bozza, collega opportunità e
richiesta e lo apre nel modulo Vendite. Non invia il preventivo, non lo conferma,
non crea consegne, fatture o pagamenti. L'associazione esplicita del cliente può
aggiornare il cliente qualificato dell'opportunità; non modifica il contatto
autenticato, i recapiti o le righe fotografate della richiesta.

L'azienda viene dalla richiesta autorizzata. Il contesto viene preparato tramite
`crm.lead._prepare_opportunity_quotation_context()`; Vendite determina listino
del cliente, valuta, indirizzi, posizione fiscale, imposte e condizioni di
pagamento. Il commerciale li può controllare e modificare nel preventivo prima
dell'invio. Nessun `price_unit`, sconto, imposta o importo della ricevuta pubblica
viene copiato nelle righe. I prezzi correnti sono calcolati dai campi nativi di
`sale.order.line`, anche per quantità, unità alternative e attributi senza variante.
Il contesto di creazione conserva solo i default nativi CRM e lingua/aziende
dell'operatore: default economici RPC arbitrari non diventano prezzi contrattuali.

Vengono trasferiti variante effettiva, quantità, `product_uom_id`, attributi
senza variante e `product.attribute.custom.value`. Righe diverse rimangono
distinte. I nomi e le descrizioni commerciali del preventivo sono quelli nativi;
la fotografia ricevuta resta disponibile per confronto, anche dopo modifiche del
commerciale. Prodotti archiviati/non vendibili, configurazioni non più valide,
unità rimosse o conversioni modificate producono un errore, senza saltare righe
o scegliere altri prodotti. La pubblicazione attuale sul sito non impedisce di
quotare internamente un prodotto ancora vendibile già richiesto dal cliente.
Le configurazioni combo non rappresentate dal protocollo di richiesta vengono
rifiutate esplicitamente, non trasformate in righe incomplete.
La tabella della richiesta mostra nome, unità e configurazioni ricevuti ricavati
dalla fotografia, affiancati al collegamento al prodotto corrente. Rinominare un
prodotto non cambia queste informazioni originali.

## Permessi e duplicazioni

Il codice di preventivazione non usa `sudo()`. Verifica il gruppo commerciale,
accesso alla richiesta, azienda attiva dell'operatore, modifica dell'opportunità,
creazione Vendite e lettura del cliente. L'ORM verifica inoltre compatibilità
aziendale di cliente, opportunità e ordine. I wizard sono transient privati
dell'operatore, senza ACL per pubblico o portale e con regola aziendale.

L'elenco degli ordini collegati viene cercato con SQL circoscritto alla sola
richiesta già autorizzata, poi verificato con `check_access('read')`: un ordine
riassegnato e non leggibile non viene ignorato creando un duplicato. La ricerca
include anche ordini già confermati, così ripetere «Prepara preventivo» non apre
un secondo processo commerciale. Se esiste un preventivo/ordine non annullato,
viene aperto il più recente. Se sono tutti annullati, occorre motivare una nuova
preparazione.

«Nuovo preventivo / revisione» è un'azione separata, con motivazione obbligatoria.
Collega il preventivo precedente e registra origine/motivazione nel chatter del
nuovo preventivo e dell'opportunità. Il risultato del wizard viene memorizzato:
un doppio clic sullo stesso wizard restituisce lo stesso documento. Due finestre
di revisione aperte sulla stessa base convergono alla revisione già preparata;
per un'ulteriore revisione occorre aprire intenzionalmente un nuovo wizard dalla
versione corrente. Le versioni precedenti non vengono annullate automaticamente.

I blocchi PostgreSQL proteggono wizard e richiesta. Con isolamento REPEATABLE READ
un blocco in sola lettura non aggiorna lo snapshot: viene incrementato il solo
campo tecnico privato `quotation_lock_version`, in modo che Odoo possa ritentare
l'intera transazione su uno snapshot aggiornato. Questo metadato backend non è
una modifica alle righe, ai recapiti o alla fotografia della richiesta ricevuta.
Nessun bypass del guardiano di immutabilità per i dati commerciali.

## Accettazione e seguito nativo

Percorso email: il commerciale registra l'accordo con una nota nel chatter del
preventivo e usa la conferma standard. Non è previsto un nuovo stato di approvazione.

Percorso online: controllare cliente e condizioni, scegliere Firma online e/o
l'acconto/pagamento richiesto tramite i campi nativi, poi inviare il preventivo
con l'azione standard Odoo. In questa build 20 il pagamento richiesto è regolato
da `prepayment_percent`/`prepayment_amount`; non esiste `require_payment`.
La firma e il pagamento legittimi confermano secondo il comportamento standard,
senza una seconda approvazione manuale Torrepulia.

È usato `assigned_website_id` nativo, verificato nel sorgente installato:
associa l'origine e l'URL del sito al preventivo senza segnalarlo come carrello
e-commerce (`website_id` rimane vuoto). Nessuna selezione pubblica viene
convertita in un carrello. Le route native `/my/orders/...` e `/payment/...`
rimangono escluse dalla politica prezzi pubblici e dal guardiano del carrello.
Anche con prezzi nascosti nel catalogo, il cliente autorizzato può vedere e
accettare il preventivo commerciale che gli è stato inviato.

Conferma ordine, consegne e fatture continuano nei moduli standard installati;
non sono aggiunti motori fiscali, di pagamento, di stock o di fatturazione.
Le opzioni native CRM/Vendite per opportunità senza richieste restano invariate.
Disattivare la modalità sul website non impedisce di lavorare internamente
richieste già ricevute.

## Ambiente e aggiornamento

Verificato Odoo **20.0-20260926**, sorgenti effettivi nel container sotto
`/usr/lib/python3/dist-packages/odoo/addons`. Nel database isolato erano installati
`account`, `payment`, `sale_stock`, CRM/Vendite e Website delle issue precedenti.
`payment_demo` è stato installato soltanto in `torrepulia_request_test` per le
prove con pagamenti fittizi; non è una dipendenza funzionale da installare in
produzione. Odoo 20 usa `payment.provider.is_live`, non il precedente campo `state`.
Le fixture Demo mantengono `is_live=False`.

Con backup DB/filestore, solo sviluppo/staging con SMTP intercettato:

```sh
odoo -d <database_sviluppo> -u website_torrepulia_request --stop-after-init
```

Riavviare il servizio Odoo. Nessuna nuova dipendenza funzionale rispetto alla
versione precedente. L'ORM aggiunge wizard e metadati di collegamento/revisione.
Non genera preventivi retroattivi, non modifica richieste o opportunità storiche
e non cambia contenuti Builder, prezzi o stock esistenti. Non occorre aggiornare
il tema originale. Nessuna modifica a dominio, HTTPS o indicizzazione dello staging.
`odoo_dev` e produzione non sono stati aggiornati.

## File di questa issue

Tutti sotto `custom/website_torrepulia_request/`:

- `__manifest__.py`: versione 20.0.1.5.0 e nuova vista.
- `models/__init__.py`, nuovo `models/quotation.py`: autorizzazione, wizard,
  creazione nativa, trasferimento configurazioni, duplicazioni e traccia revisione.
- `security/ir.access.csv`: wizard commerciale privato e isolamento aziendale.
- `views/request.xml`: azioni su richiesta e righe del tab CRM.
- Nuovo `views/quotation.xml`: wizard e collegamenti nel preventivo.
- `tests/__init__.py`, nuovi `tests/test_quotation.py`,
  `tests/test_quotation_portal.py`, `tests/test_quotation_accounting.py`.
- Nuovo `tools/quotation_concurrency_qa.py`: due scenari PostgreSQL reali.
- `README.md`, nuovo `QA-quotation.md`, nuovo `quotation-test-results.txt`.

## Verifiche e limiti

Comandi ed esiti effettivi in [quotation-test-results.txt](quotation-test-results.txt).
Superati **65 test Odoo**, con ripetizione finale dei **10 test nuovi**, **29 test
JavaScript** e **2 scenari PostgreSQL concorrenti**.
Tutte le prove usano solo `torrepulia_request_test`, contatti sintetici `.invalid`
e pagamenti Demo. SMTP è intercettato nei percorsi che inviano conferme. La prova
HTTP di firma usa il controller reale e una firma sintetica; la generazione PDF
è sostituita da un allegato di prova, non è un collaudo della resa del report.
La prova pagamento controlla sia la route transazione del portale sia il
post-processing nativo Demo, senza contattare circuiti reali.

Browser non disponibile: `apps: [], browsers: []`. Screenshot e verifica visiva
di pulsanti/wizard non eseguibili qui; le viste sono validate dall'aggiornamento
Odoo. Nessun deploy in produzione o messaggio reale ai clienti.
