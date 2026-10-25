# Handoff Torrepulia: stato al 25/10/2026

Documento di ripresa per la prossima sessione di lavoro. Tutto il lavoro del 23-25/10 è su
`main` e deployato (ultimo: tema `20.0.3.24.0`). Versioni: tema `20.0.3.24.0`,
richieste `20.0.1.16.0`, richieste-tema `20.0.1.6.0`, campagne `20.0.1.9.0`.
Apertura pubblica prevista **entro fine ottobre 2026**. **Dal 25/10 la produzione è su
https://torrepulia.it** (spostata dall'utente; www → dominio senza www e http → https in 301,
CSS/JS in gzip). Il vecchio indirizzo http://212.227.88.91:10000/ non risponde più.
**Da sistemare:** canonical, `og:url`, `og:image` e la sitemap in robots.txt escono in
`http://`: Odoo non sa di essere dietro HTTPS. Servono `proxy_mode = True` in `odoo.conf`,
il dominio del sito `https://torrepulia.it` (Website → Impostazioni → Dominio) e
`web.base.url` = `https://torrepulia.it` con `web.base.url.freeze` = True.

## Prossima sessione: verso l'apertura

1. **HTTPS e compressione** (rinviato dall'utente il 24/10, bloccante per l'apertura): oggi
   CSS 1,3 MB e JS 2,7 MB arrivano senza compressione. Proposta: Caddy nel compose della VM
   (`encode zstd gzip`, Let's Encrypt automatico), DNS di torrepulia.it verso 212.227.88.91,
   porte 80/443 fino al container `dind-to20`, `proxy_mode = True`, `web.base.url` in https
   con `web.base.url.freeze`, redirect www → dominio senza www. In `odoo.conf` della VM anche
   `list_db = False` (la master password l'utente l'ha impostata il 23/10). È il giorno in
   cui si spegne il vecchio sito ed entrano in gioco i redirect 301.
2. **Configurazione a cura dell'utente** (fatto: master password, attributo Filtrazione,
   corriere):
   - **server di posta in uscita (SMTP) + SPF/DKIM su torrepulia.it: senza, nessuna email
     parte** (conferma prenotazione, notifiche, ordini);
   - team commerciale con almeno un membro con email (notifica interna);
   - pagamenti: per ora **solo bonifico** (pubblicare "Bonifico bancario" con IBAN e
     nascondere "paga su fattura", che il footer mostra). Altri metodi online solo dopo un
     benchmark dell'utente;
   - giacenze dei formati a scorte dopo la molitura (oggi "Temporaneamente esaurito");
   - campagna: "Prezzo" oggi "Prezzo bloccato garantito" → "Bloccato per tutta la stagione"
     o vuoto; "Consegna" oggi "Consegna prevista tra…" ripete l'etichetta → "Tra novembre e
     dicembre";
   - prodotti (testi preparati il 24/10, vedi sotto): nome con il formato, titolo web vuoto,
     un solo paragrafo di descrizione; 6 bottiglie: formato "6 bottiglie", contenuto "6
     bottiglie da 500 ml"; Bag in Box: "5 litri" minuscolo; latta: unità L e quantità 5 sulla
     variante (oggi "13,80 € / Unità"); attributo "Non Filtrato" → "Non filtrato";
   - scheda azienda: via "Contrada Pagliara Vecchia SNC" (oggi "Pagliara Vecchia SNC
     Contrada Torremaggiore");
   - menu di produzione: c'è "Home" e "Acquista" (in locale niente Home, "Acquista olio");
   - shop: filtri per attributo visibili in produzione (in locale spenti). Nel Builder il
     menu "Filtri" della pagina prodotti, oppure attributo Filtrazione → Visibilità →
     Nascosto (da verificare l'opzione esatta del menu "Filtri" in Odoo 20);
   - **termini e condizioni**: incollare l'articolo 6-BIS (testo sotto) dopo il punto 6.2;
     far rivedere 7.1 (refuso "per interno"), 7.2 (PayPal non attivo), 10.4 (rimborso su
     carta) a chi ha scritto i termini;
   - cookie policy da completare con GA4 e Meta prima di inserirne gli ID (GA4: Impostazioni
     sito → Google Analytics; Meta: campo "Meta Pixel" subito sotto).
3. **Collaudo finale in produzione:** un ordine dalle scorte e una prenotazione veri (email
   comprese), poi apertura.
4. Facoltativo, dopo l'apertura: modello di email per la conferma d'ordine (preventivo
   dall'opportunità) con scadenza e istruzioni di pagamento.

## Flusso della prenotazione (deciso il 24/10)

Prenoti (zero anticipo, non è un ordine) → email di riepilogo → qualche giorno prima della
molitura conferma d'ordine (prezzo bloccato, spedizione, totale) → **7 giorni** per
confermarla e completare il pagamento (campo campagna `confirmation_days`) → ricevuto il
pagamento, spedizione da Torremaggiore. Modifica o annullamento senza costi fino alla
conferma d'ordine. Spese di spedizione lette da `website.torrepulia_shipping_note` (lo
stesso campo dello shop). Regole di testo: mai "paghi alla spedizione", mai il metodo di
pagamento nei testi del sito e delle email (solo nella conferma d'ordine), tono morbido
("Prenoti · Confermi l'ordine · Lo ricevi a casa", "Ricevuto il pagamento, ti spediamo
l'olio nuovo direttamente da Torremaggiore").

Articolo da incollare nei termini (dopo 6.2, titolo con lo stile di "6. CONFERMA
DELL'ORDINE"):

> **6-BIS. PRENOTAZIONE DELL'OLIO NUOVO**
> 6-bis.1 Durante la campagna di raccolta l'utente può prenotare i Prodotti del nuovo
> raccolto dalla pagina "Olio nuovo" del Sito. La prenotazione è gratuita, non comporta
> alcun pagamento e non costituisce un ordine ai sensi dei punti 5 e 6.
> 6-bis.2 Al ricevimento della prenotazione MICHELE LEONE invia all'utente un'e-mail di
> riepilogo. Fino all'invio della conferma d'ordine di cui al punto 6-bis.3, l'utente può
> modificare o annullare la prenotazione senza alcun costo, rispondendo a tale e-mail o
> contattando MICHELE LEONE ai recapiti indicati sul Sito.
> 6-bis.3 Prima della molitura MICHELE LEONE invia all'utente, tramite e-mail, una conferma
> d'ordine con i Prodotti prenotati, il prezzo indicato sul Sito al momento della
> prenotazione, le spese di spedizione calcolate secondo le tariffe indicate sul Sito e
> l'importo totale.
> 6-bis.4 L'ordine si intende concluso con il pagamento dell'importo totale, da effettuarsi
> entro 7 (sette) giorni dall'invio della conferma d'ordine con le modalità in essa
> indicate, tra quelle previste al punto 7. Per gli ordini derivanti da una prenotazione
> tale termine sostituisce quello indicato al punto 7.2. Decorso il termine senza che il
> pagamento sia stato effettuato, la prenotazione decade senza alcun costo per l'utente.
> 6-bis.5 La spedizione avviene dopo il ricevimento del pagamento, secondo quanto previsto
> al punto 8. Dalla conclusione dell'ordine si applicano integralmente le presenti
> Condizioni generali di vendita, compreso il diritto di recesso di cui al punto 10.

## Testi dei prodotti (preparati il 24/10, da inserire dall'utente)

| | Nome prodotto | Formato | Contenuto | Per chi è questo formato |
|---|---|---|---|---|
| Duetto | La Regina, Duetto | Duetto | 2 bottiglie da 500 ml | Per un regalo, o per assaggiarla la prima volta. |
| 6 bottiglie | La Regina, 6 bottiglie | 6 bottiglie | 6 bottiglie da 500 ml | Per la tavola di ogni giorno, una bottiglia alla volta. |
| Latta | La Regina, latta 5 litri | Latta | 5 litri | Per la dispensa di casa, da travasare poco alla volta. |
| Bag in Box | La Regina, Bag in Box 5 litri | Bag in Box | 5 litri | Per chi usa l'olio ogni giorno, fino all'ultima goccia. |

Descrizioni (un paragrafo, sotto il titolo):
- Duetto: «Due bottiglie da 500 ml di La Regina nella confezione regalo. Per far assaggiare
  la nostra Peranzana a chi non la conosce ancora, o per tenerne una in tavola e una di
  scorta.»
- 6 bottiglie: «Sei bottiglie da 500 ml in vetro scuro, che ripara l'olio dalla luce. Se ne
  apre una alla volta e le altre restano intatte: la scorta per la cucina di tutti i giorni.»
- Latta: «Cinque litri di La Regina in latta, che tiene l'olio al buio. Il formato della
  dispensa: si travasa poco alla volta in un'oliera e si conserva al fresco, lontano da
  fonti di calore.»
- Bag in Box: «Cinque litri di La Regina in una sacca che si richiude su sé stessa a ogni
  erogazione e lascia entrare poca aria, dentro una scatola che ripara dalla luce. Il
  formato per chi usa l'olio ogni giorno, a crudo e in cucina.»

In produzione l'utente ha usato " - " al posto della virgola nei nomi: il titolo non va a
capo dopo "La Regina" (va bene comunque).

## Fatto il 25/10: testi e analisi da un'unica fonte (tema 3.22.0)

Migrazione `recopy_pages` (`models/editorial_pages.py`, `home_copy.recopy_section`): per
elementi, backup `before_copy_2510_*`, rieseguibile. Decisioni dell'utente, valgono su tutto il sito:
- **Fruttato medio-intenso** (sostituisce "medio" del 23/10), profilo elegante e armonico,
  morbido e rotondo, amaro e piccante delicati e ben bilanciati, finale pulito; **niente erba
  e grano**. Raccolta: "Raccogliamo … è il momento in cui l'oliva è più ricca di polifenoli e
  di profumi" (mai "antiossidanti").
- **"Frantoio di fiducia"** (non più "partner"). **Niente magazzino**: "confezioniamo
  direttamente in frantoio e lo spediamo a casa tua".
- **Oltre 1.500 ulivi** (non 1000). Franco non ha studiato economia.
- Home: "Il carattere della nostra terra.", didascalia "Solo Peranzana, solo dai nostri
  ulivi.", famiglia "Tre generazioni, gli stessi ulivi.", gusto "Morbido. Equilibrato.",
  fatto "Dal 1945 · tre generazioni sulla stessa terra" al posto di "0,17 %".
- /aboutus: i tre capitoli 1945/1980/2020 con i testi dell'utente (vecchio sito come fonte).
- /l-olio: apertura "duplice attitudine", "dalle loro olive nasce La Regina", meta
  description senza "raccolto 2024".
- **Analisi:** `s_torrepulia_oil_analysis` ora è un contenitore (`.tp-analysis-content`,
  `static/src/js/oil_analysis.js`) riempito da `/torrepulia/analisi` con
  `oil_analysis_content`. Mostra `_torrepulia_published_analysis()`: l'ultima carta d'identità
  con valori, solo se `harvest_year >= stagione - 1` (stagione = anno da settembre),
  altrimenti "Le analisi del raccolto <stagione>" in arrivo. Nuovi campi della carta:
  `report_file` (PDF, servito da `/torrepulia/analisi/<id>/rapporto.pdf`) e `analysis_note`.
  **Da fare dall'utente:** carta "Raccolto 2025" senza valori collegata ai prodotti a scorte
  (oggi mostrano la tabella 2024); a dicembre carta "Raccolto 2026" con valori e PDF.
- Fascia stagionale dello shop con `olive-cassone-*`.

### 25/10 (mattina), tema 3.23.0
- Profumo senza "oliva appena colta" (`retext_aroma`, backup `before_aroma_*`).
- Barra fissa della scheda prodotto su telefono: `#product_details { z-index: auto }` (lo
  `z-index: 0` di Odoo la faceva finire sotto carta d'identità e footer).
- **Conferma d'ordine nel portale** (`views/portal_order.xml`, `scss/portal.scss`, solo sul sito
  Torrepulia): "Conferme d'ordine", "Conferma e paga" (neutro sul metodo, Stripe arriverà),
  "Paga con un altro metodo" se c'è già una transazione, "Da confermare entro il", "IVA inclusa",
  "Il tuo referente", niente "Powered by Odoo", finestra di rifiuto "Annulla l'ordine", dettagli
  del bonifico Beneficiario/IBAN/Importo/Causale. Nuova dipendenza `payment_custom`.
- La firma online è già un campo nativo per ordine (`require_signature`, "Firma online" nella
  scheda dell'ordine); il predefinito si toglie in Vendite → Impostazioni → Firma online.
- Verificato: una conferma d'ordine creata dal backend con olio in campagna si paga col bonifico
  (transazione pending). Il blocco "olio del nuovo raccolto" vale solo per i carrelli del sito.
- **Configurazione in produzione:** conto bancario (IBAN) sull'azienda, collegato al fornitore
  "Bonifico bancario"; messaggio "In attesa" del fornitore in italiano (oggi "Please find the
  payment details below."); Vendite → Impostazioni: Firma online spenta, Pagamento online acceso
  al 100 %; nome delle imposte in italiano (oggi in locale "0% Exports", "Tax 15%").
- **Email in pochi secondi:** l'invio della richiesta sveglia `cron_prepare_request_notifications`
  e la preparazione sveglia `mail.ir_cron_mail_scheduler_action` (nativo: ogni ora). I turni
  periodici restano come rete di sicurezza (`_trigger_cron` in `submission.py`).
- **Indirizzo nella prenotazione:** il modulo della campagna chiede via, CAP (5 cifre), città e
  provincia (elenco `res.country.state` IT) al posto di "CAP o Città"; il modulo richieste generico
  resta con "CAP o Città". L'indirizzo va in `torrepulia.request.address` e nei campi nativi
  dell'opportunità (`_shipping_lead_values`): "Nuovo preventivo → crea cliente" lo copia sul contatto.
- Email: Zoho piano gratuito, SMTP `smtp.zoho.eu` 465 SSL, filtro FROM `info@torrepulia.it`,
  dominio alias torrepulia.it con mittente e catchall `info`. DNS su Aruba: SPF `spf.zoho.eu`,
  DKIM selettore `zoho` (1024 bit), DMARC `p=none`. Team destinatario configurato il 25/10 (senza,
  l'invio della prenotazione si annulla e resta bozza).
- **Conferma d'ordine (tema 3.24.0):** `sale.order._find_mail_template` sceglie sul sito Torrepulia
  `mail_order_confirmation` (corpo `mail_order_confirmation_body`, cornice `mail_layout_bare`, oggetto
  "La tua conferma d'ordine S000xx", PDF "Conferma d'ordine S000xx.pdf" da `action_report_order_confirmation`);
  `type_name` "Conferma d'ordine"; PDF con titolo "Conferma d'ordine", "Data", "Da confermare entro".
  Il modello email e' noupdate (oggetto e mittente modificabili dal backend), il corpo e' una vista.
- **Popup di pagamento:** difetto di Odoo 20 (`portal_prepayment.js` legge `data-is-partially-paid="false"`
  come vero e apre la finestra a ogni visita); patch in `static/src/js/portal_prepayment.js`.
- PDF: lo stile viene dal "Layout documenti" dell'azienda (configurazione dell'utente).
- La chat del portale ("Hai una domanda? Scrivici") è un componente isolato con stile proprio
  (pulsante "Invia" viola di Odoo): non raggiungibile dal tema.

## Fatto il 24/10 (pomeriggio e sera)

- **Foto della raccolta (tema 3.21.0):** da `Foto Raccolta/` (WhatsApp 24/10, collaboratori
  con consenso) tre scatti convertiti in `cinematic/owner/`: `olive-cassone-*` (testata di
  /prenotailtuoolio, messa dall'utente nel Builder e predefinita dello snippet campagna),
  `process-harvest*` ("La raccolta" su /l-olio, messa dall'utente nel Builder e predefinita
  dello snippet), `raccolta-reti-*` (telo sotto gli ulivi, colonna dell'introduzione del
  processo: la migrazione `add_process_photos` aggiunge solo la foto, backup
  `before_process_photo_*`). L'introduzione resta fissa solo su schermi alti almeno 820 px.
  Scartati: scatti con tubi e parafango (16.11.36, 16.17.47) e i doppioni del trattore.
- **Video Instagram:** servono i file originali (non i link); taglio 6-10 s muto in
  MP4/WebM + poster come `hero-desktop/mobile`, niente embed di Instagram (cookie di Meta).

- **Home in `noindex` (fix 3.19.0):** la 3.18.0 cercava la home senza lingua (l'url di
  `website.page` è tradotto) e correggeva un altro record. Ora `_torrepulia_launch_seo` usa
  la stessa ricerca di `website.page._get_page_info` (lingua del sito, `website_domain()`,
  `order='website_id asc'`). Verificato in produzione.
- **Menu stagionale:** "Olio nuovo" (menu e footer) visibile solo con lo switch del sito
  **e** la campagna aperta (`website._torrepulia_seasonal_visible()`,
  `_torrepulia_seasonal_open()` nel modulo campagne). La 3.19.0 ha messo il flag
  `torrepulia_seasonal` sulla voce di produzione (bordo oro) e acceso lo switch.
- **Filtrazione:** la 3.19.0 imposta l'attributo "Filtrazione" a `pills` (in produzione era
  radio); il tema lo disegna come interruttore.
- **Footer su una griglia a 12 colonne** (`footer.scss`, `.mc-footer-identity`): marchio
  sulla metà sinistra, contatti allineati alla terza colonna, quattro colonne uguali, oro
  solo ai titoli, email/telefono/indirizzo 16 px stesso colore, città in maiuscolo resa
  leggibile (`navigation.py`). Il footer resta allineato all'header (cornice a tutta
  larghezza, come la home): le pagine editoriali hanno contenitori più stretti.
- **Scheda prodotto:** titolo con scala propria (`boutique.scss`, 52 px desktop / 32 px
  telefono, `calc()` dentro `clamp()` per libsass), a capo dopo la virgola da 768 px
  (`.tp-title-format`). Sottotitolo composto: formato (solo se non nel titolo) ·
  `torrepulia_denomination` (nuovo campo, predefinito "Olio extravergine di oliva
  Peranzana", vuoto = omesso) · contenuto. La pagina prodotto ha anche la classe `.mc-page`:
  serve la specificità di `#product_details`.
- **Flusso prenotazione (campagne 1.9.0, tema 3.20.0):** testi di pagina, riepilogo,
  pagina di conferma, email cliente/team, riquadro scheda prodotto, fascia shop, riga dei
  formati in home e chiusure editoriali (migrazione con backup `before_payment_wording_*`).
  Fatti della campagna centralizzati in `campaign._public_facts()`. La migrazione campagne
  svuota i vecchi `payment_note`/`shop_band_text` "paghi alla spedizione".

## Fatto il 23-24/10: verso l'apertura

- **Verifica produzione (23/10):** pagine 200, nessuno scorrimento a 1440/390, caratteri
  locali, nessun errore JS. Il gestore database era pubblico senza master password:
  sistemato dall'utente.
- **Testi:** via "lo spediamo entro 48 ore" (scheda prodotto, fascia shop): ora "Lo moliamo
  entro 8 ore dalla raccolta e te lo spediamo appena è pronto". Plurale "1 confezione".
- **Email di prenotazione** (`website_torrepulia_request`, `views/mail.xml`): le notifiche
  esistenti (coda `torrepulia.request.notification`, cron ogni 5 minuti, coda email nativa)
  ora usano un template QWeb per client email (tabelle, stili in linea). La ricevuta salva
  `reservation` (stagione + fatti della campagna) all'invio tramite
  `website._request_receipt_context()` (vuoto nella base, campagna in modalità ibrida).
  Oggetto calcolato `_mail_subject()` (migrazione 1.16.0 sui template noupdate). Anche
  `/la-tua-richiesta/conferma` parla di prenotazione.
- **SEO** (`website_torrepulia_theme/models/seo.py`, migrazione 3.18.0,
  `_torrepulia_launch_seo`, rieseguibile): home di nuovo indicizzata (in produzione aveva
  `noindex`) con titolo/descrizione del seed; /shop "Acquista olio extravergine Peranzana";
  descrizione predefinita delle schede prodotto; immagine di condivisione
  `torrepulia-condivisione.jpg`; `/terms` (testo Odoo in inglese) → 301
  `/termini-e-condizioni` (`controllers/terms.py`); `/privacy` → `/privacy-policy`, fuori
  sitemap. Redirect 301 dal vecchio sito (anch'esso Odoo, indirizzi dalla sua sitemap):
  schede prodotto per codice LARGBIB5/LARG6BT500/LARG2BT500/LARGLAT5, /home, blog,
  livechat, /brand-listing. Nessun valore del gestore viene sovrascritto. Odoo 20 applica i
  301 solo se nessuna rotta risponde; i dati strutturati prodotto sono già nativi.
- **Cookie** (`views/consent.xml`, `scss/consent.scss`): barra accesa sul sito, testi
  italiani, Rifiuta/Accetta con lo stesso peso, la X rifiuta, scelta valida 180 giorni,
  "Preferenze cookie" nel footer. GA4 nativo con Consent Mode. Meta Pixel
  (`website.torrepulia_meta_pixel_id`) caricato solo dopo il consenso.
- **Prenotazione bloccata da righe archiviate (24/10):** dopo l'aggiunta della Filtrazione
  le bozze vecchie contenevano varianti archiviate senza modo di toglierle sulla pagina
  campagna. Ora "Rimuovi" nel riepilogo compatto, un solo avviso in alto, campi chiusi
  riconoscibili.

Facoltativo, rinviato dall'utente: filestore nel backup del deploy, backup giornaliero
separato e copia fuori dalla VM (oggi: solo `pg_dump` del DB sulla VM, ultimi 10 deploy).

Contenuti che aspettano l'utente: frasi vere di papà o del nonno per i due segnaposto;
analisi del raccolto 2026 (nuovo profilo olio + PDF + blocco analisi nel Builder); prezzi,
badge e nomi prodotto definitivi (oggi di prova); foto della testata dell'olio nuovo (in
produzione c'è il tramonto scelto nel Builder; `olive-raccolta-1280.webp` è disponibile).

## Fatto il 23/10 (sera): pagina olio nuovo e menu

- **/prenotailtuoolio** (modulo campagne `20.0.1.8.0`, `views/snippet.xml`, `models/page.py`
  passo `opening_facts_v2` / attributo `data-hero-facts`): testata con testo "moliamo entro
  8 ore", pulsante "Scegli i formati"; tre fatti nella testata letti dalla campagna
  (`delivery_period`, `price_note`, `payment_note`, con testi predefiniti); "Come funziona"
  in tre passi; via "PREZZO BLOCCATO / FILIERA PROTETTA / ZERO ANTICIPO" e "produzione
  limitata" (si produce in base alle prenotazioni). Su schermi ≥768 px una sola griglia a
  1320 px con `display: contents` su testata e contenuto (nessun nodo spostato via JS). La
  foto predefinita del tema viene sostituita, quella scelta nel Builder resta.
- **Bag in Box:** il link della home punta a `<scheda>#come-funziona`. Il sanitizer di Odoo
  toglie gli `id` dalla descrizione prodotto e la scheda riscrive l'URL con la variante:
  l'ancora la mette `static/src/js/bag_in_box.js`, che legge l'hash al caricamento.
- **Menu:** voce stagionale "Olio nuovo" come pulsante con bordo oro (pieno sulla sua
  pagina, bianco sopra la foto della home); su telefono prima voce con "Prenotazioni aperte"
  solo se la campagna è aperta (`design_system.scss`, `navigation.xml`).

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
- Test Odoo (146 al 25/10):
  `docker exec torrepulia-20-local-dev-odoo-1 bash -c 'odoo --db_host "$HOST" --db_user "$USER" --db_password "$PASSWORD" -d torrepulia_request_test -u website_torrepulia_theme,website_torrepulia_request,website_torrepulia_request_theme,website_torrepulia_request_campaign --stop-after-init --http-port=8079 --max-cron-threads=0 --test-enable --test-tags=/website_torrepulia_theme,/website_torrepulia_request,/website_torrepulia_request_theme,/website_torrepulia_request_campaign --log-level=test'`
- Test JS (48): `MSYS_NO_PATHCONV=1 docker exec -w /mnt/torrepulia/custom torrepulia-20-local-dev-odoo-1 bash -c 'node --test website_torrepulia_request*/tests/*.mjs'`
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
- La home salvata ha versioni `en_US`, `it_IT` (quella pubblica) e `_en_US` diverse: le
  migrazioni lavorano per elementi (`models/home_copy.py`), non per frasi esatte.
- Il sanitizer delle descrizioni prodotto (`website_description`) toglie gli `id`, anche
  scritti dal sistema: ancore da impostare via JS.
- La scheda prodotto riscrive l'URL con la variante (`?filtrazione-…`) e cancella l'hash.
- Se la versione del modulo in locale è già quella nuova, una migrazione aggiunta dopo non
  riparte: eseguirla a mano da `odoo shell`. In produzione parte normalmente.
- Odoo 20: i redirect 301/302 di `website.rewrite` valgono solo se nessuna rotta risponde
  (fallback 404); `/shop/<slug>-<id>` usa l'ID finale, quindi un vecchio ID esistente vince.
- Il popup di Odoo mette il focus sul secondo elemento attivabile (presume che il primo sia
  la X): nella barra dei cookie la X va per prima.
- Il metodo `get_current_website()` non esiste in Odoo 20: usare `self.env.website`.
- L'url di `website.page` è tradotto: cercare le pagine nella lingua del sito, come fa
  `_get_page_info`.
- libsass calcola `1.25rem + 2.2vw` dentro `clamp()` e fallisce: scrivere `calc(...)`.
- Odoo mette in cache le pagine pubbliche e la sitemap (12 ore): dopo un cambio, le verifiche
  da anonimo possono vedere la versione vecchia.
- Lo script di collaudo deve impostare il cookie `website_cookies_bar`: la barra dei
  cookie copre i pulsanti.
- Il modulo campagne esegue `_install_request_campaign_pages` a ogni `-u`: i cambi di testo
  vanno resi "una volta sola" con un passo nel backup (`visual_bullets_copy_v1`,
  `opening_facts_v2`) o un attributo sullo snippet (`data-hero-facts`).
- Template generici del tema che ereditano `website.layout` valgono per tutti i siti del
  database: agganci xpath robusti (`//header//t[...]`) e template di intestazione/footer
  legati al sito Torrepulia (`_torrepulia_scope_navigation`).
- In Git Bash gli heredoc con apici e caratteri speciali (€) si rompono: scrivere gli script
  in un file nella scratchpad ed eseguirlo.
