# Prenota il tuo olio: copy e icone — 21/10/2026

Applicato a `http://localhost:8069/prenotailtuoolio`, database
`torrepulia_cinematic_install`, addon `website_torrepulia_request_campaign`
installato **20.0.1.5.0** ([stato](module.txt)). Nessun deploy in produzione.

## Risultato

Hero e introduzione riportano il copy richiesto. Tra H2 e prodotti compare una
sola lista semantica di tre visual bullet: lucchetto, ramoscello e carta con check.
SVG decorativi nascosti alle tecnologie assistive; titoli e sottotesti restano
normale testo accessibile. Font Manrope, titoli 13 px / 700, descrizioni 12 px,
colori richiesti e icone verde #3d4a3e. Margini verticali 24 px. Rimosse le
rassicurazioni duplicate nelle card e l'ulteriore paragrafo di consegna.
Il testo della campagna rimane configurabile dal backend.

## Controlli eseguiti

| Scenario | Risultato | Evidenza / limite |
| --- | --- | --- |
| Installazione e aggiornamento database locale | Superato | [Upgrade](upgrade-translations.log), [modulo](module.txt) |
| Copy esatto hero e introduzione italiana salvata | Superato | [Browser](checks.json), [desktop](page-1440.png) |
| Lista unica, 3 SVG, niente ripetizioni nelle card | Superato | Browser e test HTTP |
| Desktop 1440 e tablet 768: riga orizzontale | Superato | [1440](page-1440.png), [768](page-768.png) |
| Mobile 390 e 360: colonna centrata | Superato | [390](page-390.png), [360](page-360.png) |
| Margini 24 px, nessun overflow orizzontale | Superato | Misure DOM in [checks.json](checks.json) |
| Aggiunta da card aggiorna riepilogo senza reload | Superato | Browser, selezione anonima QA poi svuotata |
| Errori JavaScript nel percorso provato | Nessuno | [checks.json](checks.json) |
| Migrazione idempotente, conservazione foto/titoli/SEO, successive modifiche editoriali e traduzioni | Superato | [Test Odoo](odoo-tests-final.log), [test corretto con lingua attivata](translation-migration-test.log) |
| Prezzi visibili/nascosti, isolamento, campagna chiusa, invio stagionale | Superato | Test HTTP su database isolato; email intercettate, destinatari `.invalid` |
| Rilevatore stile sulle modifiche frontend | Nessuna segnalazione | [design-detect.json](design-detect.json) |
| Apertura, duplicazione e salvataggio interattivo Builder | Non rieseguito in questa modifica | Verificati migrazione e anteprima HTTP isolata; nessun JavaScript Builder modificato |

**14 test Odoo distinti superati**: 13 nel secondo giro completo e il test di
migrazione multilingua nell'esecuzione mirata finale. Il primo giro ha individuato
un marcatore mancante nel percorso di migrazione dei vecchi snippet, poi corretto.
Il secondo ha rilevato una lingua italiana non attivata nel fixture del database di
test: corretta la preparazione del fixture, esecuzione mirata 1/1 superata. Il
browser ha inoltre rilevato inizialmente la vecchia traduzione italiana: la
migrazione ora aggiorna una volta tutte le traduzioni salvate, con backup.
Log intermedi conservati per trasparenza. Nessun invio reale dal browser;
nessun pagamento eseguito.

## File modificati

- `custom/website_torrepulia_request_campaign/__manifest__.py`
- `custom/website_torrepulia_request_campaign/models/campaign.py`
- `custom/website_torrepulia_request_campaign/models/page.py`
- `custom/website_torrepulia_request_campaign/views/snippet.xml`
- `custom/website_torrepulia_request_campaign/static/src/scss/campaign.scss`
- `custom/website_torrepulia_request_campaign/tests/test_campaign.py`
- `custom/website_torrepulia_request_campaign/tests/test_http.py`
- `custom/website_torrepulia_request_campaign/README.md`
- Questa cartella: report, script riproducibile, log e screenshot.

## Aggiornamento e recupero

Già eseguito `-u website_torrepulia_request_campaign` e riavvio sulla 8069.
Nessuna dipendenza aggiunta. Backup database precedente:
`../backups/torrepulia_before_seasonal_bullets_20261021.dump` nella directory
esterna `torrepulia_odoo20`. Contenuti precedenti anche nella copia amministrativa
`website.torrepulia_campaign_page_backup`; il copy viene aggiornato una sola volta,
così i successivi salvataggi editoriali sono preservati. La foto, la disposizione
e i prodotti configurati dal gestore sono rimasti invariati.
