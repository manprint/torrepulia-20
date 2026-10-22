# Handoff Torrepulia: stato al 23/10/2026

Documento di ripresa per la prossima sessione di lavoro. Ultimo commit deployato: vedi `git log` (Fase 2 punto 1, shop a righe e olio nuovo).

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
2. **27/10:** home con i formati e i prezzi subito dopo "La Regina"; checkout Odoo
   (indirizzo, pagamento, conferma) con colori e caratteri del tema.
3. **28/10:** microinterazioni con le skill di Emil Kowalski, poi nuovo audit Impeccable.
4. **29-30/10:** collaudo completo (acquisto e prenotazione di prova, telefono e
   desktop), deploy. Poi SEO di base e analytics.

Rimasti dall'audit (P2/P3): token di colore nei moduli richiesta/campagna (circa 130
hex fissi), CSS/JS pesanti da verificare con compressione in produzione.

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
- Test Odoo (119 al 23/10):
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
