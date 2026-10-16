# About Us: Apertura Editoriale

## Ambito

Prima fase del 16 ottobre 2026: sostituire solo apertura e
racconto delle tre generazioni su `/aboutus`, database
`torrepulia_cinematic_install`. La home, il blocco storico inferiore e la CTA
esistente non sono stati modificati. Una vista inattiva conserva la pagina
precedente: `website_torrepulia_theme.about_before_editorial_20261016_173810`.
Lo script di applicazione verifica che home e sezioni successive restino identiche.
Il successivo completamento della seconda meta e descritto in
[Radici: Seconda Meta](roots-closing.md); mantiene invariati questi due blocchi.

## Composizione

- Fondo bianco ottico, verde Torrepulia e font serif Libre Caslon Display.
- H1 su due frasi, sottotitolo del brief e fotografia autentica in bianco e nero
  di Franco e Salvatore a tutta larghezza della griglia editoriale.
- Foto nativa, sostituibile dal builder; bordi 8px e ombra leggera. Nessuna
  generazione o ricostruzione delle persone. Il file originale resta invariato.
- Tre colonne sopra 991px, con partenze sfalsate di 0/80/160px. Lo sfalsamento
  usa spazio reale e non trasformazioni che possano sovrapporsi ai contenuti.
- Sotto 992px: una colonna, ordine cronologico e spaziatura regolare. Sotto
  576px: gutter 22px, fotografia 3:2 e tipografia dedicata, senza font in vw.
- Testi del brief riprodotti senza riscrittura.

## Codice

- `views/snippets/s_phase_two.xml`: due snippet esistenti aggiornati.
- `static/src/scss/about_editorial.scss`: stili isolati alle nuove classi.
- `static/src/js/about_editorial.js`: entrata progressiva nativa, senza librerie.
- `__manifest__.py`: nuovo foglio nel bundle frontend Odoo.
- `tools/about_editorial.py`: ispezione; `--apply` sostituisce esplicitamente
  soltanto i due blocchi concordati, con backup e controlli di conservazione.
  `--restyle` aggiorna invece solo la struttura decorativa, preservando foto,
  testi e attributi gia salvati nel database.

La pubblicazione locale e esplicita. I normali aggiornamenti del modulo non
sovrascrivono la pagina salvata dal proprietario; i default dei due snippet
rimangono disponibili nel gruppo Torrepulia del builder.

## Verifiche

`python custom/website_torrepulia_theme/tools/about_editorial_qa.py`
verifica sei viewport, foto, contrasto automatico, assenza di overflow,
testi esatti, colonne sfalsate e ordine verticale mobile.

`python custom/website_torrepulia_theme/tools/final_builder_qa.py --about`
prova modifica foto e salvataggio del testo su una copia privata eliminabile,
non sulla pagina pubblica. L'account temporaneo viene disattivato al termine.

Risultati in `docs/qa-about/`; per salvare le catture fuori dal modulo impostare
`TORREPULIA_QA_IMAGES`. Safari/iOS fisico non rientra in questo collaudo.

### Esito Locale

- Playwright Chromium: 1440, 1280, 1024, 834, 390 e 320px, tutti superati.
- Zero overflow, testo troncato, errori JavaScript, richieste HTTP fallite o
  violazioni automatiche axe WCAG A/AA nei due blocchi nuovi. Non e una
  certificazione completa di accessibilita o del resto della pagina.
- Corrispondenza esatta dei tre paragrafi fra template e pagina pubblicata.
- Partenze desktop a 0/80/160px; colonna unica ordinata sotto 992px.
- Immagine caricata e markup nativo modificabile. Selettore media e salvataggio
  testo effettivamente provati nel builder su copia privata, poi eliminata.
  Nel report builder `homeUnchanged` indica la pagina sorgente della prova,
  in questo caso About Us; la home e stata verificata separatamente dal deploy.
- XML, SCSS e JavaScript verificati; Impeccable: zero anti-pattern. Dodici avvisi
  documentali su misure responsive, raggi e ombreggiatura, non difetti di resa.

Catture esterne in
`../torrepulia-theme-cleanup-20261016-110332/qa-about` rispetto al repository.

## Revisione Magazine

- Margini desktop reali 0/80/160px, `align-items: start`, azzerati sotto 992px.
- Date decorative 1945/1980/2020, serif 128px, opacita 6,5%, assolute dietro
  i titoli. Non intercettano il puntatore e sono escluse dall'albero accessibile.
- Sopratitoli maiuscoli 12px. Titoli con interlinea 1,08 e gruppi finali
  non separabili, per evitare l'ultima parola isolata.
- Didascalia nella foto, in basso a sinistra: bianco al 70%, 12px su desktop
  e 11px su mobile, con ombreggiatura locale per mantenerla leggibile.
- Intersection Observer per ciascuna colonna, entrata di 20px in 700ms e
  ritardi 0/200/400ms. Nessuna libreria o listener continuo sullo scroll.
