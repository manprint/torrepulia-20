# Torrepulia — base delle richieste di preventivo

Modulo funzionale `website_torrepulia_request`, versione `20.0.1.9.0`.

Il modulo contatti include «CAP o Città», libero e facoltativo (massimo 256
caratteri). All'invio viene anteposto alle note della richiesta e alla descrizione
CRM; non crea contatti né esegue validazioni stradali. Le note del cliente restano
limitate a 5000 caratteri; il confine interno ammette 5300 caratteri per ospitare
anche l'etichetta e l'area normalizzata, senza troncare le note.
Il collegamento nell'header apre una sidebar modale accessibile con prodotti,
quantità e importi nativi quando abilitati. «VAI AL RIEPILOGO» apre il percorso
centralizzato; senza JavaScript il collegamento conserva il suo normale href.

Revisione UI del 20 ottobre: controlli quantità tondi condivisi fra catalogo e
snippet formati, selezione esplicita delle varianti native semplici e conferma
con quantità appena aggiunta e subtotale calcolato dal server. Configurazioni
complesse continuano sulla scheda prodotto, conservando la quantità desiderata.
La raccolta rimane distinta dal carrello e non crea ordini durante la selezione.
Dipendenze: `website_sale` e `sale_crm` (che portano CRM e Vendite).

## Perimetro di questa issue

Configurazione per website, raccolta privata distinta dal carrello, modelli,
ACL/regole, transizione finale verso CRM e collegamenti ai preventivi nativi.
Sono disponibili il protocollo HTTP pubblico con CSRF, il servizio frontend unico
`torrepulia.request` e il binding condiviso per i componenti delle cinque superfici.
Contratti, operazioni e integrazione sono descritti in [SELECTION.md](SELECTION.md).
Catalogo, scheda prodotto, widget commerciali nativi e header ora usano la
selezione condivisa. L'aggiunta mostra una conferma senza interrompere la scelta;
i prodotti configurabili richiedono il passaggio esplicito sulla scheda.
La pagina `/la-tua-richiesta` permette di rivedere e modificare la selezione e
inviare la richiesta con nome/email, telefono e note facoltativi, privacy e
controlli CAPTCHA nativi. L'invio finale crea una sola opportunità CRM; la conferma
è protetta dalla sessione. Dettagli, aggiornamento e verifiche in
[QA-review.md](QA-review.md).
L'elaborazione finale prepara una selezione successiva vuota, collega il website,
le note e l'origine CRM, configura una fase iniziale aperta e persiste le notifiche
al team e al cliente. Preparazione e invio email sono separati dalla ricezione
transazionale. Dettagli, gestione degli errori e aggiornamento in
[QA-submission.md](QA-submission.md). La validazione telefono usa il servizio
nativo `phone_validation` con `phonenumbers` (dipendenza Python esplicita).
Il commerciale può ora usare «Prepara preventivo» dalla richiesta o dalla scheda
Richieste website dell'opportunità. Il cliente viene scelto esplicitamente e
Vendite ricalcola prezzi/condizioni; il preventivo resta in bozza. I preventivi
esistenti vengono riaperti, le revisioni richiedono una motivazione. I percorsi
di conferma manuale, firma e pagamento rimangono nativi. Dettagli, file e prove in
[QA-quotation.md](QA-quotation.md).
Prezzi nascosti: rimozione dalle risposte HTML/JSON pubbliche, incluse copie
Builder, frammenti AJAX e dati strutturati. Prezzi visibili: calcoli commerciali
nativi con listino, imposte, valuta e UoM del contesto corrente.

Il tema `website_torrepulia_theme` resta responsabile di grafica, snippet e
contenuti editoriali. Non è una dipendenza di questa base e nessun suo file viene
aggiornato. Il modulo opzionale `website_torrepulia_request_theme` integra i suoi
formati AJAX; si installa automaticamente quando entrambe le dipendenze sono
presenti. Non richiede di aggiornare/riprovisionare il tema. Il modulo opzionale
`website_torrepulia_request_campaign` sostituisce il form stagionale storico con
la vetrina condivisa e ne disabilita l'invio CRM diretto. Configurazione, migrazione
circoscritta e risultati sono descritti nel suo [README](../website_torrepulia_request_campaign/README.md).
Non viene creato un secondo elenco globale di prodotti ammessi.

## Verifica ambiente

