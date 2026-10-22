# Banner garanzie — 21/10/2026

Installato sulla **8069**, database `torrepulia_cinematic_install`, modulo
`website_torrepulia_request_campaign` **20.0.1.5.1**. [Stato modulo](module.txt),
[aggiornamento](upgrade.log). Nessun deploy in produzione.

Il banner è un div dedicato con lista semantica interna: sfondo #f4f2ee,
raggio 8 px, padding 20 px verticale / 40 px orizzontale, massimo 900 px,
centrato e con margine laterale anche alle larghezze inferiori. Icone outline
32×32 px verde #3d4a3e, allineate al centro dei testi. La carta di credito è
sostituita da una spunta cerchiata. Copy invariato.

Hero: titolo con margine inferiore 24 px e interlinea 1.2. Titolo formati:
margine inferiore 20 px. Descrizione: margine inferiore 32 px, coerente con
l'ultimo esempio CSS richiesto; banner a 40 px dalle card. Le regole dei titoli
e della descrizione sono circoscritte allo snippet e prevalgono sulle regole
generali del tema, senza modificare il tema originale o le pagine salvate.

## Matrice dei controlli

| Scenario | Risultato | Evidenza / limite |
| --- | --- | --- |
| Installazione locale | Superato | Modulo installato 20.0.1.5.1 |
| Desktop 1440: banner centrato 900 px, riga orizzontale | Superato | [Banner](banner-1440.png), [pagina](page-1440.png) |
| Tablet 768 | Superato | [Pagina](page-768.png) |
| Mobile 390 e 360: colonna centrata, nessun overflow | Superato | [390](page-390.png), [360](page-360.png), [banner mobile](banner-390.png) |
| Padding, raggio, colore, dimensioni SVG, spazi sopra/sotto e titoli | Superato | Misure computed style / DOM in [checks.json](checks.json) |
| Tre icone, terza con check; testi invariati | Superato | Browser e screenshot ispezionati |
| Quantità card → riepilogo senza reload | Superato | Browser: aggiunta di una confezione, selezione QA poi svuotata |
| Test HTTP prodotti/prezzi/isolamento selezione e anteprima Builder senza dati personali | **2/2 superati** | [Log Odoo](odoo-tests.log), database isolato `torrepulia_request_test` |
| Errori JavaScript nel percorso provato | Nessuno | [checks.json](checks.json) |
| Rilevatore stile | Nessuna segnalazione | [design-detect.json](design-detect.json) |
| Salvataggio e duplicazione interattivi nel Builder | Non rieseguiti | Solo anteprima HTTP isolata verificata; nessun handler Builder modificato |

Il primo controllo delle misure ha rilevato interlinea e margine della descrizione
sovrascritti dal tema: corretti e verifica finale completata a tutte e quattro le
larghezze. Nessun invio richiesta, email o pagamento durante il controllo browser.

## File modificati e aggiornamento

- `custom/website_torrepulia_request_campaign/views/snippet.xml`
- `custom/website_torrepulia_request_campaign/static/src/scss/campaign.scss`
- `custom/website_torrepulia_request_campaign/__manifest__.py`
- `custom/website_torrepulia_request_campaign/README.md`
- Questa cartella: report, script di verifica, log e screenshot.

Eseguito `-u website_torrepulia_request_campaign` e riavvio Odoo. Non occorrono nuove
dipendenze né migrazioni aggiuntive dei contenuti. Il banner è renderizzato a
runtime; le personalizzazioni già salvate rimangono inalterate. Backup precedente:
`C:/Users/salvatore.leone/Downloads/torrepulia_odoo20/backups/torrepulia_before_seasonal_banner_20261021.dump`.
