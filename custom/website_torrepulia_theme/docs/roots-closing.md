# Radici: Seconda Meta

## Implementazione

Tre sezioni autonome in `views/snippets/s_roots_closing.xml`:

1. `s_torrepulia_roots_transition`: fascia verde notte, foto storica e H2 nella
   colonna sinistra, testo in quella destra. `.row.align-items-center`, colonne
   `.col-12.col-md-6` e padding nativo `.p-md-4`.
2. `s_torrepulia_roots_values`: fondo bianco, titolo centrato, tre colonne
   `.col-12.col-md-4`, numeri romani oro, H3 serif e testo neutro. Nessuna card.
3. `s_torrepulia_roots_cta`: fondo scuro pieno, contenuto centrato e link nativo
   `/shop`, con `.btn.btn-light.btn-lg`, hover e icona Lucide gia presente.

Il CSS in `static/src/scss/roots_closing.scss` e CSS standard, senza sintassi
Sass, plugin, import remoti o JavaScript aggiuntivo. Usa font e token del tema
gia caricati; griglie, utility e breakpoint strutturali restano Bootstrap 5.
Colori e contenuti possono essere modificati con i controlli nativi Odoo.
Le sezioni sono registrate nel gruppo Torrepulia del builder.

## Conservazione

La pubblicazione locale sostituisce soltanto il vecchio blocco editoriale e
la vecchia CTA di About Us. Apertura e Tre Generazioni sono confrontate prima
e dopo come XML serializzato: identiche. Anche la home resta identica.

Backup inattivo: `website_torrepulia_theme.roots_before_closing_20261016_202235`.
[Registro della pubblicazione](qa-about/closing-publication.json).

`tools/roots_closing.py` ispeziona la composizione. L'opzione `--apply` esegue
esplicitamente la sostituzione con backup; i normali upgrade del modulo non
riscrivono la pagina gia personalizzata dal proprietario.
I default di `data/pages.xml` usano la nuova sequenza sulle nuove installazioni.

## Test E Limiti

`tools/roots_closing_qa.py`: Chromium a 1440, 1024, 834, 390 e 320px;
verifica ordine, testo esatto del brief, layout Bootstrap responsive, immagine,
contrasto axe A/AA dei tre nuovi blocchi, overflow, hover e destinazione CTA.
[Risultati](qa-about/closing-results.json).

`tools/final_builder_qa.py --roots`: selezione media della fotografia storica
e modifica/salvataggio del nuovo testo su copia privata, senza modificare la
pagina pubblica. La copia viene eliminata e l'account QA disattivato.
[Risultati builder](qa-about/builder-roots-results.json).

Impeccable: zero anti-pattern, dodici avvisi documentali su tonalita del brand
gia usate e misure tipografiche responsive. XML e CSS compilati correttamente.
Safari/iOS fisico, screen reader, pagamenti e checkout non fanno parte di questa
verifica. Nessun prodotto, prezzo, stock o ordine modificato.

## Copy Fornito Dal Proprietario

I testi sono quelli richiesti, senza aggiungere risultati analitici, numeri,
marchi di certificazione o documenti inventati. Il collaudo tecnico non verifica
le dichiarazioni "Filiera Corta Certificata", "nessuna contaminazione", le
analisi condivise, acidita, polifenoli e benefici per la salute. Prima del
go-live occorre confermarle con la documentazione aziendale appropriata;
non presentare questo report come certificazione di tali affermazioni.

## Micro-design E Footer

- La riga `align-items-center` ora abbina solo foto e corpo del testo sulla
  prima linea desktop; il titolo occupa la successiva cella a sinistra.
  Le utility `order-*` mantengono foto, titolo, testo su mobile, senza duplicati.
- Padding destro del testo 48px da `md`, 8px su mobile; centro verticale del
  paragrafo misurato entro 0,01px dal centro della foto nei viewport desktop.
- Aggiunto il sottotitolo richiesto con `text-muted small mb-5`, numeri romani
  `h5` da 24px in oro e descrizioni `text-dark` con colore brand all'80%.
- CTA: titolo da 58px e larghezza massima 1040px; una riga a 1440, 1024 e 834px,
  ridimensionamento e ritorni a capo naturali su mobile.
- Footer esterno e `#mc-footer` usano lo stesso `#18231f` della CTA su tutte
  le pagine Torrepulia. Anche la sfumatura finale della home termina in questo
  colore, senza alterare l'immagine o il testo della chiusura.

Pubblicazione `--polish`: testi precedenti, foto, apertura e home conservati;
aggiunto esclusivamente il nuovo sottotitolo. Backup:
`website_torrepulia_theme.roots_before_closing_20261016_203128`.
Il test pubblico verifica il footer anche su home e shop, oltre che su Radici.
