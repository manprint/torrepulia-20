# Torrepulia Premium Website Theme

Addon Odoo 20 nativo per il tema e-commerce Torrepulia.

## Installazione locale

Lo stack locale in `torrepulia-20-local-dev` monta live `custom/` dal repository.

```powershell
cd C:\Users\salvatore.leone\Downloads\torrepulia_odoo20\torrepulia-20-local-dev
.\scripts\upgrade-module.ps1 -Module website_torrepulia_theme
```

Aprire poi `http://localhost:8069`, aggiornare l'elenco applicazioni se necessario e installare il modulo.

## Contenuti

- 11 snippet editabili nel gruppo Website Builder `Torrepulia`.
- Homepage iniziale disponibile su `/torrepulia-home`.
- Vetrina prodotti basata sullo snippet dinamico standard `website_sale.s_dynamic_snippet_products_grid`.
- Stili premium per header, footer, catalogo, card prodotto e pagina prodotto.
- Immagini locali tratte dal sito pubblico Torrepulia consultato durante l'audit.

## Odoo e Owl

Versione Odoo verificata nello stack locale: `20.0-20260926`.

Il container include `web/static/lib/owl/owl.js` e `web/static/src/owl2/owl3_compatibility_layer.js`, ma non espone un `package.json` Owl con versione semantica verificabile. Non sono stati introdotti componenti Owl custom: per hero, sezioni editoriali, formati e processo produttivo i template QWeb nativi sono più stabili e completamente compatibili con Website Builder. La parte e-commerce resta affidata a `website_sale`.

## Limiti noti

- La homepage viene creata su `/torrepulia-home` per evitare di sovrascrivere una home già presente nel database. Può essere impostata come pagina principale da Website.
- La newsletter è un blocco editoriale con CTA contatti; può essere sostituita con lo snippet mailing standard se `website_mass_mailing` è installato e configurato.
- I link prodotto dei formati puntano allo shop generale perché gli ID prodotto variano per database.

## Test eseguiti

- XML parse locale dei file in `views/`: OK.
- Installazione modulo su stack locale `torrepulia-20-local-dev`, database `odoo_dev`: OK.
- Riavvio servizio Odoo locale: OK.
- Verifica HTTP `http://localhost:8069/torrepulia-home`: 200, contenuti tema presenti.
- Verifica HTTP `http://localhost:8069/shop`: 200, classe tema shop presente.

## Note di verifica

Durante l'installazione sono stati corretti XPath non compatibili con Odoo 20 per homepage, header, tile prodotto e scheda prodotto. Le personalizzazioni e-commerce finali usano CSS e classi native per preservare i flussi standard di `website_sale`.

Non sono stati eseguiti test browser completi su checkout e Website Builder visuale con login interattivo. Il modulo registra gli snippet in `website.snippets` e usa il building block dinamico prodotti nativo di Odoo per la vetrina commerciale.
