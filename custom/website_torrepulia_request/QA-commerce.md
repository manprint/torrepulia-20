> Nota del 20/10/2026: questo documento descrive il collaudo storico.
> La politica di esaurimento del catalogo è stata aggiornata: ora rispetta
> «Vendi quando esaurito», mantenendo il preorder stagionale separato.
> Consultare [il report aggiornato](../../docs/qa-20261020-stock/REPORT.md).

# Issue 3 — catalogo, prodotto e header

## Implementazione

Ambiente verificato: Odoo 20.0-20260926, sorgente effettivamente installato nel
container; `website_sale`, CRM/Vendite, `website_sale_stock` e tema del repository.
Non sono state modificate API o viste del core.

Il servizio nativo `cart` viene esteso al punto comune `CartService.add`:
in modalità standard richiama esattamente il metodo originale; in modalità
richiesta usa `torrepulia.request`. Vale anche per acquisto immediato, wishlist,
prodotti consigliati, pulsanti dinamici e configuratori che usano quel servizio.
I controller carrello e la creazione carrello sono inoltre bloccati lato server
in modalità richiesta. La selezione non crea `sale.order` né riserva stock.

Il catalogo mostra il pulsante richiesta anche quando la disponibilità impedisce
l'acquisto online. Per varianti, attributi personalizzati o più UoM, il primo
passaggio apre la scheda; nessuna variante viene aggiunta implicitamente.
La scheda mantiene immagini, validità delle combinazioni, attributi e unità nativi;
le quantità della richiesta rispettano i limiti del website e non la giacenza.
Le varianti dinamiche sono risolte dall'API nativa dopo validazione esplicita.

La conferma non modale mostra nome variante, quantità aggiunta, successo,
«Continua a scegliere» e collegamento centrale «Rivedi la richiesta».
In caso di esito di rete incerto consente il ritentativo della stessa operazione.
Header desktop/mobile: link e nome accessibile, contatore aggiornato dallo stato
server; il carrello nativo non viene mostrato. Il riepilogo iniziale consente
modifica quantità, rimozione e svuotamento esplicito.

La policy di uscita è circoscritta al website in modalità richiesta. Adatta anche
le copie di header/pulsanti e importi materializzate dal Builder senza salvarle.
Non modifica viste o contenuti in database; una vera sessione editor autorizzata
con `enable_editor` riceve il documento originale. Il solo parametro pubblico non
aggira la policy. Backend, portale preventivi `/my/`, report e pagamenti nativi
sono esclusi dalla riscrittura. L'accettazione dei preventivi inviati resta nativa.

Con prezzi nascosti elimina contenitori importo, confronti, extra attributi,
metadata economici, tracking e offerte JSON-LD; preserva identità prodotto,
varianti, stock e valori degli attributi. Nessun prezzo fittizio o zero sostitutivo.
Con prezzi visibili il riepilogo usa `_get_combination_info` e `format_amount`:
nessun motore prezzi parallelo. Il totale indica soli prodotti, trasporto escluso.
Il bridge usa `_get_sales_prices` per gli stessi prodotti già scelti dal tema.

## File aggiunti/modificati per questa issue

Nel modulo `custom/website_torrepulia_request`:

- `__manifest__.py`: versione, viste e asset.
- `models/__init__.py`, `models/commerce.py`, `models/public_policy.py`:
  controllo catalogo, protezione carrello e policy di output pubblico.
- `controllers/__init__.py`, `controllers/commerce.py`: metadata, risoluzione
  varianti, anteprima con prezzi nativi, riepilogo e protezioni HTTP.
- `views/commerce.xml`: pulsanti shop/snippet e pagina di riepilogo iniziale.
- `static/src/js/commerce.js`: integrazione servizi/interazioni Odoo e conferma.
- `static/src/scss/commerce.scss`: header, conferma e riepilogo responsive.
- `tests/__init__.py`, `tests/test_commerce.py`, `tests/test_commerce.mjs`.
- `README.md`, `QA-commerce.md`, `commerce-test-results.txt`.

Nuovo modulo `custom/website_torrepulia_request_theme`:

- `__init__.py`, `__manifest__.py`.
- `controllers/__init__.py`, `controllers/commerce.py`.
- `views/commerce.xml`.
- `tests/__init__.py`, `tests/test_commerce.py`.
- `README.md`.

I file delle issue 1 e 2 restano inclusi nella directory del modulo, già presente
nel workspace come insieme non tracciato. Nessun file del tema originale viene
modificato da questa issue.

## Aggiornamento solo sviluppo/staging

Con backup DB/filestore e destinatari di prova:

```sh
odoo -d <database_sviluppo> -u website_torrepulia_request \
  -i website_torrepulia_request_theme --stop-after-init
```

Il bridge dipende dal tema: omettere `-i website_torrepulia_request_theme` nelle
installazioni che usano solo lo shop nativo. Riavviare Odoo per il codice Python
e rigenerare gli asset con l'aggiornamento modulo. Non occorre `-u` sul tema.
Non migra contenuti, non elimina bozze, non modifica prezzi o stock. Gli esistenti
website conservano la configurazione precedente; il default resta `shop`.
Un URL di riepilogo personalizzato deve puntare a una pagina esistente predisposta
con i binding condivisi; `/la-tua-richiesta` è la destinazione pronta all'uso.

I test di installazione/aggiornamento sono eseguiti esclusivamente sul database
isolato `torrepulia_request_test`; nessun deploy e nessun aggiornamento di `odoo_dev`.

## Verifiche e limiti

Risultati effettivi e comandi riproducibili in `commerce-test-results.txt`.
Esito finale: **33 test Odoo superati, 0 errori; 16 test JavaScript superati**.
I test coprono incremento e impostazione, ritentativi, isolamento, varianti e
valori personalizzati, quantità senza stock, fallback standard, header/pulsanti,
prezzi HTML/JSON/schema, confronto con prezzo nativo e conservazione dei contenuti
Builder, oltre alle regressioni ACL/CRM delle issue dipendenti.
Il detector della skill impeccable non ha rilevato segnalazioni (`[]`).

Nessun browser disponibile nella sessione: screenshot, verifica visiva mobile/
desktop, esecuzione degli asset nel browser e interazione completa con i dialoghi
nativi non eseguibili qui. I test Node usano dipendenze simulate e non sostituiscono
questa verifica. Il vecchio form campagna e il modulo pubblico di invio finale
restano per le rispettive issue; non vengono presentati come completati.
Nessuna email reale, pagamento o modifica di dominio/HTTPS/indicizzazione.
