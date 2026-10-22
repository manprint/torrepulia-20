# CAP o Città e sidebar della richiesta — 20 ottobre 2026

Applicato su **localhost:8069**, database **torrepulia_cinematic_install**.
Modulo `website_torrepulia_request` aggiornato a **20.0.1.9.0**.

## Risultato

- Nuovo campo **CAP o Città**, testo libero facoltativo, massimo 256 caratteri,
  nel modulo condiviso di `/la-tua-richiesta` e `/prenotailtuoolio`.
- Micro-testo a 11 px, grigio: «Necessario esclusivamente per una stima indicativa
  delle spese di spedizione.» Nessun controllo rigido su CAP, strade o località.
- All'invio l'area, normalizzata negli spazi, viene anteposta alle note come
  `CAP o Città: …`. Resta nelle note della richiesta e nella **descrizione
  dell'opportunità CRM**, insieme alle note del cliente. Non viene creata una
  località o un contatto a partire da questo testo.
- I commerciali possono usare l'indicazione nelle note per ricercare e organizzare
  le richieste per zona. Non è introdotto un raggruppamento geografico automatico
  o un calcolo automatico del trasporto.
- Il clic ordinario su **La tua richiesta** nell'header apre una sidebar modale
  dalla destra, senza cambiare pagina. Mostra immagini, prodotti, configurazioni,
  quantità, eventuali avvisi e importi nativi quando abilitati.
- **VAI AL RIEPILOGO** apre la pagina completa attraverso il percorso centralizzato
  del website. Chiusura tramite croce, Esc o sfondo su desktop; focus restituito
  al collegamento nell'header. Tab rimane nei controlli della sidebar.
- Su mobile la sidebar occupa la larghezza disponibile; elenco scorrevole e
  chiusura/riepilogo sempre separati dal contenuto. La modalità standard conserva
  il comportamento nativo; il link mantiene anche il normale href di fallback.

## Aggiornamento e dati

Eseguito sul Compose locale reale `torrepulia-20-local-dev`:

```text
odoo -d torrepulia_cinematic_install -u website_torrepulia_request --stop-after-init --no-http --max-cron-threads=0
```

Log: `upgrade.log`. Nessuna nuova colonna o migrazione dei record storici.
Le richieste già inviate restano inalterate. Il limite pubblico delle note rimane
5000 caratteri; il confine interno ammette 5300 per includere anche l'etichetta e
l'area facoltativa, senza troncare il testo del cliente.

Backup preventivi in `C:\Users\salvatore.leone\Downloads\torrepulia_odoo20\backups`:

- `torrepulia_before_drawer_20261020.dump`;
- `torrepulia_filestore_before_drawer_20261020.tar.gz`.

La sidebar legge gli endpoint privati della selezione corrente: non usa il
carrello e-commerce e non crea ordini, opportunità, prenotazioni o pagamenti.
Nessun aggiornamento al core, al tema originale, al dominio, a HTTPS o alla SEO.
Ricaricare completamente il browser con **Ctrl+F5** per i nuovi asset.

## Matrice dei controlli

| Scenario | Esito | Evidenza |
|---|---|---|
| Header: apertura senza navigazione, richiesta vuota | Passato | `checks.json` |
| Sidebar con due prodotti, quantità 2 e 1, importi EUR | Passato | `drawer-desktop.png`, risposta autorevole server |
| Esc, ripristino focus e ciclo Tab | Passato | Test browser con sei Tab consecutivi |
| Sidebar mobile 390 px | Passato | `drawer-mobile.png`, footer visibile e larghezza nel viewport |
| VAI AL RIEPILOGO | Passato | Apertura della pagina completa con entrambe le righe |
| Campo facoltativo e supporto a 11 px | Passato | DOM/CSS verificati, `contact-desktop.png`, `contact-mobile.png` |
| Invio del campo nel payload e conservazione dopo errore | Passato | Risposta 422 simulata; nessun invio CRM nel database di lavoro |
| Secondo visitatore anonimo | Passato | Sidebar vuota in un contesto browser separato |
| Campo nel modulo stagionale | Passato | Verifica della pagina reale con selezione condivisa |
| CAP/Città → note richiesta e descrizione CRM | Passato | Test HTTP reale sul database separato |
| Area manipolata, note di 5000 caratteri e ritentativo | Passato | Array respinto; note conservate; area salvata una sola volta |
| JavaScript | **38/38 passati** | `js-tests.log` |
| Classe Odoo revisione/invio | 8 eseguiti: 7 passati, 1 timeout | `odoo-tests.log` |
| Ripetizione del test in timeout | **1/1 passato**, zero errori | `odoo-retest.log` |
| Controllo statico design | Nessun rilievo | `design-detect.json` |

La prima compilazione ha segnalato un'incompatibilità Sass con `max()` e
`env(safe-area-inset-bottom)`: corretta usando una formula `calc()` compatibile.
Il successivo controllo nel browser e la ripetizione Odoo usano gli asset
compilati correttamente. Il timeout iniziale riguarda un test autenticato
preesistente; la sua ripetizione è passata. Non si dichiara una seconda esecuzione
completa degli otto test.

I test Odoo sono stati eseguiti soltanto su **torrepulia_request_test**. Il test
nel browser usa un destinatario `example.invalid` e intercetta l'invio finale:
non crea un lead né invia email nel database di lavoro. Nessun pagamento reale.
Non è stato ripetuto un ciclo completo del Website Builder o un audit con lettore
di schermo in questa revisione. I controlli visuali nuovi sono a 1440 e 390 px.

## File modificati

Nel modulo `custom/website_torrepulia_request/`:

- `__manifest__.py`, `README.md`;
- `models/review.py`, `models/request.py`;
- `views/review.xml`;
- `static/src/js/review.js`;
- `static/src/js/request_drawer.js` — nuovo;
- `static/src/scss/review.scss`;
- `static/src/scss/request_drawer.scss` — nuovo;
- `tests/test_review.py`;
- `tests/test_request_drawer.mjs` — nuovo.

Documentazione: `docs/TORREPULIA_RICHIESTE_GUIDA.md` e questa cartella con script
di collaudo, log e screenshot.