- Senza JavaScript o con movimento ridotto, tutto il testo resta visibile.
  L'observer viene scollegato quando ha finito e alla distruzione nel builder.
  Non viene riprodotto l'ingresso tornando indietro nella pagina.
- Parallasse opzionale omesso per mantenere stabile la lettura.

La pubblicazione `--restyle` ha conservato la vista precedente in
`website_torrepulia_theme.about_before_editorial_20261016_174800` e verificato
che tutti i testi, la home e le sezioni inferiori restassero identici.

I numeri in filigrana sono volutamente a basso contrasto e puramente decorativi,
non testo da leggere: il test axe li esclude esplicitamente dopo aver verificato
`aria-hidden`. Il contrasto dei contenuti di lettura resta sottoposto a controllo.

### Movimento, Criteri Emil

| Prima | Dopo | Perche |
| --- | --- | --- |
| Tre racconti statici | Entrate progressive una sola volta | Accompagnare la sequenza narrativa |
| Posizionamento con padding | Margini reali e allineamento superiore | Dislivello indipendente dalla lunghezza del testo |
| Nessun comportamento motion | Transform/opacity con easing del tema | Nessuna animazione di proprieta di layout |
| Contenuto sempre statico | Rimane statico con reduced-motion o senza JS | L'effetto non impedisce la lettura |

I 700ms sono una scelta esplicita per questa entrata editoriale, non un tempo
di risposta applicato ai comandi dell'interfaccia.

Conferma runtime: stato iniziale a opacita zero e 20px senza transizione inversa;
entrata a 700ms con delay 0/200/400ms; testo visibile al termine, con movimento
ridotto e senza JS. Sei larghezze confermano didascalia nel perimetro della foto,
date decorative presenti, margini responsive e paragrafi originali invariati.
Il modulo aggiuntivo JavaScript pesa 1.799 byte non compressi.
Il builder conferma selezione media e salvataggio: nessuna classe runtime
dell'animazione rimane nell'HTML salvato. Pagina pubblica invariata dal test.
Verdetto movimento: approvato nel perimetro verificato su Chromium.

## Correzione Scatto E Foto Del Proprietario

Riprodotto il salto allo scroll: 100px su desktop, 82px su mobile. L'immagine
non aveva trasformazioni; era il contenuto intero a spostarsi. Odoo compensava
l'header affisso con padding sul main, mentre il CSS del tema manteneva quello
stesso header in posizione relativa, duplicandone l'ingombro.

Ripristinata `position: fixed` esclusivamente per `header.o_header_affixed`
nelle pagine che contengono `.tp-about-opening`. Nessuna disattivazione globale
dell'header o delle animazioni delle colonne; nessun listener aggiunto.

La foto `FOT_9739` caricata dal proprietario (attachment 781, originale 778)
resta selezionata nella pagina e modificabile dal builder. I byte WebP sono
inclusi senza ricompressione nel modulo, come default portatile dello snippet:

- `static/src/cinematic/owner/about-franco-salvatore.webp`: 1035x690, 203.322 byte.
- `static/src/cinematic/owner/about-franco-salvatore-750.webp`: 750x500, 120.950 byte.

Dimensioni esplicite, descrizione alt, caricamento prioritario e `sizes`
aggiunti senza sostituire la selezione nativa o modificare i testi. Backup:
`website_torrepulia_theme.about_before_photo_stability_20261016_201627`.

Test con rotella in discesa e risalita, misure a ogni frame su Chromium a
1366x768 e 390x844: nessuno spostamento della posizione documentale o
dell'altezza della foto dopo la correzione. Entrambe le varianti statiche
restituiscono HTTP 200. XML e SCSS verificati.
Tracce prima/dopo e script diagnostico sono nell'archivio esterno,
`qa-about/scroll-before.json` e `qa-about/scroll-after.json`.

## Rifiniture del 17 ottobre 2026

Apertura e Tre Generazioni condividono il fondo `#EEF2ED`, anche nel default
del modulo. Conservati testi, foto e personalizzazioni salvate dal proprietario.
Le dimensioni inline salvate dal builder non deformano piu le immagini:
la foto d'archivio mantiene il rapporto originale, quella principale il ritaglio
editoriale responsive. Header affisso opaco: bianco nelle pagine interne,
verde `#18231f` sulla home, senza modificare la trasparenza iniziale.

Successiva scelta grafica per Radici: header iniziale `#EEF2ED`, senza linea
divisoria e con navigazione verde oliva. Durante lo scroll il fondo mantiene
il 97% di opacita e una sfocatura di 8px dove supportata (fallback pieno).
Menu mobile pieno nello stesso verde chiaro. Le altre pagine e l'header
trasparente iniziale della home restano invariati.

Verifiche desktop/mobile: `qa-final/header-media-results.json`.
Raccordo foto finale/footer verificato separatamente su quattro larghezze:
`qa-final/closing-blend-results.json`, nessuno stacco cromatico al bordo.
