# Handoff Torrepulia: stato al 23/10/2026 (notte)

Documento di ripresa per la prossima sessione di lavoro. Ultimo lavoro: pagine editoriali
(La Peranzana, La famiglia, Il territorio, sezione famiglia della home), migrazione
`20.0.3.13.0`, dopo `740277b` (caratteri locali) e `ddef52a` (Fase 3 e collaudo).

## Fatto il 23/10 (notte): pagine editoriali dopo la critica

Migrazione `20.0.3.13.0` (`models/editorial_pages.py`): ricostruisce le sezioni salvate nel
Builder dagli snippet, con copia disattivata di ogni vista (`before_editorial_pages_*`,
`before_family_alignment_*`); tiene le sezioni aggiunte dal gestore; si può rieseguire.
In locale è già applicata (`refresh_editorial_pages`, `align_home_family` da `odoo shell`).

- **/l-olio**: apertura con link a processo e analisi; storia + mappa della home (SVG
  inline, mai `t-call` nelle pagine: toglie la sezione al Builder); processo a elenco
  ("Raccogliamo, moliamo, spediamo.": entro 8 ore, frantoio partner, molitura seguita di
  persona, estrazione sotto i 27 °C, confezionato poi in magazzino); nuovo blocco
  `s_torrepulia_oil_analysis` (#analisi, valori 2024 statici e modificabili, nota "analisi
  rapida, non laboratorio accreditato", PDF intero
  `static/src/docs/rapporto-di-prova-raccolto-2024.pdf`); Bag in Box tolto; chiusura
  `s_torrepulia_choice_oil`.
- **Bag in Box**: spiegazione nella descrizione del suo prodotto (`website_description`,
  solo se vuota), senza kicker né CTA.
- **Carta d'identità** sulla scheda prodotto: non nomina più il frantoio ("Rapporto di
  prova del frantoio del …"); nuovo campo `report_url` (link al PDF). Il campo `lab` resta
  interno.
- **/aboutus**: "Tre generazioni, la stessa terra."; anni leggibili; capitoli 1945/1980/2020
  (ulivi ereditati "alcuni già secolari", oltre 1000 piante, ricordo delle olive appena
  frante); fascia `s_torrepulia_roots_trees` "Gli ulivi del nonno." (FOT_9550, FOT_9561);
  foto del trattore con didascalia; "Come lavoriamo" (Curiamo, Raccogliamo, Moliamo,
  Spediamo, Misuriamo); chiusura firmata `s_torrepulia_choice_family` con FOT_9704.
- **Home, sezione famiglia**: testi allineati ad /aboutus (sostituzioni esatte), firma
  "Torremaggiore, dal 1945.". La chiusura della home mantiene "ulivi secolari" (veri).
- **/territorio**: apertura FOT_9842 (vigneti e orizzonte, sono dell'azienda); "Nel nord
  della Puglia." con mappa; `s_torrepulia_land_history` "1710 · Il castello e la
  Peranzana." (Raimondo di Sangro nato nel castello ducale il 30/1/1710; il legame con la
  Peranzana solo come tradizione; origine del nome Torrepulia); fascia FOT_9507; chiusura
  `s_torrepulia_choice_land`. Tolta la storia di famiglia ripetuta.
- **Segnaposto citazioni** (processo su /l-olio, foto del trattore su /aboutus):
  `[SEGNAPOSTO, NON PUBBLICATO]`, classi `o_snippet_desktop_invisible
  o_snippet_mobile_invisible d-none`. L'utente li sostituisce nel Builder ("Elementi
  invisibili") e li rende visibili.

### Home e profilo sensoriale (migrazione `20.0.3.14.0`)

`0744143` ha portato in produzione la `20.0.3.13.0`; la `20.0.3.14.0` tocca solo la home
(`align_home_family` → `refine_home`, logica pura in `models/home_copy.py`, per elementi e non
per frasi: la versione `it_IT` della home salvata è diversa da `en_US`) e ricostruisce la
sezione sensoriale di /l-olio e i capitoli di /aboutus (`SENSORY_ONLY`).

