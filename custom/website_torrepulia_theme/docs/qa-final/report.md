# Collaudo Finale Home

## Correzione Successiva: Schermi Bassi

Riprodotta la sovrapposizione del pulsante hero sulla riga inferiore a 1366x600:
gap iniziale -38,9px. Il precedente collaudo aveva viewport desktop piu alti
e non copriva questo caso. Sostituito il posizionamento assoluto di copy e
riga inferiore con un flusso flex; la hero resta almeno a schermo pieno e puo
crescere se il contenuto richiede spazio. Foto, testi e dimensioni tipografiche
preservati; immagine sempre statica e a pieno fondo.

Regressione mirata superata su 1366x600, 1280x720, 1024x600, 768x600,
1440x1000, 390x568, 320x568 e 740x360. Distanza minima pulsante/riga: 40px;
nessuna intersezione con header, nessun overflow e copertura foto completa.
Controllo Sass e bundle reale HTTP 200 superati, detector senza anti-pattern.
[Evidenza prima](hero-before-results.json), [dopo](hero-final-results.json).
Test ripetibile: `python custom/website_torrepulia_theme/tools/hero_layout_qa.py`.

16 ottobre 2026. Database `torrepulia_cinematic_install`, Odoo 20 su porta 8069.
Perimetro: homepage pubblica, collegamenti al catalogo e modifica nativa nel
builder. Nessun ordine, pagamento o dato commerciale modificato.

## Esito

Home approvata nel perimetro locale verificato. Nessuna regressione bloccante
rilevata. Allineamento della descrizione La Regina a sinistra, senza modifiche
al testo. Corretto anche il conflitto mobile della hero con il vecchio layout
Banner Contained: foto a piena altezza, senza fascia verde e senza animazione.
La lingua del documento della home e ora `it-IT`; impostazioni linguistiche e
commerciali del sito non sono state cambiate.

## Evidenze

- Chromium/Playwright: 1440x1000, 1920x1080, 834x1112, 390x844, 320x740.
- Tutti i viewport: zero overflow orizzontale, testo troncato, immagini rotte,
  errori JavaScript o richieste HTTP fallite; un solo H1 e ancore valide.
- Copertura della foto hero verificata geometricamente su tutti i viewport.
  Il mobile seleziona la variante 1920px invece di ingrandire quella da 640px.
- 12 verifiche funzionali superate: tab sensoriali, tastiera, due formati,
  tre destinazioni shop, menu mobile, tooltip touch e chiusura con Escape.
- Movimento ridotto: nessuna animazione in esecuzione. Zoom della chiusura:
  pausa e ripresa funzionanti; hero statica anche senza movimento ridotto.
- Builder: root modificabile, nessun gruppo snippet disabilitato, selettore
  media aperto sulla foto Peranzana, testo salvato, prezzi dinamici non
  incorporati nell'HTML, pannelli sensoriali coerenti, home pubblicata invariata.
  Prova su copia privata eliminata; account temporaneo disattivato.
- Bundle CSS reale: HTTP 200, 1.223.269 byte non compressi, senza errori Sass.
- Verificati 38 percorsi manifest, 24 XML, 10 SCSS inclusa la palette con
  contesto Odoo, 4 moduli JavaScript e sintassi di 15 file Python.
- Ispezione visiva delle catture desktop/mobile di hero, Regina, Peranzana e
  chiusura; conferma finale della hero mobile dopo la correzione.

[Risultati browser](final-results.json), [builder](builder-final-results.json).
Le catture sono fuori dal modulo, nella cartella `qa-screenshots` dell'archivio
indicato nel [registro di pulizia](cleanup-results.json).

## Audit Impeccable

Verdetto di integrita: sistema coerente con foto, palette, marchio e composizione
approvati dal proprietario. Nessun redesign o copywriting non richiesto.
Il detector sui tre fogli SCSS oggetto della rifinitura rileva zero anti-pattern
e 32 avvisi non bloccanti relativi a colori, raggi e misure fuori dal DESIGN.md
storico. Non sono violazioni di contrasto; non giustificano cambiare il brand.

