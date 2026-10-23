# Handoff Torrepulia: stato al 23/10/2026 (sera)

Documento di ripresa per la prossima sessione di lavoro. Ultimo commit deployato: `740277b`
(caratteri locali al posto di Google Fonts), dopo `ddef52a` (Fase 3 e collaudo).

## Prossima sessione: La Peranzana (/l-olio) e La famiglia (/aboutus)

Obiettivo: applicare la critica del 23/10 alle due pagine con i materiali dell'utente. I
testi sono nel Builder: modificarli via migrazione con backup della vista (autorizzato),
mantenendo le sezioni editabili. Verifica visiva a 1440 e 390 px, una sola tornata di test,
commit e deploy solo dopo aver mostrato il risultato all'utente.

Materiali e risposte dell'utente (23/10):
- **Analisi**: `C:\Users\salvatore.leone\Downloads\torrepulia_odoo20\Torrepulia foto webp\Analisi olio 2024.pdf`.
  Rapporto di prova del Frantoio Sacco Oliveti, Torremaggiore, 19/11/2024, committente
  Leone, misurato con XDS Rapid Liquid Analyzer (analisi rapida, non laboratorio
  accreditato; numero di rapporto vuoto). "Riproducibile liberamente solo nella sua
  totalità": pubblicare il PDF intero (file statico del tema) e chiamarlo "rapporto di prova
  del frantoio", mai "certificato". Valori: acidità 0,17 %, perossidi 4,91, K232 1,87,
  K270 0,12, DeltaK 0,00, acido oleico 70,23 %, polifenoli totali 588,98 mg/kg, tocoferoli
  243,55 mg/kg. Idrossitirosolo + tirosolo + derivati (6,95 + 12,88 + 134,40 + 100,92 +
  80,28 + 16,83) = circa 352 mg/kg, sopra la soglia di 250 mg/kg del claim UE 432/2012:
  utilizzabile solo con la formula autorizzata ("I polifenoli dell'olio d'oliva
  contribuiscono alla protezione dei lipidi ematici dallo stress ossidativo", con 20 g al
  giorno) e meglio dopo conferma di un laboratorio. Fino ad allora niente frasi salutistiche
  generiche come "benefici per la tua salute".
- **Dimensione**: "oltre 1000 piante di ulivo nell'agro di Torremaggiore" (niente ettari né
  contrada).
- **Foto del trattore**: papà Michele sul trattore e nonno Santino Vincenzo. Didascalia da
  aggiungere; uniformare ovunque il nome del nonno a "Santino Vincenzo"; anno non noto.
- **"Filiera corta certificata"**: non esiste una certificazione. L'utente: "noi
  raccogliamo, moliamo e spediamo". Togliere "certificata" e scrivere il fatto. **Da
  chiedere all'utente**: la molitura avviene al Frantoio Sacco Oliveti (di terzi)? Se sì,
  scrivere "moliamo entro poche ore al frantoio di Torremaggiore", non "moliamo noi".
- **Chi fa cosa**: "siamo piccoli, tutti fanno tutto": niente sezione sui ruoli.
- **Frasi del padre o del nonno**: non ci sono. Se utili, predisporre segnaposto ben
  marcati e **non pubblicarli come citazioni reali** finché l'utente non li sostituisce.

Interventi (dalla critica, in ordine di priorità):
1. /l-olio: blocco "Le analisi del raccolto 2024" (3 valori grandi + tabella con i limiti,
   riusando `torrepulia.oil.profile` e il template `pdp_oil_profile`) con link al PDF.
2. /l-olio: togliere il Bag in Box (`s_bag_in_box`) e portarlo nella scheda del Bag in Box;
   chiusura con doppia scelta "Ordina dalle scorte" / "Prenota l'olio nuovo".
3. /l-olio: luoghi ridotti a un paragrafo + mappa della home; card 01-04 riscritte (niente
   griglia di card uguali), righe di testo entro 70 caratteri, sentence case, spaziatura
   del sottotitolo sensoriale su mobile.
4. /aboutus: via i "pilastri" e le affermazioni non documentate ("certificata", "ulivi
   secolari", "sostenibili", "benefici per la salute", "condividiamo le analisi" senza
   link); "vendemmie" diventa "raccolte"; "secolare" va tolto (la storia parte dal 1945);
   registro meno enfatico; fascia "Come lavoriamo" con fatti e link alle analisi; date in
   filigrana leggibili; finale con firma "Franco e Salvatore Leone" e invito a prenotare.