- Hero invariata ("La nostra terra. Il tuo olio." resta per scelta dell'utente).
- Tre valori → `s_torrepulia_home_facts`, fascia centrata di tre fatti con link (oltre 1000
  ulivi → /territorio; entro 8 ore → /l-olio#processo; 0,17 % raccolto 2024 → #analisi).
- Bag in Box → `s_torrepulia_bib_line`, scheda "Il formato che consigliamo" sotto i formati,
  link alla scheda prodotto calcolato dal catalogo.
- Tolti: fascia "Da Torremaggiore alla tua tavola", note vuote de La Regina, sottotitolo
  dei formati. Testo de La Regina centrato accanto alla bottiglia.
- Profilo sensoriale dalla scheda di assaggio dell'utente, **riscritto con la voce della
  famiglia** (non copiare la scheda): fruttato medio, oliva appena colta, pomodoro verde,
  carciofo, mandorla fresca, erba e grano appena tagliati; amaro e piccante delicati in
  equilibrio; fluido, pulito, acidità bassa. Mai mela, lattuga, foglia di pomodoro,
  "medio-intenso".
- Ulivi secolari: "gli stessi che oggi sono secolari", "dai secolari del nonno a quelli
  piantati da poco"; mai "alcuni secolari".
- Chiusura della home: link a /territorio (non più email).

### Footer e menu (`20.0.3.15.0`)

- Footer nuovo: `views/footer_editorial.xml` (eredita `website.layout`, priorità 95, sostituisce
  `#mc-footer`, quindi vale anche sulla copia del sito di `cinematic_chrome`) e
  `static/src/scss/footer.scss`. Fascia marca + contatti; gruppi L'olio, Chi siamo,
  Spedizione e pagamento, Seguici; barra © anno · ragione sociale · P. IVA + documenti legali.
- Dati dall'azienda (`website._torrepulia_footer_company`): nome, indirizzo, P. IVA (prefisso
  paese tolto), email, telefono, social (`social_*` di `res.company`, icone `oi_*` di Odoo).
  Righe vuote nascoste. **In produzione compilare la scheda azienda e i social.**
- Pagamenti (`_torrepulia_footer_payments`): solo provider pubblicati; oggi "bonifico
  bancario" in testo. Loghi dei metodi (`payment.method.image`) solo quando ci saranno carte.
- Menu: migrazione 3.15 rende visibile "Il territorio" (sequenza 35, tra La famiglia e
  Contatti).
- Corretto uno scorrimento orizzontale di 9 px tra 768 e 1320 px: sezioni con righe `.gx-5`
  e contenitore a 15 px (regola in `editorial_facts.scss`).

### Altri siti nello stesso database (`20.0.3.16.0`)

In produzione la creazione di un nuovo sito falliva ("L'elemento '<xpath expr=//header/t[@t-call='website.navbar']>'
non può esser localizzato"): `navigation_layout` era generico e lo stile di intestazione "boxed" di Odoo
annida la chiamata a `website.navbar`. Ora `navigation_layout` e `footer_editorial` appartengono al sito
Torrepulia (`website._torrepulia_scope_navigation`, provisioning + migrazione 3.16) e gli agganci usano
`//header//t[...]`. Test `test_other_websites`: un sito nuovo prova tutti gli stili di intestazione e footer.

### Pagina olio nuovo in produzione (23/10)

- Prodotti non visibili su /prenotailtuoolio: la modalità commerciale del sito di produzione era
  "Acquisto online standard". Va impostata a "Acquisto online + prenotazione stagionale" (con
  team commerciale), oltre a campagna "Aperta" e date valide.
- "crypto.randomUUID is not a function": su HTTP il browser non offre `randomUUID`;
  `website_torrepulia_request/static/src/js/random_uuid.js` lo ricrea con `getRandomValues`
  (test `test_random_uuid.mjs`). **La produzione va comunque messa in HTTPS** (Let's Encrypt
  sul proxy + `web.base.url` in https) prima dell'apertura.

Regole sui testi decise con l'utente: mai nominare il frantoio (scrivere "frantoio
partner"); niente superlativi non dimostrabili, "biologico", "certificata", frasi
salutistiche; "secolari" solo per gli alberi; concime, irrigazione e difesa non si citano.

Foto: `C:\Users\salvatore.leone\Downloads\torrepulia_odoo20\Torrepulia foto webp\Foto campagna`
utilizzabili; le foto di prodotto mostrano bottiglie vecchie, non usarle.

Altre cose aperte: frasi vere di papà o del nonno per i segnaposto; URL del nuovo sito di
produzione (per verificare compressione, caratteri, corriere e bonifico); configurazione in
produzione di corriere espresso e bonifico con IBAN; testo di esaurimento della latta
("Prenota l'olio nuovo!") da cambiare a cura dell'utente; analisi del raccolto 2026
(nuovo profilo olio + PDF + aggiornare il blocco analisi nel Builder).

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
5. **Fatto il 23/10 (notte):** La Peranzana, La famiglia e Il territorio (critica del 23/10: analisi
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
