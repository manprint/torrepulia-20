# Consegna issue base — 18 ottobre 2026

Report storico della versione `20.0.1.0.0`. Per la successiva issue del servizio
condiviso (`20.0.1.1.0`) vedere [QA-selection.md](QA-selection.md).

Implementata la base funzionale nel nuovo addon `website_torrepulia_request`.
Non sono stati modificati file del tema, core, configurazione staging o dati del
database `odoo_dev`. Il database aggiunto per le verifiche è
`torrepulia_request_test`, sul PostgreSQL 17 locale.

## File aggiunti

- `__init__.py`: caricamento del modulo;
- `__manifest__.py`: versione, dipendenze e risorse;
- `models/__init__.py`: caricamento dei modelli;
- `models/website.py`: configurazioni website/settings e risoluzione sicura sessione;
- `models/request.py`: richieste, righe, snapshot, invio finale, cron, legami CRM/Vendite;
- `security/ir.access.csv`: permessi e restrizioni nel formato effettivo Odoo 20;
- `data/request_data.xml`: sequenza e cron giornaliero;
- `views/settings.xml`: impostazioni del website;
- `views/request.xml`: elenco/dettaglio commerciale e relazione dalla scheda CRM;
- `tests/__init__.py`: caricamento dei test;
- `tests/test_request.py`: suite di regressione e sicurezza;
- `README.md`: architettura, contratti privati, installazione, aggiornamento e limiti;
- `QA.md`: questo report;
- `test-results.txt`: estratto del log dell’ultima esecuzione Odoo.

## Risultati effettivi

Installazione e aggiornamento del modulo sul database dedicato completati.
Odoo `20.0-20260926`: **13 test, 0 fallimenti, 0 errori**.
Le righe “Access Denied” nel log sono attese dai test di accesso negativo.
La voce statistica “15 tests” di Odoo include i due passaggi di setup della suite;
il riepilogo dei casi applicativi è quello da 13 test.

Copertura:

1. Configurazioni indipendenti su due website e campi settings correlati;
2. Modalità standard di default e assenza di selezione richiesta quando disattivata;
3. Selezione senza ordini, opportunità, contatti o email, prezzo catalogo invariato;
4. Token server di sessione, rifiuto ID numerico e token di altro website, rotazione dopo invio;
5. Invio finale con una sola opportunità e snapshot immutabile, origine/UTM conservati;
6. ACL pubblico e portale su creazione/lettura/scrittura/eliminazione richieste e righe;
7. Commerciale del team autorizzato a leggere/scrivere bozze, accesso negato fuori team;
8. Isolamento aziende anche per responsabile Vendite e rifiuto prodotti/team incompatibili;
9. Intero catalogo pubblicato, rifiuto non pubblicati/altro website/quantità non finite;
10. Variante effettiva, attributi senza variante e testo personalizzato nativi;
11. Bozze scadute eliminate, sessione scaduta rifiutata, richieste inviate e CRM preservati;
12. Contatto autenticato e catalogo riservato agli utenti con login;
13. Validazione configurazioni, contatti finali e collegamenti ai preventivi nativi.

Compilazione Python (`compileall`), parsing XML e `git diff --check` completati
senza errori. Odoo ha validato le viste durante installazione/aggiornamento.

## Controlli non eseguiti e perimetro

- Browser controllabile non disponibile (`cua.listBrowsers()` restituisce lista
  vuota): nessuno screenshot o controllo visivo interattivo prodotto.
- Nessun test di carico o test concorrente con due connessioni DB: i lock vengono
  esercitati funzionalmente; è verificato il rifiuto del secondo invio sequenziale.
- Nessuna prova email o pagamento esterno; la suite usa esclusivamente `.invalid`.
- Il tema non è installato nel database dedicato: la base è intenzionalmente
  indipendente. Non è stata eseguita una regressione visiva del tema.
- Questa issue non introduce gli adattatori pubblici (catalogo/prodotto/snippet,
  riepilogo e form HTTP) né il generatore assistito di preventivi. I relativi
  contratti e il vecchio form stagionale da sostituire sono descritti nel README.
  Il flag prezzi è una configurazione di base: non attivare il nuovo flusso su un
  sito esposto prima di integrare e verificare tutte le superfici pubbliche.

Nessuna dipendenza mancante per questa base. Nessun deploy in produzione.
Le istruzioni di installazione/aggiornamento sono in [README.md](README.md):
nessuna migrazione o riscrittura dei contenuti Builder è necessaria.