5. Entrambe: chiusure diverse da quella di home e footer; gerarchia dei nomi (azienda
   Leone, marchio Torrepulia, olio La Regina, cultivar Peranzana); immagini del processo
   con srcset (process-crates servita a 960 px per 273 px, 188 KB).

Altre cose aperte: URL del nuovo sito di produzione (per verificare compressione, caratteri,
corriere e bonifico); configurazione in produzione di corriere espresso e bonifico con IBAN;
testo di esaurimento della latta ("Prenota l'olio nuovo!") da cambiare a cura dell'utente.

## Obiettivo e vincoli

- Sito Odoo 20 dell'Azienda agricola Leone (olio EVO Peranzana "La Regina"), marchio
  di qualità premium. Apertura pubblica **entro fine ottobre 2026**.
- Modello di vendita **ibrido**: le scorte si comprano con checkout nativo; l'olio
  nuovo si prenota (zero anticipo, paghi alla spedizione) e diventa opportunità CRM.
- L'utente installa da sé in produzione i moduli `website_torrepulia_request*`.
- GA4 e Meta Pixel si collegano solo a sviluppo finito.
- Prezzi, badge e nomi prodotto nel catalogo sono dati di prova dell'utente: non
  segnalarli come difetti.
- Skill di design: Impeccable (audit, polish), Taste (`design-taste-frontend`,
  `redesign-existing-projects`; non `gpt-taste`), Emil Kowalski (`animate`,
  `review-animations`, `emil-design-eng`). Sono in `~/.codex/skills`: leggere i
  rispettivi `SKILL.md` e adattarli a Odoo (QWeb, SCSS, Interactions, Builder).

## Fatto e in produzione

| Commit | Contenuto |
|---|---|
| `c73df32` | Moduli richiesta, campagna e bridge nel repository |
| `a751a59`, `5cc75c4` | Deploy: verifica immagine, traceback completi, **backup DB + `-u` dei moduli Torrepulia installati** a ogni deploy |
| `156a4df` | Modalità commerciale `hybrid`: `_torrepulia_request_enabled()` (catalogo a richiesta) separato da `_torrepulia_selection_enabled()` (request o hybrid); prodotti della campagna aperta solo prenotabili |
| `ef7a55c` | Audit P1: foto prodotto WebP riconvertite (Odoo non ridimensiona il WebP), logo e diagramma alleggeriti, nastri nella palette, gutter mobile, aree cliccabili, velatura Territorio |
| `43bb212` | Fase 1: home ripulita via migrazione con backup vista, H2 corretti, etichette italiane, pulsanti in minuscolo |
| `def0c78` | Fase 2, scheda prodotto: selettore formati, filtrazione a interruttore, rassicurazioni, carta d'identità dell'olio (`torrepulia.oil.profile`, profilo "Raccolto 2024") |
| Fase 2.1 | Shop a righe (fascia "Olio nuovo" a campagna aperta, etichetta di stato, frase "per chi", prezzo al litro; via ricerca, ordinamento, wishlist) e `/prenotailtuoolio` con una card per formato e contatori Filtrato / Non filtrato, riepilogo fisso su telefono, stato vuoto con ancora `#tp-campaign-formats` |

Proposta di direzione approvata: https://claude.ai/artifact/LKRhjcMZMbsqV8AX7T8xx8

## Decisioni dell'utente

- Spedizioni: proposta A, gratuita da 89 €, altrimenti 9,90 €, 24-72 ore lavorative
  (testo in Website → Siti → "Nota spedizione sulla scheda prodotto").
- Filtrato e non filtrato: stesso prezzo, filtrato proposto di default; il cliente
  può volerli misti nello stesso formato. Modello: attributo "Filtrazione" (varianti).
- Analisi 2024 (Frantoio Sacco Oliveti, 19/11/2024): acidità 0,17 %, perossidi 4,91,
  K232 1,87, K270 0,12, polifenoli 589 mg/kg, acido oleico 70,2 %, tocoferoli 244 mg/kg.
  Mostrarla sempre come raccolto 2024.
- Testi editoriali salvati nel Builder: autorizzato a correggerli via migrazione con backup.

## Prossimi passi (piano verso l'apertura)

