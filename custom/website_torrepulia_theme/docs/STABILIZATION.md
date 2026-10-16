# Collaudo Home, 16 Ottobre 2026

Composizione autorevole: home salvata nel database `torrepulia_cinematic_install`
su http://localhost:8069. Testi e fotografie del proprietario preservati.
Rimosso il giustificato dalla descrizione La Regina nel database e nei default
dello snippet; allineamento a sinistra verificato nel browser.

Il collaudo corrente sostituisce, per la home, i report storici dell'11 ottobre.
Questi ultimi e le vecchie istantanee sono conservati nell'archivio esterno
indicato nel [registro di pulizia](qa-final/cleanup-results.json).

## Prove Ripetibili

Dalla root del repository, con Python, Playwright e Chromium:

```powershell
python custom/website_torrepulia_theme/tools/inspect_compiled_css.py
python custom/website_torrepulia_theme/tools/final_home_qa.py final
python custom/website_torrepulia_theme/tools/final_builder_qa.py
```

Impostare `TORREPULIA_QA_IMAGES` per tenere le catture fuori dal modulo.
Il test pubblico non crea ordini. Il builder usa un account temporaneo e una
copia privata non indicizzata: verifica salvataggio e foto modificabile,
elimina la copia e disattiva l'account anche in caso di errore.

[Report finale](qa-final/report.md).
[Browser](qa-final/final-results.json).
[Builder](qa-final/builder-final-results.json).
[Archivio e pulizia](qa-final/cleanup-results.json).

## Limiti

Non sono certificati pagamenti reali, matrice fiscale, Safari/iOS fisico o
accessibilita con tecnologie assistive reali. Il catalogo locale mostra USD;
non sono state cambiate valute, tasse, disponibilita o prezzi.
La confezione reale da sei bottiglie richiede ancora una fotografia confermata.
