# Servizio unico di selezione — 20.0.1.1.0

## Ambito e uso dai componenti

Un solo stato server e un solo servizio browser per catalogo, scheda prodotto,
pagina stagionale, header e riepilogo. Nessuna lista locale delle quantità,
carrello Odoo o `sale.order`. Il modulo espone protocollo, store e binding
riutilizzabili; i layout delle pagine e la scelta editoriale dei prodotti della
campagna restano responsabilità delle rispettive issue del tema.
Il vecchio configuratore stagionale a quattro campi non viene mappato a prodotti
inventati, né i contenuti salvati vengono sostituiti automaticamente.

In una Interaction Odoo 20 usare `this.services['torrepulia.request']`:

```javascript
const selection = this.services['torrepulia.request'];
this.registerCleanup(selection.subscribe(state => this.render(state)));
await selection.read();
// configuration viene dal configuratore nativo: prodotto effettivo, UoM e PTAV.
await selection.add(configuration, 2);                  // catalogo: incremento
await selection.setConfiguration(configuration, 3);     // stagionale: totale 3
await selection.setQuantity(line.key, 3);               // riepilogo: totale 3
await selection.remove(line.key);
await selection.clear();                               // solo azione esplicita
await selection.retryPending();                        // esito di rete incerto
```

`configuration`: `product_id` della variante reale, `uom_id` nativa facoltativa
(default prodotto), `no_variant_value_ids` e `custom_values` come dizionario
`{stringa_id_PTAV: testo}`. Il servizio controlla i valori nativi e le esclusioni;
non crea automaticamente varianti dinamiche, prodotti combo o configurazioni
nuove non risolte. Il configuratore nativo deve fornire una variante reale.
Non passare listini, prezzi, azienda, contatti, proprietari o team.

Per widget semplici lo stesso binding `RequestSelectionBinding` è registrato
in `public.interactions` con radice `[data-tp-request]`. Non annidare radici.

| Attributo | Uso |
| --- | --- |
| `data-tp-request-config` | JSON della sola configurazione nativa sul contenitore di prodotto; ID generati dal server, nessun ID fisso |
| `data-tp-request-add="2"` | Pulsante di incremento; default 1 |
| `data-tp-request-quantity` | Input quantità totale per la configurazione del contenitore |
| `data-tp-request-line` | Su input del riepilogo, chiave opaca ricevuta dal server |
| `data-tp-request-remove` | Su pulsante rimozione, chiave della riga |
| `data-tp-request-clear` | Pulsante di svuotamento esplicito |
| `data-tp-request-count` | Contatore header/riepilogo; somma delle quantità, senza conversione fra UoM |
| `data-tp-request-link` | Link aggiornato dalla destinazione centrale del website |
| `data-tp-request-message` | Messaggi di errore/avviso; usare `role="status"` nel componente |
| `data-tp-request-retry` | Pulsante Riprova per la stessa operazione incerta |

Per attributi variabili e personalizzazioni usare direttamente il servizio dal
configuratore: non serializzare input personali negli attributi del Builder.
Gli input dinamici cambiano solo la proprietà `value`, mai `defaultValue` o
attributi quantità. Contatori e messaggi vengono ripristinati allo stop della
Interaction. Il binding non è registrato in `public.interactions.edit`.
Gli eventuali nodi del riepilogo creati da un consumer devono essere rimossi con
la cleanup della Interaction. Lo snippet salva solo configurazione editoriale.

## Protocollo HTTP

`GET /torrepulia/request/current`: stato corrente e token CSRF. In modalità
richiesta inizializza al più una bozza vuota per sessione/website; serve a fornire
un’identità della selezione prima della prima modifica, evitando che un vecchio
incremento possa essere reinterpretato come inizio di una nuova richiesta.
Non crea contatti o opportunità. In modalità standard restituisce `enabled=false`.

`POST /torrepulia/request/update`: form-urlencoded con token CSRF nativo e
`payload` JSON (massimo 32 KiB). Niente JSON-RPC con CSRF disabilitato.
Campi comuni obbligatori:

- `operation`: `add`, `set_configuration`, `set`, `remove` o `clear`;
- `operation_id`: stringa casuale di 16–64 caratteri `[A-Za-z0-9_-]`, da riutilizzare
  identica nei ritentativi della stessa operazione;
- `selection_id` e `revision`: ricevuti dall’ultima lettura autorevole;
- `add`/`set_configuration`: configurazione prodotto e `quantity`;
- `set`: `line_key` e `quantity`; `remove`: solo `line_key`; `clear`: nessun altro campo.

La chiave della riga non autorizza accesso: viene cercata solo fra le righe della
bozza risolta dalla sessione. Non si accettano ID di richiesta o website dal client.
I campi non previsti sono rifiutati, anche se sembrano campi ORM validi.

Le risposte restituiscono soltanto `state`: website corrente, identità opaca,
revisione, righe con configurazione/quantità e descrizioni già selezionate,
disponibilità della configurazione, avvisi, contatori, limiti e URL centrale.
Non espongono digest/session token, contatti, CRM o modelli elevati. Non contengono
importi: i consumer che mostrano prezzi devono usare le API native di pricing e
rispettare `show_prices`. Nessun motore prezzi viene introdotto dal servizio.