1. **Fatto il 23/10: shop a righe e pagina olio nuovo.**
   - Shop: un formato per riga, foto grande, frase "per chi", prezzo al litro,
     etichetta di stato ("Disponibile subito" / "Raccolto 2026 · in prenotazione"),
     fascia "Olio nuovo 2026" in apertura; via ricerca, ordinamento e wishlist.
   - `/prenotailtuoolio`: per ogni formato **due contatori Filtrato / Non filtrato**
     in un'unica scheda (oggi il modulo campagna fa una card per variante);
     riepilogo fisso su mobile; lo stato vuoto non deve rimandare fuori pagina;
     card più brevi.
2. **Fatto il 23/10:** home e checkout (vedi sotto, Fase 2.2).
3. **Fatto il 23/10:** microinterazioni, token di colore, audit (vedi Fase 3).
4. **Fatto il 23/10 in locale:** collaudo end-to-end (vedi Fase 3). Restano: correzione
   Google Fonts, verifica in produzione (serve l'URL della VM), poi SEO di base e analytics.
5. **Dopo i materiali dell'utente:** La Peranzana e La famiglia (critica del 23/10: analisi
   2024 in pagina, Bag in Box nella sua scheda, affermazioni non documentate da togliere,
   errori "vendemmie" / "secolare" / nome del nonno, sentence case, chiusure con
   "Prenota l'olio nuovo"). Materiali chiesti: PDF analisi, ettari o piante e contrada,
   foto del trattore (chi, anno), documento per "certificata", chi fa cosa, una frase vera.

Residui dell'audit: token completati il 23/10. In locale CSS 1,3 MB e JS lazy 2,7 MB non
compressi (gzip: 166 KB e 607 KB): verificare la compressione del proxy in produzione.

## Fase 3 e collaudo (23/10)

- Microinterazioni: battito del contatore carrello (`static/src/js/cart_feedback.js`),
  accordion della scheda con `::details-content` + `interpolate-size`, riquadro carrello
  e pulsanti nel tema, zoom delle righe shop solo con puntatore. Nessuna animazione su
  contatori e prezzi (dati letti).
- Token nuovi in `design_system.scss` (`--tp-photo`, `--tp-paper`, `--tp-field`,
  `--tp-alert`, `--tp-scrim`, `--tp-shadow`, `--tp-on-dark*`, `--tp-gold-line`,
  `--tp-focus-on-dark`); i moduli richiesta/campagna usano `var(--tp-x, fallback)`.
- Scheda prodotto: via confronto, accordion in sentence case, avviso di esaurimento
  ripulito anche con vendita da esaurito consentita (`commerce.py`, `availability.xml`).
- Collaudo locale (script `collaudo.py purchase|preorder|closed` nella scratchpad della
  sessione): 33/33. Ordini di prova S00019, S00020; opportunità 106 e 108.
- Google Fonts: risolto in `740277b` (migrazione 20.0.3.12.0, test `test_brand_fonts_are_self_hosted`).

## Fase 2.2 (home e checkout)

- Home, sezione "La tua tavola. Il tuo formato.": stessa etichetta di stato dello shop
  (template `format_state`), frase "per chi", prezzo al litro, "Prenota" in stagione;
  nastri nativi e freccia nelle righe tolti (i badge "Badge nei formati" restano).
- Checkout: titoli Caslon, "Nome e cognome", "Azienda", identificativo fiscale in italiano
  (patch JS in `static/src/js/checkout.js`), via "Riordina velocemente", "Il tuo ordine"
  su telefono. Migrazione 20.0.3.11.0: passi "Carrello › Consegna › Pagamento", pulsanti
  "Procedi all'acquisto" / "Vai al pagamento", etichetta "Conferma l'ordine" per i metodi
  da pagare dopo (il bonifico lo è sul sito Torrepulia).
- Configurazione locale (da replicare in produzione a mano): metodo "Corriere espresso"
  a prezzo fisso 9,90, gratuito oltre 89, prodotto servizio dedicato, "Standard delivery"
  non pubblicato; fornitore "Wire Transfer" rinominato "Bonifico bancario" e pubblicato
  (in produzione serve l'IBAN sui conti bancari dell'azienda). Account: default Odoo.
- Indirizzo del nuovo sito di produzione: da chiedere all'utente (torrepulia.it è il vecchio).

## Configurazione introdotta con la Fase 2.1