Sorgente effettivo nel container locale: Odoo **20.0-20260926**, commit
`7434faa93558d4f46fdda77acd1be4dfc663ea7c`; PostgreSQL 17.
Il repository include i dati sotto `odoo/`, non un checkout del core.
Il database locale `odoo_dev` contiene `website`, `website_sale`, `crm`,
`sale_crm` e il tema (versione registrata `20.0.3.1.2`, manifest repository
`20.0.3.6.0`). Non è stato aggiornato per eseguire questi test.

API lette nel sorgente installato:

- `website_sale/models/website.py`: `sale_product_domain`, `has_ecommerce_access`;
- `website/models/res_config_settings.py`: website selezionato e azienda correlata;
- `product/models/product_template.py`: `_is_combination_possible`;
- `sale/models/sale_order_line.py`: `_get_available_uoms`, valori senza variante e personalizzati;
- `sale_crm/models/sale_order.py`: `opportunity_id`;
- `sales_team/models/crm_team.py`: membri, responsabile e azienda;
- ORM Odoo 20: `models.Constraint`, `check_access`, `fields.Domain`.
- `base/models/ir_access.py` e `crm/security/ir.access.csv`: Odoo 20 unifica
  permessi e domini in `ir.access`; nessun uso dei vecchi `ir.rule`/`ir.model.access`.

## Configurazione

Website → Configurazione → Impostazioni, selezionare il website e cercare
“Torrepulia — Richieste di preventivo”. Ogni campo è salvato sul website:

- modalità `shop` (default) / `request`;
- prezzi visibili (default sì); la futura UI deve interrogare
  `_torrepulia_request_prices_visible()` prima di renderizzare importi e metadati;
- team destinatario obbligatorio in modalità richiesta, attivo e della stessa
  azienda (oppure condiviso);
- assegnatario facoltativo, membro o responsabile del team, interno, attivo e
  abilitato all’azienda del sito; il selettore mostra solo gli utenti coerenti;
- destinazione locale iniziale `/la-tua-richiesta`, restituita esclusivamente da
  `_torrepulia_request_url()`; nessun componente deve duplicare il percorso;
- conservazione bozze: **30 giorni dall’ultima modifica**, configurabile 1–365.
- quantità minima, massima e passo per configurazione (default 1, 1000 e 1),
  sempre compatibili con la precisione nativa della UoM. Zero rimuove una riga.

## Modelli e sicurezza

`torrepulia.request`: sequenza globale univoca `TPR/…`, website, azienda storica,
lingua, bozza/inviata, hash SHA-256 del segreto di sessione, attività, contatto
autenticato, dati forniti all’invio, righe, opportunità e preventivi, origine e UTM.
`torrepulia.request.line`: variante `product.product` effettiva, quantità, UoM
nativa, valori `no_variant`, testi personalizzati indicizzati dai PTAV nativi.
Non memorizza né modifica prezzi, listini, scorte o disponibilità.
Il protocollo aggiunge identità pubblica opaca, revisione, fotografia di selezione
e registro privato `torrepulia.request.operation` per deduplicare i ritentativi.

All’invio vengono conservati anche nomi, codici, attributi e UoM con fattore
di conversione: una successiva modifica al catalogo non cambia la fotografia.
Richiesta e righe inviate non sono modificabili/eliminabili tramite ORM, anche
dal commerciale. Nessun token o ID numerico costituisce un URL pubblico.

Pubblico e portale non hanno ACL sui due modelli. I commerciali vedono solo
richieste assegnate a loro o al loro team; i responsabili Vendite vedono tutte le
richieste nelle aziende consentite. Le regole sulle righe seguono la richiesta.
L’hash della sessione è riservato agli amministratori tecnici.

Elevazioni limitate: sequenza dedicata; ricerca della bozza per hash + website +
azienda + stato + scadenza; creazione bozza con whitelist di valori; lettura della
configurazione destinatari; creazione finale della sola opportunità validata.
Le letture di catalogo e configurazioni prodotto restano nell’ambiente del
visitatore. Non sono assegnate ACL CRM/contatti aggiuntive.

## Contratto per i successivi adattatori pubblici

Tutti i metodi che seguono sono privati e non invocabili via RPC Odoo.
Il controller deve usare `request.env.website` nell’ambiente del visitatore e
la vera `request.session`, senza accettare website, richiesta o partner dal client.
Le modifiche della selezione pubblica passano esclusivamente dal protocollo di
[SELECTION.md](SELECTION.md): `_set_selection` è il primitivo interno, non un
percorso alternativo che consenta di saltare revisione e idempotenza.

1. `_torrepulia_session_request(request.session, create=True)` recupera/crea una
   bozza mediante segreto casuale da 256 bit, separato per website. Senza `create`
   non crea nulla. Modalità standard o catalogo riservato non accessibile: vuoto.
