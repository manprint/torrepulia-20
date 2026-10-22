# Integrazione richiesta e scheda prodotto Torrepulia

Versione **20.0.1.3.1**. Bridge fra `website_torrepulia_request` e il tema originale,
che rimane invariato. I formati riutilizzano quantità, varianti, disponibilità,
prezzi nativi e servizio di richiesta condiviso. Le aggiunte del catalogo
rispettano «Vendi quando esaurito»; la campagna stagionale resta un preorder.

## Gestione della scheda prodotto

In **Vendite / Prodotti → prodotto → Torrepulia → Scheda prodotto sul sito**:

- **Titolo della scheda Torrepulia**: valore iniziale «La Regina» per preservare
  la presentazione esistente; se vuoto, compare il nome del prodotto.
- **Il Profilo Sensoriale**, **Abbinamenti in Cucina**, **Spedizione e
  Conservazione**: tre campi HTML traducibili e sanitizzati da Odoo. Ogni campo
  compilato genera una sezione espandibile sotto il prezzo. I campi vuoti,
  compreso HTML visivamente vuoto, non generano sezioni.

Gli esempi nei campi backend sono segnaposto: nessuna descrizione sensoriale,
condizione commerciale o tempistica di spedizione viene assegnata automaticamente
ai prodotti reali. La modifica dei testi non modifica nome commerciale, prezzo,
stock o dati delle richieste ricevute.

## Formati e nastri

«Gli altri formati» esclude il prodotto corrente mediante un filtro server sul
catalogo accessibile del website. Lo snippet generico continua a mostrare tutti
i prodotti scelti dal gestore. Il filtro vale anche in modalità shop standard.
Non vengono modificati gli ID salvati nel Website Builder.

I nastri usano `_get_ribbon()` nativo: `website_ribbon_id`, colori e priorità,
comprese le assegnazioni automatiche. Sono presenti nell'anteprima e nella riga
del formato anche in modalità richiesta, distinti dai badge editoriali del tema.

## Aggiornamento

Aggiornare `website_torrepulia_request` **20.0.1.11.0** e questo bridge, quindi
riavviare Odoo. Il bridge crea quattro colonne sul modello nativo
`product.template`; non richiede migrazioni manuali o aggiornamenti al tema
originale. I campi editoriali nuovi rimangono vuoti; il titolo mantiene il valore
predefinito. Nessuna pagina o personalizzazione Builder viene riscritta.

L'inizializzazione ORM del modello menu del tema resta inclusa per i database
storici. La correzione degli sfondi oltre 1920 px resta attiva.

[Report, file modificati, test e screenshot](../../docs/qa-20261020-product/REPORT.md).


Dal 21/10/2026 gli avvisi stock dei formati riutilizzano il componente condiviso
senza cornice rossa. Testo e pulsante sono separati, con CTA coerente con le altre
card. La prenotazione viene mostrata solo per una campagna aperta del website.
Non richiede un pulsante HTML nel messaggio. I nastri e i badge editoriali rimangono
configurazioni separate, senza modifiche automatiche ai dati del gestore.
Il layout è applicato anche nel Builder. Vedere il
[report aggiornato](../../docs/qa-20261021-stock-design/REPORT.md).