- Prodotto → scheda Torrepulia → "Per chi è questo formato" (frase nello shop; migrazione
  20.0.3.10.0 l'ha compilata per i tre formati solo dove vuota).
- Website → "Etichetta shop: disponibile" / "Etichetta shop: esaurito".
- Campagna → gruppo "Shop durante la campagna": etichetta in prenotazione, titolo e testo
  della fascia. Vuoti = testo predefinito con l'anno di apertura della campagna.
- Prezzo al litro: impostazione "Prezzo di riferimento" del sito + quantità e unità L su
  ogni variante (5 L latta e Bag in Box, 3 L le 6 bottiglie).
- "Acquista" nelle righe apre la scheda prodotto (la filtrazione si sceglie lì). In
  modalità `request` lo shop torna alla griglia nativa (`_torrepulia_shop_rows_enabled`).
- Campagna chiusa + prodotto esaurito: nessuna richiesta possibile (scelta attuale);
  restano "Avvisami" nativo e il messaggio di esaurimento del prodotto.
- Locale: l'utente ha chiuso la campagna "Nuovo raccolto" il 22/10 per prova.

## Ambiente e comandi

- Repository: `C:\Users\salvatore.leone\Downloads\torrepulia_odoo20\torrepulia-20`,
  branch `main`. Ogni push su `main` fa build, test, pubblicazione GHCR e deploy
  sulla VM (backup + `-u`). Niente `[skip ci]` su commit con codice.
- Stack locale: container `torrepulia-20-local-dev-odoo-1` (repo montato in
  `/mnt/torrepulia`, sola lettura per l'utente del container) e `...-db-1`.
  Database: `torrepulia_cinematic_install` (sito locale, porta 8069) e
  `torrepulia_request_test` (test). Il server serve di default `odoo_dev`.
- Test Odoo (121 al 23/10, dopo il riordino dei test della home):
  `docker exec torrepulia-20-local-dev-odoo-1 bash -c 'odoo --db_host "$HOST" --db_user "$USER" --db_password "$PASSWORD" -d torrepulia_request_test -u website_torrepulia_theme,website_torrepulia_request,website_torrepulia_request_theme,website_torrepulia_request_campaign --stop-after-init --http-port=8079 --max-cron-threads=0 --test-enable --test-tags=/website_torrepulia_theme,/website_torrepulia_request,/website_torrepulia_request_theme,/website_torrepulia_request_campaign --log-level=test'`
- Test JS (45): `MSYS_NO_PATHCONV=1 docker exec -w /mnt/torrepulia/custom torrepulia-20-local-dev-odoo-1 bash -c 'node --test website_torrepulia_request*/tests/*.mjs'`
- Aggiornare il sito locale: stesso comando con `-d torrepulia_cinematic_install`,
  senza `--test-enable`, poi `docker restart torrepulia-20-local-dev-odoo-1`.
- Verifica visiva: Playwright in Python locale. Per servire il database giusto senza
  toccare la configurazione si usa un proxy locale su `:8090` che inoltra a `:8069`
  con una sessione legata a `torrepulia_cinematic_install` (script nella scratchpad
  della sessione precedente: ricrearlo se serve).

## Insidie già incontrate

- Log locali in DEBUG: i traceback `ir_access ... failed to evaluate domain` sono
  rumore del core, non errori.
- Odoo 20: i campi binari vogliono `BinaryValue`/stringa base64; Pillow in Odoo non
  carica il WebP finché non si importa `WebPImagePlugin`; per le cache dei template
  usare `env.transaction.invalidate_ormcache('templates')`.
- Aggiungere un attributo a un prodotto con una variante **archivia la variante** e
  ne crea di nuove; unità base e quantità vanno impostate su ogni variante.
- Le pillole delle varianti cambiano il radio selezionato, non la classe `active`.
- Nel Git Bash usare `MSYS_NO_PATHCONV=1` con percorsi `/mnt/...` e non chiamare
  `inspect.py` uno script Python (oscura il modulo standard).
- Il database locale è in modalità **ibrida** per scelta dell'utente: non ripristinarlo.
  Vi sono già l'attributo Filtrazione e le varianti 58-63 in campagna.
- libsass interpreta `max()`/`min()` con `env()` come funzioni Sass e la compilazione
  fallisce ("A css error occurred"): scrivere `Max(...)` come fa già il tema.
- Le migrazioni non devono forzare `lang='it_IT'`: il database di test non ha l'italiano.
  Usare la lingua predefinita del sito.
- Un template nuovo richiede `-u` del modulo: il solo riavvio con dev_mode non lo registra.