2. Sulla bozza risolta, `_set_selection(website, product, quantity, uom=…,
   no_variant_values=…, custom_values=…, line=…)` verifica dominio nativo,
   pubblicazione, azienda, variante, combinazione, UoM e valori personalizzati.
   Passare prodotto/UoM/PTAV nell’ambiente del visitatore. `line` deve essere
   risolta fra le righe della bozza; quantità zero rimuove solo quella riga.
   Le aggiunte dal catalogo rispettano la disponibilità nativa e il flag
   «Vendi quando esaurito». Le quantità della campagna stagionale restano
   prenotazioni e non riservano giacenze.
3. Solo al submit finale, `_submit(website, contact)` ricontrolla le righe e
   richiede nome/email valida. `contact` ammette `contact_name`, `email`, `phone`,
   `address`, `notes`. Il contatto autenticato deriva dall’utente attuale;
   l’email digitata non viene usata per cercare/associare contatti esistenti.
   Origine/UTM possono essere valorizzate prima dell’invio solo da attribuzione
   server attendibile, mai da un dizionario di campi ORM accettato dal visitatore.
4. L’invio crea una sola opportunità e due intenzioni di notifica persistenti,
   senza contatto anonimo, ordine o invio email sincrono. Il cron prepara le email
   nella coda Odoo; la spedizione SMTP resta al gestore email nativo.
   I lock della richiesta serializzano modifica/invio/pulizia. Un secondo invio
   sulla medesima richiesta viene rifiutato. Il successivo recupero con `create`
   genera una nuova bozza e ruota il segreto; la fotografia inviata resta intatta.

Gli adattatori HTTP implementati mantengono CSRF nativo, validano gli input e
serializzano solo una whitelist di dati della selezione. Validazione privacy,
antispam, messaggi e redirect appartengono all’issue del modulo pubblico.
Gli errori di invio devono provocare rollback della transazione; non intercettare
eccezioni per poi commettere aggiornamenti parziali.

Il CRM mostra la relazione inversa alla richiesta. `sale.order.torrepulia_request_id`
collega solo una richiesta inviata della stessa azienda e della stessa opportunità.
La generazione assistita del preventivo precompilato è un successivo adattatore
commerciale: deve usare i normali campi e calcoli di `sale.order.line` e le
condizioni commerciali correnti, senza riutilizzare prezzi editoriali.
Conferma manuale o accettazione online del preventivo restano flussi nativi.

## Pulizia

Cron giornaliero, massimo 500 bozze per website per esecuzione, con controllo
scadenza anche dopo l’acquisizione del lock. Elimina solo `state=draft` con
`last_activity` precedente alla durata configurata. Non tocca richieste inviate,
opportunità, preventivi, contatti o documenti contabili. Anche prima del cron una
sessione scaduta non permette il recupero della bozza. Aumentare la frequenza del
cron se il volume supera stabilmente il limite di 500 bozze scadute al giorno.

## Installazione e aggiornamento (solo sviluppo)

Con backup ordinario DB/filestore, ricostruire l’immagine se gli addon sono
copiati dal Dockerfile. Nell’ambiente di sviluppo con bind mount non serve rebuild.

```sh
docker compose run --rm odoo -d <database_sviluppo> -i website_torrepulia_request --stop-after-init
# Aggiornamenti successivi:
docker compose run --rm odoo -d <database_sviluppo> -u website_torrepulia_request --stop-after-init
```

Riavviare il servizio Odoo per caricare i modelli. Nessuna migrazione di dati o
contenuti Builder richiesta; i website esistenti ricevono modalità standard.
Non convertire automaticamente vecchie opportunità/form stagionali in richieste.
Nessun deploy in produzione eseguito o previsto da questi comandi di verifica.

## Test riproducibili

Su un database di test dedicato, con SMTP di prova/disabilitato:

```sh
odoo -d <database_test> -i website_torrepulia_request --without-demo \
  --test-enable --test-tags=/website_torrepulia_request --stop-after-init
# Dopo modifiche utilizzare -u invece di -i.
```

Gli indirizzi dei test terminano in `.invalid`; le connessioni SMTP sono
intercettate e non vengono eseguiti invii reali o pagamenti. Report storico della base in [QA.md](QA.md); risultati aggiornati del
servizio condiviso e inventario della nuova issue in [QA-selection.md](QA-selection.md).
Integrazione catalogo, file modificati, aggiornamento e verifiche:
[QA-commerce.md](QA-commerce.md).

