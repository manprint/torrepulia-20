# Issue 8 — checkout autonomo e ripristino

## Ambiente verificato

Odoo **20.0-20260926**, sorgenti realmente presenti nel container in
`/usr/lib/python3/dist-packages/odoo/`; dispatcher nel pacchetto `odoo/http/`.
Ispezione e prove svolte il 18 ottobre 2026. Solo database isolato
`torrepulia_request_test`; nessun aggiornamento a `odoo_dev` o produzione.

Moduli verificati nel DB di prova:

| Modulo | Versione | Stato |
| --- | --- | --- |
| website | 20.0.1.0 | installato |
| website_sale | 20.0.1.1 | installato |
| website_sale_stock | 20.0.1.0 | installato |
| sale | 20.0.1.2 | installato |
| sale_crm | 20.0.1.0 | installato |
| crm | 20.0.1.9 | installato |
| payment | 20.0.2.0 | installato |
| payment_demo | 20.0.2.0 | solo QA, pagamenti fittizi |
| website_sale_loyalty | — | non installato |
| website_torrepulia_theme | 20.0.3.6.0 | installato |
| website_torrepulia_request | 20.0.1.6.0 | installato |
| website_torrepulia_request_theme | 20.0.1.0.0 | installato |
| website_torrepulia_request_campaign | 20.0.1.0.0 | installato |

## Audit del sorgente disponibile

Tutti i percorsi seguenti sono relativi a `odoo/addons/`.

| Sorgente | Route o comportamento verificato | Intervento |
| --- | --- | --- |
| website_sale/controllers/cart.py | `/shop/cart`, `/shop/cart/add`, `/shop/cart/quick_add`, `/shop/cart/update` | Il confine server precede i corpi dei controller; GET verso riepilogo, JSON-RPC rifiutato |
| Stesso file | Recupero `id/access_token` su GET `/shop/cart` può ripristinare o fondere righe e cancellare il vecchio carrello | Redirect prima della lettura del token e delle modifiche; nessuna fusione |
| website_sale/controllers/main.py | `/shop/checkout`, `/shop/address`, `/shop/address/submit`, `/shop/extra_info`, `/shop/payment`, `/shop/confirmation`, `/shop/print`, `/shop/print/invoice` | GET/HEAD 303 al riepilogo centrale; POST HTTP 409 con errore/redirect controllati |
| Stesso file | `/shop/payment/validate` può confermare un carrello gratuito durante GET | Blocco prima di `_validate_order`; nessuna conferma gratuita |
| Stesso file | `/shop/express_checkout`, `/shop/update_address` | JSON-RPC rifiutato prima di creare contatti o aggiornare documenti |
| website_sale/controllers/delivery.py | `/shop/delivery_methods`, `/shop/set_delivery_method`, `/shop/get_delivery_rate`, `/shop/express/shipping_address_change`, `/website_sale/set_delivery_date` | JSON-RPC rifiutato, nessun aggiornamento logistico del carrello |
| website_sale_stock/controllers/location_selector.py | `/website_sale_stock/set_pickup_location` | Modifica rifiutata |
| website_sale/controllers/website.py | `/website/form/shop.sale.order` | POST 409, nessun dato/allegato applicato al vecchio carrello |
| website_sale/controllers/reorder.py | `/my/orders/reorder` usa direttamente `Cart()`, aggirando una semplice ereditarietà del controller cart | Bloccata questa sola azione di riacquisto; il resto del portale resta nativo |
| website_sale/controllers/payment.py | `/shop/payment/transaction/<order_id>` | Blocco route e controllo dell'ordine realmente collegato alla transazione |
| sale/controllers/portal.py | `/my/orders/<order_id>/transaction`, `/accept`, `/decline` | Autorizzazione documento nativa; i token dei vecchi carrelli non autorizzano pagamento/firma/cancellazione nel flusso sospeso |
| payment/controllers/portal.py | Creazione transazione precede addebito e valori di elaborazione | Postcondizione ORM sotto savepoint prima che il chiamante elabori/addebiti il pagamento |
| website_sale/models/website.py | `_get_and_cache_current_cart` può recuperare, riassegnare e ricalcolare un carrello al login | In modalità richiesta restituisce recordset vuoto prima di tali operazioni, conservando il puntatore della sessione |
| Stesso file | `_cron_send_abandoned_cart_email` marca anche i carrelli scartati come già notificati | Esclusione dei website sospesi prima del raggruppamento e dei flag; algoritmo nativo restante conservato |
| website_sale/models/sale_order.py | `_cart_add`, `_cart_update_line_quantity`, `_validate_order`, recupero manuale/diretto | Protezione anche nel modello su carrelli appartenenti ai siti sospesi |

Sono riservati anche i prefissi di checkout `/shop/claimreward`, `/wallet/top_up`
e `/coupon` qualora venga installata la relativa estensione. Non sono dichiarati
collaudati i moduli aggiuntivi non installati. Le route native di listino e
configurazione dei prodotti rimangono disponibili per il contesto commerciale
del catalogo; l'assenza del carrello corrente evita modifiche ai vecchi carrelli.

Il tema originale `website_torrepulia_theme` mantiene responsabilità grafiche:
header in `views/cinematic.xml`, navigazione e footer in `views/navigation.xml`
e `views/footer.xml`, asset commerciali dichiarati dal manifest. La precedente
integrazione `website_torrepulia_request_theme/views/commerce.xml` e la politica
di rendering del modulo funzionale sostituiscono le azioni commerciali e i
collegamenti al carrello senza riscrivere le pagine salvate nel Builder.
Il controllo server aggiunto qui rende inefficaci anche i vecchi link copiati,
le schede aperte prima del cambio modalità e le chiamate dirette.

