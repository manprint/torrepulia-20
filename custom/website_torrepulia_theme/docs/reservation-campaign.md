# Prove di valore e prenotazione olio nuovo

Versione modulo: `20.0.3.6.0`. Solo ambiente di sviluppo; nessun deploy.

## Contenuti e layout

- La fascia `s_torrepulia_value_proofs` viene materializzata subito dopo
  `s_cinematic_0`. Le altre sezioni della homepage sono preservate per ogni lingua.
- `/prenotailtuoolio` mantiene URL, website, pubblicazione e metadati. Il contenuto
  autorizzato viene sostituito con apertura, condizioni e configuratore unificato.
- Layout Grid con breakpoint a 768 px; CSS confinato alle nuove classi semantiche.
  Font Caslon per H1/H2, Manrope per testo, campi e titoli di dettaglio. Nessun
  reset globale o modifica agli stili del Bag in Box, header, shop o checkout.
- Sezioni, testi, icone SVG e foto sono contenuti degli snippet e restano nel
  Website Builder. L'immagine dell'uliveto riusa gli asset `campaign/land-*`.

Correzioni concordate: «Puglie» al posto di «Pregie» e molitura in frantoio
esterno, senza affermare che avvenga all'interno dell'azienda. Il proprietario ha
confermato il pagamento alla conferma della spedizione. Campagna 2026/2027,
prezzo di 14 euro/litro e termine di 48 ore risultano anche nei contenuti
esistenti e nell'archivio `docs/source/audit.json` della pagina originale.

I 70 euro per confezione da 5 litri sono il testo della campagna richiesto dal
proprietario. Non aggiornano prezzi dei prodotti, listini, imposte o valuta del
catalogo. Filtrato/non filtrato sono scelte della richiesta CRM, come nel form
precedente: non vengono create varianti, ordini o prenotazioni di giacenza.

## Form e riferimenti Odoo 20

Verificati sul codice installato Odoo `20.0-20260926`:

- `website/static/src/snippets/s_website_form/form.js`: invio, CAPTCHA, validita
  HTML, campi personalizzati e redirect nativi. Il pulsante e un vero `button`.
- `website/controllers/form.py` e `website_crm/controllers/website_form.py`:
  creazione CRM con contesto website/azienda/lingua e dati del visitatore.
- `website_sale/static/src/interactions/product_page.js`:
  `ProductPage.prototype.incOrDecQuantity` e `_updateMinusButtonTitle` sono
  riusati da una Interaction circoscritta al configuratore, senza invocare il carrello.

Restano i quattro nomi delle quantita del form precedente e il limite 0–100.
Nome, email, telefono, CAP/citta e privacy sono obbligatori; note facoltative.
E richiesta almeno una confezione. Validazione server limitata alle richieste
Torrepulia di questa campagna: gli altri form mantengono la gestione nativa.

## Aggiornamento esplicito dei contenuti salvati

1. Conservare il normale backup database/filestore.
2. Aggiornare `website_torrepulia_theme`, poi riavviare Odoo per controller e JS.
3. In Odoo shell sul database di sviluppo indicato, eseguire prima il piano:

```python
import runpy
run = runpy.run_path('/mnt/torrepulia/custom/website_torrepulia_theme/tools/reservation_content.py')['run']
run(env, 'plan')
```

4. Applicare con un percorso nuovo, non ancora esistente:

```python
run(env, 'apply', '/var/lib/odoo/torrepulia-reservation-before-CHANGE.json')
env.cr.commit()
```

Il file viene creato in modo esclusivo e contiene tutte le architetture originali
e applicate, incluse traduzioni differite, e i flag originali delle due viste.
La procedura usa gli external ID delle pagine, verifica lo stesso website e
blocca le due righe durante l'operazione. Nessun ID numerico viene fissato nel codice.
Una seconda applicazione non riscrive le sezioni e conserva gli interventi
successivi del Website Builder. Le nuove installazioni usano gli stessi snippet.

Il tipo `StoredTranslations` e la lettura `_get_stored_translations` sono stati
verificati nell'Odoo installato (`odoo/orm/fields_textual.py`). L'uso e limitato
alla migrazione esplicita: mantiene le diverse strutture Builder delle lingue
senza propagare indiscriminatamente una lingua sulle altre. Le scritture passano
dall'ORM e dalla validazione XML delle viste. Non vengono scritti menu, robots,
indicizzazione, dominio o altri parametri del sito.

Ripristino:

```python
run(env, 'restore', '/var/lib/odoo/torrepulia-reservation-before-CHANGE.json')
env.cr.commit()
```

Il ripristino si ferma se una pagina e stata modificata dopo l'applicazione:
occorre prima confrontare le modifiche con il backup. Non forzare la sovrascrittura.

Backup finale locale applicato:
`/var/lib/odoo/torrepulia-reservation-final-before-20261018.json`.

## Verifiche

- Runner Odoo, tag `/website_torrepulia_theme`: 16 test superati, incluse
  creazione CRM, azienda e lingua, campi obbligatori, quantita e privacy; restano
  superati i test di badge, nastri e disponibilita dei formati.
- Applicazione, seconda applicazione senza cambiamenti e ripristino verificati
  in una transazione annullata; architetture originali ripristinate esattamente.
- Browser a 360, 390, 768 e 1440 px: colonne responsive, fascia dopo la hero,
  quantita +/- con limite minimo zero, nessun overflow o errore JavaScript.
- Validazione browser di selezione vuota e privacy; payload e redirect del form
  verificati con risposta di successo simulata, senza inviare richieste allo staff.
  Rifiuto privacy verificato anche sulla route reale. Creazione effettiva CRM
  verificata dai test transazionali, senza dati di prova permanenti.
- Prove Website Builder su copie private: testo fascia, introduzione, etichetta
  telefono e selettore media. Nessun aggiornamento del catalogo o checkout.

File: `views/snippets/s_reservation_campaign.xml`, `views/snippets/s_forms.xml`,
`views/cinematic_snippets.xml`, `data/pages.xml`, `models/cinematic.py`,
`static/src/scss/reservation_campaign.scss`, `static/src/js/reservation_campaign.js`,
`controllers/reservation.py`, `controllers/__init__.py`, `__manifest__.py`,
`tools/reservation_content.py`, `tests/test_reservation.py`, `tests/__init__.py`
e questa documentazione.
