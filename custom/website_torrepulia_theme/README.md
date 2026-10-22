# Torrepulia: Mediterranean Cinematic

Modulo Odoo 20 `website_torrepulia_theme`, versione **20.0.3.6.0**.
Stack locale: http://localhost:8069, database `torrepulia_cinematic_install`.
Con piu database selezionare prima `/web/login?db=torrepulia_cinematic_install`.

## Struttura

- `models/`, `controllers/`, `data/`: provisioning, prodotti reali e prezzi contestuali.
- `views/cinematic*.xml`: homepage, header/footer e commerce nativo.
- `views/snippets/`: blocchi necessari alle pagine istituzionali e ai form.
- `static/src/cinematic/`: fotografie, film responsive, icone e licenze.
- `static/src/js/`, `static/src/scss/`, `static/src/xml/`: frontend ed editor Odoo.
- `docs/source/`: fonti aziendali e testi legali usati dal provisioning.
- `tools/`: produzione media e regressioni locali; nessuna dipendenza runtime.

Homepage e nove altre pagine sono gia pubblicate. Shop, schede, quantita,
disponibilita, carrello e checkout sono nativi `website_sale`. Gli aggiornamenti
non riscrivono pagine salvate nel Builder. Nessun import automatico del catalogo.

## Aggiornamento

```powershell
cd ..\torrepulia-20-local-dev
docker compose up -d
.\scripts\upgrade-module.ps1 -Module website_torrepulia_theme
```

Dipendenze: `website`, `website_sale`, `website_sale_stock`, `website_crm`.
Nessuna patch al core o framework frontend esterno.

## Editor e Asset

Testi, foto, collegamenti e ordine delle sezioni sono modificabili nel Builder.
La CTA della sezione La Regina e un pulsante nativo: testo e URL sono
modificabili direttamente dal builder. La selezione Prodotti Torrepulia
controlla i formati dinamici, le cui immagini provengono dalle schede prodotto.
I prezzi dinamici non vengono salvati nell'HTML. Se si sostituisce la foto
hero/territorio, il vecchio film non copre il nuovo upload. I film sono
animazioni fotografiche degli originali, non riprese documentarie.

[Inventario e materiali mancanti](docs/ASSETS.md).
[Baseline e collaudo](docs/STABILIZATION.md).
[Navigazione, sistema visivo e procedura reversibile del menu](docs/navigation-design-system.md).
[Disponibilita e badge configurabili dei formati](docs/formats-availability.md).
[Prove di valore, prenotazione e aggiornamento reversibile dei contenuti](docs/reservation-campaign.md).

## Regressione Locale

```powershell
python custom/website_torrepulia_theme/tools/inspect_compiled_css.py
python custom/website_torrepulia_theme/tools/final_home_qa.py final
python custom/website_torrepulia_theme/tools/final_builder_qa.py
python custom/website_torrepulia_theme/tools/release_check.py
python custom/website_torrepulia_theme/tools/release_browser_qa.py
```

Eseguire dalla root con Python, Playwright e Chromium. I test Builder usano
account QA e bozza privata; il cleanup disattiva l'account. Screenshot e video
di test possono essere salvati fuori dal modulo impostando `TORREPULIA_QA_IMAGES`.
Non confermare ordini o pagamenti reali. La home pubblicata non viene modificata.
La cache axe resta nella cartella temporanea del sistema (personalizzabile con
`TORREPULIA_QA_CACHE`), non negli asset del modulo. Gli inventari runtime
contengono copie delle viste: vanno archiviati fuori dal repository dopo la pulizia.

La versione `20.0.3.2.0` include home, Radici e La Peranzana aggiornate, foto
WebP e snippet Bootstrap modificabili. Le pagine gia salvate nel database
mantengono la proprieta del builder: l'upgrade non le sostituisce con i default.
I tool di pubblicazione locale richiedono flag espliciti e creano un backup;
non fanno parte dell'esecuzione ordinaria del sito.

## Go-Live

Configurare pagamento, fiscalita, spedizioni, stock e SMTP. Confermare testi
legali, campagna olio nuovo, attualita delle etichette e liberatorie. Servono
foto della confezione sei bottiglie. I due loghi utilizzati sono conservati:
oro/bianco su hero e footer scuro, blu-grigio nell'header su sfondo chiaro.
Safari/iOS fisico e matrice fiscale completa non sono certificati dai test locali.
Il catalogo locale mostra attualmente prezzi in USD: verificare la configurazione
commerciale prima della pubblicazione.

## Scheda prodotto boutique (20.0.3.9.0)

Direzione approvata il 22/10/2026. Sulla scheda di ogni formato La Regina:

- **Formato**: elenco dei prodotti con nome formato Torrepulia; ogni voce apre la
  propria scheda nativa e mostra prezzo, prezzo al litro e, con l'addon campagna,
  lo stato "In prenotazione". Sostituisce "Gli altri formati".
- **Filtrazione**: varianti native con attributo a pillole, mostrate come
  interruttore a due voci. Il carrello tiene righe distinte per variante.
- **Rassicurazioni** sotto il pulsante; la nota di spedizione si modifica in
  Website → Siti → campo "Nota spedizione sulla scheda prodotto".
- **Carta d'identità dell'olio**: eCommerce → Prodotti → Carte d'identità dell'olio,
  assegnata al prodotto nella scheda Torrepulia. Acidità, perossidi, K232 e K270
  sono disegnati in scala rispetto al limite UE dell'extravergine; i valori a zero
  non compaiono. La migrazione crea "Raccolto 2024" (Frantoio Sacco Oliveti,
  19/11/2024) e lo assegna ai formati che non ne hanno uno.
- Wishlist e tabella nativa "Specifiche" sono nascoste nel tema.

Configurazione della filtrazione nel catalogo:

1. Vendite → Configurazione → Attributi: "Filtrazione", varianti istantanee,
   tipo pillole, valori Filtrato (primo) e Non filtrato, nessun sovrapprezzo.
2. Aggiungere l'attributo a ogni formato. **Odoo archivia la variante esistente e
   ne crea due nuove**: giacenze, campagne e regole riferite alla vecchia variante
   vanno riportate sulle nuove (inventario, righe della campagna olio nuovo).
3. Unità base e quantità (per esempio L e 5) vanno impostate **su ogni variante**:
   con più varianti il modello non le conserva. Attivare il prezzo di riferimento
   nelle impostazioni eCommerce per mostrare il prezzo al litro.
