# Verifica finale del 17 ottobre 2026

Versione modulo: `20.0.3.2.0`.

## Pulizia

Inventario aggiornato di entrambi i database locali, incluse viste inattive e
versioni precedenti: nessun ulteriore asset privo di riferimenti. Conservate
le immagini utilizzate dai contenuti salvati e dalle pagine legacy.

Archiviati fuori dal modulo due inventari grezzi e la vecchia cache axe:
3 file, 3.692.760 byte. Copia completa prima dell'archiviazione in
`torrepulia-theme-cleanup-20261017-013258`, accanto al repository.
Rimossa la funzione `prepare()` non utilizzata dal helper locale, che modificava
lingua e account di test. La cache axe ora vive nella cartella temporanea di
sistema, non nel codice distribuito. Screenshot e inventari esclusi da Git.

## Esiti

- Sintassi Python e XML, file nel manifest e riferimenti statici: superati
  (`source-release-results.json`).
- CSS frontend reale compilato e restituito con HTTP 200, senza errori Sass.
- Home a 1440, 1920, 834, 390 e 320px: nessun overflow, immagine mancante,
  errore JavaScript o violazione axe rilevata nei controlli eseguiti.
  Menu, tooltip, formati, pausa/ripresa e hero statica verificati
  (`release-results.json`).
- Radici, La Peranzana e shop a 1440 e 390px: HTTP 200, nessuna risorsa
  mancante, nessun errore JS o overflow (`release-browser-results.json`).
- Prove builder su copie private delle pagine documentate nei report dedicati:
  selettore immagini e salvataggio testi funzionanti, originali invariati.
- Installazione da database vuoto con dipendenze Odoo completata.
- Upgrade sul database temporaneo alla versione `20.0.3.2.0` completato;
  hash dell'HTML di home, Radici e La Peranzana identici prima/dopo.
- Home, Radici, La Peranzana e shop verificati anche sull'installazione pulita
  a 1440 e 390px, senza errori JS, immagini mancanti o overflow
  (`clean-install-browser-results.json`). Database temporaneo e relativo
  filestore rimossi dopo la verifica; database del proprietario invariato.

Le verifiche sono locali, non una certificazione WCAG o una prova di incasso,
fiscalita, spedizioni, SMTP o compatibilita Safari/iOS su dispositivi fisici.
Valuta, catalogo, analisi e dichiarazioni commerciali restano da confermare per
il deployment reale come indicato nella documentazione del modulo.
