# La Peranzana: apertura editoriale

Prima meta della pagina `/l-olio`, aggiornata il 17 ottobre 2026.

- HTML QWeb: `views/snippets/s_cultivar_editorial.xml`.
- CSS dedicato: `static/src/scss/oil_editorial.scss`.
- Due snippet autonomi nel builder: La Cultivar Reale e Origini della Peranzana.
- Griglia nativa Bootstrap 5: hero 7/5 da 992px, impilata sotto.
- Sfondo bianco, serif del brand, fotografia WebP gia presente nel modulo.
- Immagine nativa modificabile, srcset, dimensioni riservate e nessuna animazione.
- Header coordinato bianco, senza bordo; durante lo scroll opacita 97% con
  blur di 8px dove supportato e fallback pieno. Menu mobile pieno.
- Nessuna modifica all'header di Radici o alla home.

Testi forniti dal proprietario conservati, incluso il carattere tradizionale
e non documentale del collegamento con Raimondo de Sangro.
Titolo oro del focus in tonalita scura per mantenere leggibilita sul fondo chiaro.

Pubblicazione locale con `tools/oil_editorial.py --apply`: crea prima un backup
inattivo e verifica che le sezioni successive, la home e Radici restino immutate.
Il comando senza argomenti ispeziona soltanto. Evitare upgrade globali del modulo
per pubblicare singoli blocchi su pagine personalizzate.

Verifiche: `tools/oil_editorial_qa.py` e `tools/final_builder_qa.py --oil`.
Il secondo lavora su una copia privata temporanea, senza modificare la pagina
pubblica, verifica apertura del selettore media e salvataggio di un testo.

Esito: layout verificato a 1440, 1024, 834, 390 e 360px; nessun overflow,
nessuna immagine mancante o eccezione JavaScript. Link `#processo` visibile
sotto l'header affisso; menu mobile con fondo pieno. Builder: selettore media
aperto, testo salvato sulla copia privata, pagina pubblica invariata.
Report in `docs/qa-final/oil-editorial-results.json` e
`docs/qa-final/builder-oil-results.json`. Controllo Impeccable sui nuovi HTML/CSS
senza rilievi. Raggruppate le ultime due parole dell'H1 per evitare un'ultima
riga con una sola parola, senza cambiare il testo.

## Revisione degli allineamenti

Hero ampliata: colonna testo 7/12, fotografia 5/12, contenitore massimo 1400px.
A 1440px il paragrafo misura circa 725px, contro i circa 600 precedenti.
Sotto 992px testo e immagine tornano verticali, evitando colonne strette su tablet.

Storia organizzata in titolo a sinistra e racconto a destra, in griglia 5/7.
Fascia territorio aperta, senza fondo panna: tre comuni con icone Lucide
map-pin locali dorate, separatori sottili e descrizioni allineate a sinistra.
Torremaggiore e identificata dalla nota "Qui coltiviamo i nostri ulivi".
Nessun primato geografico o marchio territoriale non documentato aggiunto.

Pubblicazione con `tools/oil_editorial.py --restyle`: conserva i contenuti
salvati e la foto originale, con verifica automatica del testo prima/dopo.
Processo produttivo, abbinamenti e altri blocchi restano invariati.
QA aggiornata controlla allineamenti, larghezza testo, disposizione dei comuni,
icone caricate, header, ancoraggio e menu mobile sulle cinque larghezze.
