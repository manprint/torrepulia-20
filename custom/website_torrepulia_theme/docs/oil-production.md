# Processo produttivo e abbinamenti

Aggiornamento del 17 ottobre 2026 sulla pagina `/l-olio`.

## Sorgenti

- HTML/QWeb: `views/snippets/s_production_process.xml`.
- CSS: `static/src/scss/oil_production.scss`, incluso negli asset frontend.
- Due snippet indipendenti, griglia nativa Bootstrap 5, nessuna libreria JS.
- Quattro schede da 992px, due da 768px, una sui telefoni.
- Testi in flusso naturale, nessuna altezza fissa o posizionamento assoluto.
- Hover solo su dispositivi con puntatore: zoom immagine 1.045, 300ms ease-in-out.
  Il riquadro resta stabile; movimento disabilitato con prefers-reduced-motion.
- Icone Lucide gia presenti nel modulo; numero oro scuro leggibile.
- Abbinamenti a due colonne, descrizioni del proprietario preservate e CTA `/shop`.

## Fotografie autentiche

Tre fotografie fornite dal proprietario convertite in WebP (qualita 88, massimo
960px, senza ritocchi o tagli). Restano sostituibili tramite il selettore media.
Tool ripetibile: `tools/prepare_production_media.py <cartella-originali>`.

| Originale | Asset | Dimensioni | Byte |
| --- | --- | --- | --- |
| bin_forati.jpeg | process-crates.webp | 960x960 | 187684 |
| molitura.jpeg | process-mill.webp | 950x960 | 96702 |
| confezionamento_frantoio.jpeg | process-bottling.webp | 586x586 | 25908 |

La prima fase usa lo scatto delle olive sul ramo gia incluso nel modulo.
Nessuna immagine sintetica rappresenta gli impianti dell'azienda.

## Correzione tecnica richiesta

Il proprietario ha confermato che lo stoccaggio sotto azoto non fa parte del
processo: riferimento rimosso e quarta fase intitolata Confezionamento in
Frantoio. Nessuna promessa di eliminazione dell'ossigeno o freschezza totale.
Le altre specifiche sono quelle fornite dal proprietario, non una nuova
certificazione o verifica documentale di processo.

## Pubblicazione e verifica

`tools/oil_production.py --apply` crea un backup inattivo prima di sostituire
esclusivamente processo e abbinamenti. Apertura, storia, profilo sensoriale,
Bag in Box e chiusura restano identici. Nessun upgrade globale del modulo.

QA: `tools/oil_production_qa.py` (cinque larghezze, assenza sovrapposizioni,
immagini caricate, hover stabile, movimento ridotto e CTA shop) e
`tools/final_builder_qa.py --oil-production` (copia privata temporanea).
Report JSON in `docs/qa-final`.

Esito positivo a 1440, 1024, 834, 390 e 360px: nessuna sovrapposizione o
overflow, quattro immagini caricate, CTA shop funzionante. Zoom 1.045 senza
spostamento delle schede e nessun movimento con preferenza ridotta. Builder:
selettore media aperto e testo salvato sulla copia privata, originale invariato.
Controllo Impeccable sui nuovi HTML/CSS senza rilievi.

## Rifinitura tipografica

Descrizioni delle schede allineate a sinistra e fotografie quadrate, mantenendo
la stessa larghezza del testo e aumentando la presenza visiva. Quarta fase:
"Confezionamento Accurato", senza riferimenti a sottovuoto o azoto.

Profilo sensoriale: etichette maiuscole 12px, descrizioni in Libre Caslon Display
32px (28px sui telefoni). Accenti oro sulle note pomodoro verde, carciofo e
mandorla fresca. Spaziatura lettere normale, nessuna nuova animazione.

Abbinamenti interamente allineati a sinistra, CTA piena `#18231f`, testo bianco,
freccia bianca anche a riposo, distanza dal testo ridotta a 24px.

`tools/oil_production.py --polish` interviene solo sui tre blocchi interessati,
conservando foto e descrizioni delle schede, testi degli abbinamenti e tutte
le altre sezioni della pagina. QA estesa a gerarchie sensoriali, allineamenti,
formato immagini e colori effettivi della CTA.

## Chiusura coordinata con Radici

Dopo Bag in Box la pagina usa lo snippet `s_torrepulia_roots_cta`, copiato
direttamente dalla versione salvata sulla pagina La famiglia: titolo
"Il prossimo assaggio comincia qui.", sottotitolo e CTA shop identici.
Sostituita la vecchia CTA finale per evitare due chiusure consecutive.
Sfondo `#18231f`, identico al footer; nessuna nuova regola CSS necessaria.
Pubblicazione con backup e verifica desktop/mobile:
`tools/oil_closing.py --apply --verify`.