| Dimensione | Punteggio | Evidenza / limite |
| --- | --- | --- |
| Accessibilita | 3/4 | Axe WCAG A/AA senza violazioni automatiche; tastiera e movimento ridotto verificati |
| Prestazioni | 3/4 | WebP responsive, hero prioritaria, codice SVG obsoleto rimosso; bundle nativo ancora ampio |
| Theming | 2/4 | Palette Odoo e rosa presenti; alcuni colori e misure locali restano letterali |
| Responsive | 3/4 | Cinque viewport e touch sintetico riusciti; dispositivi fisici non certificati |
| Integrita | 3/4 | Builder nativo, copy preservato e nessun asset mancante; documentazione token da allineare |
| Totale | 14/20 | Buono, senza blocchi funzionali nel perimetro verificato |

### Rilievi Residui

- **P2, Theming:** `static/src/scss/bag_in_box.scss` contiene valori locali
  approvati non tutti espressi come token. Impatto sulla manutenzione e su
  futuri cambi globali, non sulla resa attuale. Un futuro intervento mirato
  `$impeccable extract` puo consolidarli senza ridisegnare la home.
- **P3, Prestazioni:** il bundle CSS Odoo servito e circa 1,22 MB non compresso.
  Non e tutto codice del tema; non sono state rimosse dipendenze native a
  rischio del builder. `$impeccable optimize` e opportuno con misure del
  deployment reale, seguito da `$impeccable polish`.
- **Da configurare prima del go-live:** il catalogo locale e in USD e la CTA
  anticipata promuove il primo prodotto disponibile, attualmente la latta 5 L,
  mentre la fotografia editoriale raffigura la bottiglia. Serve confermare
  catalogo e valuta; nessun prodotto o prezzo e stato inventato per mascherarlo.

Axe segnala 13-16 controlli di contrasto incompleti sulle superfici fotografiche:
la leggibilita e stata valutata visivamente, ma questo non costituisce una
certificazione WCAG. Restano da verificare screen reader e dispositivi fisici.
Non sono stati eseguiti Lighthouse, test di carico, upgrade/installazione pulita,
pagamenti, spedizioni o matrice fiscale. Nessuna nuova certificazione dello shop.

## Revisione Movimento, Criteri Emil

| Prima | Dopo | Motivo |
| --- | --- | --- |
| Hero mobile influenzata dalla griglia Banner Contained | Foto assoluta nel frame, senza movimento | Copertura stabile senza bordi verdi |
| Observer, timer, goccia e filtri del vecchio SVG Bag | Rimossi; resta solo il tooltip del raster approvato | Meno lavoro runtime e nessuna animazione estranea alla nuova immagine |
| Zoom fotografico della chiusura | Conservato, pausable e disattivato con movimento ridotto | Ritmo narrativo deliberato, non transizione di un comando |

Verdetto: approvato per le interazioni e il movimento verificati. Nessuna nuova
animazione aggiunta. Le animazioni native scelte dal proprietario restano native.

## Pulizia

116 file archiviati fuori dal modulo: 13 immagini/icone non referenziate,
46 helper superati e 57 evidenze storiche o snapshot intermedi. Totale
42.283.593 byte, circa 40,3 MiB, oltre al codice SVG JS/SCSS non piu necessario.
Rimossa anche la cache Python del vecchio helper fotografico.

Prima dello spostamento e stata salvata una copia completa del modulo.
Archiviazione conservativa basata su codice e viste di entrambi i database,
comprese quelle inattive: conservate risorse delle altre pagine e film legacy
ancora referenziati in `odoo_dev`. Nessuna pagina o foto attuale rimossa.
Il planner richiede ora inventari aggiornati dei due database prima di operare.
README e documentazione operativa aggiornati ai comandi rimasti disponibili.

Archivio: `C:\Users\salvatore.leone\Downloads\torrepulia_odoo20\torrepulia-theme-cleanup-20261016-110332`.
