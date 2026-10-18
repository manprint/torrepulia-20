# Snippet salvati e disponibilita dei formati

## Contenuti incorporati

`views/cinematic.xml`, snippet `s_cinematic_0` e `s_cinematic_1`, riprende
testi, struttura, classi e stile salvati nella homepage italiana (`it_IT`) di
`torrepulia_cinematic_install`. La fotografia Regina usa l'asset gia incluso
nel modulo, senza riferimenti numerici ad allegati del database. Gli attributi
runtime del traduttore/editor e la selezione vuota dei prodotti non vengono esportati.
Il testo del proprietario e conservato, incluso il refuso «LA NOTRA TERRA».

L'aggiornamento cambia le definizioni per i nuovi inserimenti degli snippet.
Non riscrive la homepage, altre pagine, traduzioni salvate o personalizzazioni
Website Builder. Non occorre migrare i contenuti esistenti.

## Disponibilita

Riferimento verificato: Odoo `20.0-20260926`, installato nell'ambiente locale.

- `website_sale/models/product_template.py`: `_get_combination_info`, con
  contesto `website_sale_product_page=True`, e `_get_ribbon`.
- `website_sale_stock/models/website.py`: `_get_product_available_qty` usa
  il magazzino del website; nessuna somma autonoma delle giacenze.
- `website_sale/static/src/interactions/product_page.js` e
  `static/src/xml/website_sale_product_availability.xml`: quantita residua dopo
  carrello, soglia, messaggio esaurito e impostazione di vendita oltre giacenza.
- `website_sale.product_ribbon`: rendering nativo del nastro nell'anteprima.

La route pubblica esistente `/torrepulia/formats` continua a filtrare i prodotti
con il dominio di vendita del website. Prezzi, imposte e valuta continuano a
usare le API native e il contesto della richiesta. I link usano `website_url`.
La disponibilita non viene persistita nell'HTML della pagina: viene riletta
ad ogni caricamento dello snippet, anche dopo la riapertura dell'editor.

Quando il prodotto e tracciato e la vendita oltre giacenza e disattivata,
il pulsante Acquista viene disabilitato se la disponibilita residua non
consente l'acquisto. Il tab del formato e il link Dettagli restano utilizzabili.
Con vendita oltre giacenza attiva, il pulsante resta attivo anche a zero.
Il messaggio esaurito proviene dal prodotto; il riepilogo ne mantiene l'HTML
sanificato, la riga compatta ne mostra il testo. In assenza di messaggio e
con vendita bloccata viene mostrato «Esaurito».

La quantita si vede solo se «Mostra quantita disponibile» e attivo e il residuo
non supera la soglia configurata, come nella scheda nativa. Nessuna impostazione
commerciale viene cambiata per rendere visibile questa informazione.
Il nastro usa il record e le priorita native: un nastro manuale puo prevalere
su un nastro automatico di esaurimento, come nello shop.

Per template con piu varianti si usa `_is_sold_out()` per mantenere raggiungibile
il configuratore finche esiste una variante disponibile. Non viene presentata
una quantita aggregata tra varianti differenti. Il prodotto conserva tutte le
verifiche native al momento della scelta della variante e nel carrello.

## Aggiornamento e ripristino

Aggiornare `website_torrepulia_theme` alla versione `20.0.3.4.0` nel database
di sviluppo, quindi riavviare Odoo per ricaricare il controller Python.
L'aggiornamento standard carica template e asset; non eseguire script che
sostituiscano `page_home_view.arch_db`. Prima di aggiornare altri ambienti,
conservare il consueto backup database/filestore. Per ripristinare questa
funzionalita, ripristinare insieme controller, template, JS e SCSS precedenti,
aggiornare il modulo e riavviare. Le pagine salvate restano intatte.

Test eseguibili con il runner Odoo:

```text
-u website_torrepulia_theme --test-enable
--test-tags /website_torrepulia_theme:TestCinematicFormats
--http-port=8079 --stop-after-init --dev=
```

Usare le normali opzioni di connessione dell'ambiente di sviluppo. La porta
separata evita conflitti con il server gia attivo. I dati dei test sono
transazionali; nessuna giacenza reale viene aggiornata.

Verifica locale del 18 ottobre 2026: 9 test funzionali superati; homepage,
shop, prodotto e carrello verificati a 360, 390, 768 e 1440 px senza overflow
orizzontale o errori JavaScript. Il selettore funziona anche da tastiera.
Su una copia privata temporanea sono stati modificati e salvati i testi di
entrambi gli snippet e aperto il selettore immagini. L'HTML dinamico dei prodotti
non e stato salvato nella pagina e l'hash della homepage originale e rimasto
invariato. Copia e utente temporanei sono stati rimossi dopo il controllo.
Il catalogo effettivo contiene due formati pubblicati: il caso con quattro
formati e coperto dai test transazionali senza creare prodotti permanenti.

## Badge configurabili per formato (20.0.3.5.0)

Aprire un prodotto dal backend, scheda **Torrepulia**, campo **Badge nei formati**.
Si possono selezionare piu etichette oppure crearne di nuove. Cliccare su una
etichetta per aprire la scheda nativa: **Nome**, **Colore**, **Visibile ai clienti**
e, quando e attiva la gestione multiwebsite, **Website**. Il nome usa le
traduzioni native di Odoo. Le etichette senza website sono condivise;
quelle associate a un altro website non vengono mostrate. La sequenza nativa
delle etichette determina l'ordine.

La selezione e una relazione separata su `product.template` verso il modello
nativo `product.tag`: non aggiunge tag ai filtri dello shop e non sostituisce
i nastri nativi. Il colore appartiene all'etichetta: modificarlo cambia tutti
i suoi utilizzi. Non vengono create etichette commerciali predefinite.
I badge appaiono nelle righe dello snippet Formati, anche quando riutilizzato
in «Gli altri formati» della pagina prodotto; sono riletti dal backend ad ogni
caricamento e non salvati nell'HTML della pagina dal Website Builder.

Il testo dei badge viene escapato. Sono ammessi per il rendering colori esadecimali
a tre o sei cifre; valori non validi usano il verde del tema. Il colore del testo
e scelto automaticamente tra nero e bianco in base alla luminanza, mantenendo
un contrasto di almeno 4.5:1. Etichette lunghe vanno a capo senza allargare la riga.

Aggiornare il modulo a `20.0.3.5.0` e riavviare Odoo per caricare il nuovo campo
Many2many. Non occorre migrare o sostituire contenuti salvati. Dopo l'aggiornamento
il campo e vuoto: i badge vengono mostrati solo sui prodotti configurati.

Verifica badge del 18 ottobre 2026: 12 test funzionali superati, compresi
nastri e disponibilita; controllo browser a 360, 390, 768 e 1440 px con badge
di prova renderizzati dalla route in una transazione annullata, senza overflow
o errori JavaScript. Verificati selettore da tastiera, salvataggio del nuovo campo
nel backend su prodotto temporaneo e apertura della scheda colore nativa.
Traduzione italiana del nome verificata. Prodotto, etichetta e utente temporanei
rimossi; assegnazioni sui prodotti reali e homepage rimaste invariate.