Blocco server del checkout autonomo, audit delle route installate, conservazione
dei carrelli, recuperi e ripristino per website: [QA-checkout.md](QA-checkout.md).

Guida dei gestori e collaudo dell'intero percorso:
[guida operativa](../../docs/TORREPULIA_RICHIESTE_GUIDA.md) e
[matrice dei controlli](../../docs/TORREPULIA_RICHIESTE_COLLAUDO.md).


### Disponibilità del catalogo (20.0.1.10.0)

Per prodotti con inventario tracciato, senza «Vendi quando esaurito», il catalogo,
la scheda prodotto, i formati del tema e i prodotti consigliati non offrono
l'aggiunta quando esauriti. Riutilizzano `_is_sold_out()` nativo, con il magazzino
del website quando `website_sale_stock` è installato. Nessun nuovo campo stock.
Il «Messaggio per esaurito» HTML configurato sul prodotto appare anche nella
card, con avviso rosso e pulsanti che vanno a capo. Non viene generato un invito
commerciale diverso da quello configurato dal gestore.

L'operazione `add` del servizio condiviso rivalida l'esaurimento sul server,
dopo il controllo di idempotenza. `set_configuration` rimane il percorso di
prenotazione stagionale, senza vincoli di disponibilità fisica; il riepilogo
non cancella le selezioni esistenti. La selezione non riserva stock e non è
una garanzia di disponibilità fino alla qualificazione commerciale.
Un vecchio carrello ecommerce non viene sottratto alla disponibilità della
richiesta separata. In modalità standard rimangono i controlli nativi.

Aggiornare anche `website_torrepulia_request_theme` (20.0.1.2.2) e riavviare Odoo.
Non aggiornare il tema originale né le pagine editoriali per questa modifica.
Evidenze e limiti: [report disponibilità](../../docs/qa-20261020-stock/REPORT.md).


### Disponibilità: presentazione unificata (21/10/2026, 20.0.1.11.0)

Il messaggio di esaurimento nel catalogo, nello snippet e nella scheda prodotto
usa ora testo libero senza contenitore rosso e un pulsante verde rettangolare.
Il testo deriva sempre dal campo nativo «Messaggio per esaurito». L'HTML salvato
non viene riscritto: il componente estrae testo e collegamenti senza applicare
stili inline, classi o forme del vecchio pulsante. Gli altri link configurati
restano disponibili come collegamenti informativi.

Il pulsante «PRENOTA IL NUOVO RACCOLTO» viene mostrato solo quando il modulo
campagna restituisce una
campagna predefinita aperta per il website. Il modulo base non presume che
esista una campagna attiva. Chiusura e date vengono verificate sul server.
Aggiornare i testi editoriali se non più pertinenti dopo la chiusura.

La combinazione nativa della scheda prodotto trasporta la stessa proiezione
editoriale; l'estensione del template frontend mantiene i controlli nativi di
stock/varianti e il comportamento standard fuori modalità richiesta. Quando
il preorder è disponibile, il comando nativo di notifica stock viene nascosto
per non introdurre una seconda azione principale.

Gli stili delle azioni sono collegati al componente della richiesta, non agli
attributi del body aggiunti solo nelle risposte pubbliche: valgono quindi anche
nel Website Builder. Non vengono salvate quantità o frammenti runtime nelle
pagine del gestore. [Report](../../docs/qa-20261021-stock-design/REPORT.md).


### Riepilogo stagionale compatto (21/10/2026, 20.0.1.12.0)

Il frammento privato `/torrepulia/request/form?layout=campaign`, quando il modulo
campagna è installato, produce il layout stagionale: recapiti a sinistra e un
solo elenco prodotti nel riepilogo a destra. Non crea una seconda selezione o
un carrello ecommerce. I controlli delle card e l'elenco usano il servizio di
richiesta condiviso e i subtotali nativi della preview server, senza ricaricare
la pagina. L'elenco comprende anche prodotti esterni alla campagna.

La pagina estesa `/la-tua-richiesta` mantiene immagini, modifica quantità e
rimozione. Il form stagionale invia al percorso dell'addon campagna, che richiede
telefono e CAP o Città e riutilizza l'invio transazionale/idempotente esistente.
Sul riepilogo esteso quei due campi restano facoltativi. CAP o Città rimane testo
libero e confluisce nelle note CRM. Se i prezzi sono nascosti, la versione
stagionale non mostra importi e dice «Nessun pagamento richiesto oggi».

[Report, file modificati e verifiche](../../docs/qa-20261021-seasonal-summary/REPORT.md).