## Confine tra carrello e preventivo autorizzato

La politica usa il website risolto da Odoo e la route canonica corrispondente,
non query string, lingua del percorso o flag del browser. CSRF e autenticazione
restano nativi. Le risposte HTTP di sospensione hanno `private, no-store`.

Per i documenti si usa la provenienza persistente nativa: un ordine in
`draft/sent` con `website_id` di un sito in modalità richiesta è un carrello
e-commerce sospeso, salvo il collegamento strutturato alla richiesta validato
dal server. Il token del documento, da solo, non cambia questa provenienza:
anche il recupero carrello può emettere un token. Lo stato `sent` da solo non
prova l'invio da parte del commerciale.

I preventivi preparati dal commerciale nell'issue 7 usano `assigned_website_id`
nativo e il collegamento alla richiesta; `website_id` e-commerce rimane vuoto.
Le altre offerte native create nel backend seguono lo stesso comportamento
standard. Firma, pagamento e accettazione nel portale rimangono funzionanti,
anche con prezzi pubblici nascosti. La conferma manuale interna resta nativa.
Gli ordini già confermati sono esclusi dal blocco dei carrelli e possono seguire
il normale ciclo Vendite, inclusi pagamenti residui autorizzati.

Non vengono alterati `_has_to_be_signed` o `_has_to_be_paid`: influenzano anche
la validazione nativa delle transazioni già avviate. Il controller di firma
verifica invece l'accesso nativo e ferma un vecchio carrello prima di salvare
firma, PDF o messaggi. Un token invalido conserva il percorso di errore nativo.
La creazione di nuove transazioni collegate a carrelli sospesi viene annullata
sotto savepoint, anche se un chiamante interno intercetta l'errore. Non esiste
un parametro pubblico `from_portal` o di contesto che autorizzi un'eccezione.

Non vengono disabilitati provider, portale, firme, contabilità o Vendite.
Le notifiche/callback di transazioni avviate prima del cambio non vengono
retroattivamente annullate; restano gestite da Odoo. Le email di recupero già
accodate prima del cambio non vengono cancellate dal database. L'amministratore
deve esaminare transazioni in corso e coda email al passaggio; eventuali vecchi
link ricevuti restano comunque protetti dal confine server.

## Passaggio e ripristino

Nelle impostazioni del website sono presenti un avviso, il numero dei carrelli
aperti e, per i responsabili Vendite, il pulsante **Esamina carrelli**.
Il conteggio è limitato a website/azienda selezionati e aziende attive; l'unica
elevazione è l'aggregato ristretto per amministratori/responsabili autorizzati.
L'apertura dei documenti applica i normali permessi Vendite, senza elevazione.
Pubblico e portale non possono usare questa azione per leggere altri carrelli.

Attivando la modalità richiesta non si cancellano, importano o convertono
carrelli, preventivi, richieste, opportunità o altri documenti. La selezione della
richiesta rimane separata. I recuperi automatici dei siti sospesi non consumano
flag di invio; i recuperi degli altri siti continuano.

Disattivando la modalità tornano disponibili le route e il recupero del carrello
nativi. Nella stessa sessione, se il carrello è ancora valido secondo Odoo,
viene riutilizzato lo stesso documento. Sessioni scadute, carrelli confermati o
passaggi tra siti continuano a seguire i criteri nativi. I recuperi email possono
riprendere secondo la configurazione e i filtri Odoo; non vengono forzati invii.
Le richieste inviate restano consultabili internamente; le ricevute pubbliche
restano protette dalla sessione e disabilitate con il flusso. Nessuna richiesta
aperta viene convertita in ordine e nessun dato personale viene ripubblicato.

## File modificati e aggiornamento

Tutti i file di questa issue sono in `custom/website_torrepulia_request/`:

- `__manifest__.py`: versione 20.0.1.6.0.
- `models/__init__.py`, nuovo `models/checkout_policy.py`.
- `controllers/__init__.py`, nuovo `controllers/checkout.py`.
- `views/settings.xml`: avviso e verifica carrelli per website.
- `tests/__init__.py`, nuovo `tests/test_checkout_policy.py`.
- `README.md`, nuovi `QA-checkout.md` e `checkout-test-results.txt`.

Con backup ordinario DB/filestore, solo sviluppo o staging:

```sh
odoo -d <database_sviluppo> -u website_torrepulia_request --stop-after-init
```

Riavviare il servizio Odoo perché include nuove classi Python. Nessuna nuova
dipendenza funzionale, migrazione di documenti o aggiornamento del tema originale.
Non vengono toccati core, prezzi, giacenze, domini, HTTPS, indicizzazione o
contenuti Website Builder. Il codice è nei moduli locali; nessun deploy eseguito.

## Prove

Comandi e risultati effettivi in [checkout-test-results.txt](checkout-test-results.txt).
Superati **71 test Odoo** (6 nuovi per questa issue), **29 test JavaScript** e
parsing Python/XML di **60 file**. Nessun test saltato nella suite JavaScript;
il provider Demo necessario alle prove di pagamento è presente nel DB di QA.
Le prove HTTP usano la sessione pubblica reale del test server e controllano
route dirette, POST/JSON-RPC, vecchi token, carrello gratuito, recupero,
isolamento di un secondo website e ripristino dello stesso carrello.
Le regressioni del portale commerciale verificano firma e pagamento Demo;
nessuna email o transazione reale verso clienti/circuiti esterni.

Browser non disponibile (`apps: [], browsers: []`): screenshot e verifica visiva
del nuovo avviso backend non eseguibili. Le viste vengono validate da Odoo.
Il test HTTP di firma mantiene il PDF sintetico della suite precedente; non è
un collaudo della resa del report commerciale.
