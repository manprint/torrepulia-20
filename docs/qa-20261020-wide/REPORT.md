# Fascia bianca laterale — 20 ottobre 2026

Correzione applicata su **localhost:8069**, database **torrepulia_cinematic_install**.

La sezione `.section-pad` del tema originale ha `max-width: 1920px` e margini
automatici: a 2074 px produceva **77 px bianchi per lato**. Riprodotto il problema
con lo stesso offset dello screenshot. Non dipendeva dalla sidebar aperta.

Nel modulo di integrazione grafica è stata aggiunta una regola per le sole sezioni
editoriali principali sopra 1920 px: sfondo esteso al viewport e padding compensato
per mantenere invariati posizione e larghezza dei contenuti. Nessuna modifica al
tema originale, al core o ai contenuti salvati nel Website Builder.

## Controlli effettivi

| Viewport | Bordo sinistro sezione | Larghezza sezione | Inizio contenuto | Esito |
|---|---:|---:|---:|---|
| 2074 px | 0 px | 2074 px | 141 px, conservato | Passato |
| 2560 px | 0 px | 2560 px | 384 px, conservato | Passato |
| 1440 px | 0 px | 1440 px | 64 px | Passato |
| 390 px | 0 px | 390 px | 22 px | Passato |

Nessun overflow orizzontale. Verificata anche apertura/chiusura della sidebar:
la pagina resta allineata. Nessun errore JavaScript. Evidenze in `checks.json`,
script riproducibile `browser_qa.py`, screenshot prima/dopo e mobile nella cartella.
Non ripetuti test backend: modifica esclusivamente CSS/manifest.

## File e aggiornamento

- `custom/website_torrepulia_request_theme/__manifest__.py`: versione **20.0.1.2.1**, asset aggiunto;
- `custom/website_torrepulia_request_theme/static/src/scss/full_width_sections.scss`: nuova regola;
- `custom/website_torrepulia_request_theme/README.md` e questa cartella di evidenze.

Eseguito `-u website_torrepulia_request_theme` sul Compose locale, con riavvio
del servizio della 8069. Log `upgrade.log`. Nessuna migrazione di dati o deploy
in produzione. Ricaricare il browser con **Ctrl+F5**.