Tutte le risposte hanno `Cache-Control: no-store, private` e `Vary: Cookie`.
La modalità standard e le rotte native carrello/checkout non vengono sovrascritte.

## Identità e quantità

La chiave di configurazione è SHA-256 di un JSON canonico comprendente variante
`product.product`, UoM, PTAV senza variante ordinati e testi personalizzati.
Gli spazi iniziali/finali dei testi vengono rimossi; maiuscole, contenuto e varianti
restano distinti. Le righe equivalenti preesistenti vengono presentate aggregate;
la modifica esplicita di quella configurazione le consolida senza toccare altre
configurazioni. Non si fondono quantità di UoM differenti.

Origine e campagna sono attribuzione commerciale della richiesta. Non fanno
diventare differenti due prodotti uguali; se il raccolto cambia realmente la
fornitura, rappresentarlo con un prodotto/attributo/variante nativo distinto.
Non è accettato un campo libero “raccolto” che alteri silenziosamente l’identità.

Minimo, massimo e passo sono configurabili per website. Le quantità devono essere
finite, non negative, multipli del passo e rappresentabili con `uom.round` nativo
Odoo 20 (“Product Unit”); niente API di rounding di versioni precedenti.
`add` rifiuta zero; i controlli totali usano zero per la rimozione esplicita.
Sono ammesse al massimo 200 configurazioni e 32 testi personalizzati per bozza.

Il dominio di catalogo, la pubblicazione, l’azienda, gli attributi e la UoM vengono
controllati dal server nell’ambiente del visitatore. Nessun controllo di stock
blocca una semplice richiesta di preventivo e non si riservano quantità.
Le righe divenute archiviate/non pubblicate/non valide restano con un avviso e la
descrizione salvata quando erano accessibili; non si mostrano nuovi dati privati
di catalogo. Sono rimovibili, ma non aggiornabili finché la configurazione non è
nuovamente valida.

## Concorrenza e ritentativi

La bozza è protetta dal lock PostgreSQL; le operazioni hanno un registro con
vincolo univoco `(request_id, operation_id)`. Un replay restituisce lo stato
attuale senza riapplicare l’operazione. Riutilizzare un identificatore per un
contenuto diverso è un errore. Il registro sopravvive a clear/rimozioni e viene
cancellato insieme alle sole bozze scadute; non viene potato prematuramente.

Revisione o identità superata: HTTP 409 con stato corrente e nessuna modifica.
Il client mostra il conflitto; un nuovo intento esplicito userà la revisione
aggiornata. Le ValidationError causano rollback al savepoint e HTTP 422.
Gli errori PostgreSQL di serializzazione sono gestiti dai ritentativi di
transazione nativi Odoo; una collisione durante l’inizializzazione viene tradotta
in `ConcurrencyError` per ottenere lo stesso comportamento.

Il client serializza i comandi, ignora risposte precedenti alla revisione/epoca
accettata, ritenta una risposta di rete persa con lo stesso identificatore e
conserva l’operazione incerta in `sessionStorage` del tab, quando disponibile.
Finché l’esito non è verificato, un nuovo incremento è bloccato: Riprova controlla
la stessa operazione anche dopo navigazione/ricaricamento. Lo stato completo
della selezione rimane sul server. Se lo storage browser è disabilitato, la
deduplicazione dei ritentativi dello stesso comando resta attiva durante la pagina.

Al ritorno tramite pageshow/BFCache, focus o tab visibile si rilegge il server.
BroadcastChannel invia solo una notifica “changed”, mai prodotti/quantità, e gli
altri tab attivi rileggono il proprio website. Senza BroadcastChannel la rilettura
avviene comunque al ritorno. Nessuna sincronizzazione anonima fra dispositivi.
Il login nativo ruota il SID e conserva i dati della sessione: la capability
Torrepulia già inizializzata preserva la selezione; non si cercano richieste
storiche per email/contatto. Il logout nativo svuota la sessione come previsto.

## Aggiornamento e verifiche

Aggiornare solo `website_torrepulia_request` a `20.0.1.1.0`, poi riavviare Odoo e
rigenerare gli asset secondo il normale aggiornamento modulo. La pre-migrazione
`migrations/20.0.1.1.0/pre-selection.py` assegna un’identità distinta a ciascun
record preesistente prima dei vincoli NOT NULL/UNIQUE; l’ORM inizializza la
revisione. Il solo default casuale di un campo non basta per una colonna legacy.
Nessuna migrazione distruttiva o
riscrittura dei contenuti Builder. Le richieste inviate rimangono immutabili.

```sh
odoo -d <database_test> -u website_torrepulia_request --stop-after-init \
  --test-enable --test-tags=/website_torrepulia_request
node --test custom/website_torrepulia_request/tests/test_request_store.mjs
```

Il test con connessioni PostgreSQL concorrenti si esegue da Odoo shell chiamando
`tools/concurrency_qa.py:run(env)`. È bloccato su qualsiasi database diverso da
`torrepulia_request_test`; commette fixture dedicate e le elimina a fine verifica.
Non eseguirlo su staging o produzione. Risultati in [QA-selection.md](QA-selection.md).
