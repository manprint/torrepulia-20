# Navigazione e leggibilità — 20.0.3.3.0

## Ricognizione

Verificato sul container locale `odoo:20.0`: Odoo `20.0-20260926`, commit
`7434faa93558d4f46fdda77acd1be4dfc663ea7c`. Il modulo tecnico è
`website_torrepulia_theme` (nome visualizzato: Torrepulia Premium Website Theme).
Il manifest precedente era 20.0.3.2.0; la baseline dichiarata nel README era obsoleta.

`views/cinematic.xml` eredita `website.layout` e aggiunge `.mc-chrome`,
`.mc-header` e `#mc-footer`; `views/header.xml` aggiunge `.tp-site`.
`views/branding.xml` sostituisce i loghi. Le viste shop/prodotto e
`cinematic_commerce.xml` mantengono il commercio nativo. `models/website.py`,
`cinematic.py` e `photo_campaign.py` gestiscono provisioning e precedenti migrazioni.

Nel database locale `torrepulia_cinematic_install` esistono copie website-specifiche
di `cinematic_chrome`, oltre alla vista originale. Sono presenti regole `ir.asset`
per `user_theme_color_palette.scss` e `user_values.scss`. Le pagine pubblicate
sono composizioni materializzate del Builder, non semplici chiamate agli snippet.
Non vanno sostituite aggiornando `arch_db`.

Gli asset sono dichiarati nel manifest: `web.assets_frontend`,
`web._assets_primary_variables` e `website.website_builder_assets`.
Gli stili `.tp-site.tp-cinematic` erano distribuiti tra `theme.scss`,
`cinematic.scss`, `cinematic_odoo.scss`, `brand_direction.scss` e fogli editoriali.
I menu desktop/mobile erano hardcoded e diversi; due selettori con `!important`
nascondevano tutti i figli degli elementi header/footer tranne quelli del tema.

## Implementazione

`design_system.scss`, ultimo foglio frontend del modulo, definisce i token
semantici e gli alias per gli snippet esistenti: palette, larghezze, scala fluida,
spaziatura e controlli. Mantiene Caslon/Manrope e fotografie. L'oro originale
rimane decorativo; `#746014` è la variante scura per testo/focus su fondi chiari.

La nuova vista `navigation_layout` opera sul layout combinato, incluse le copie
specifiche del website, senza scrivere le loro architetture. Esclude con `t-if`
soltanto le chiamate al navbar desktop/mobile e il footer standard quando
`torrepulia_theme_enabled` è attivo. Restano disponibili disclaimer, preferenze
cookie e account. I selettori nativi di lingua/listino sono richiamati nel footer
del tema; il copyright aziendale esistente resta invariato. La classe
`.top_menu` è necessaria anche al bootstrap minimale di Odoo 20;
`o_no_autohide_menu` lascia al tema la gestione dei breakpoint.

Desktop/mobile chiamano lo stesso template basato su `website.menu`, con nomi
tradotti, visibilità nativa, `_clean_url()` e `_is_active()`. I sottomenu usano
`details/summary`, evitando destinazioni fittizie. Le categorie e i megamenu non
sono stati introdotti in questo intervento. Il carrello conserva gli agganci
`o_wsale_my_cart` e `my_cart_quantity`. Il footer usa le pagine esistenti del sito,
verificandone website e visibilità con la stessa strategia del menu nativo.
I collegamenti documentali e i recapiti già presenti sono spostati con
`position="move"`, supportato dal codice installato, conservando etichette e URL
personalizzati senza duplicarli o scrivere le architetture salvate.

Il mobile usa Bootstrap Collapse già incluso in Odoo. Enter/Spazio aprono,
il primo link riceve il focus, Escape chiude e restituisce il focus; clic esterno,
uscita del focus e passaggio al desktop chiudono il pannello. Non è una modale:
Tab può proseguire nella pagina.

## Aggiornamento e contenuti

Eseguire esclusivamente nell'ambiente desiderato, con backup ordinario del DB:

1. Aggiornare il codice del modulo e lanciare `odoo -d DATABASE -u website_torrepulia_theme --stop-after-init --no-http` con le opzioni DB del proprio ambiente.
2. Riavviare il servizio Odoo. Non sono necessarie cancellazioni manuali degli asset.
3. Aprire Odoo shell sul medesimo DB ed eseguire la procedura sottostante.

```python
import runpy
tool = '/mnt/torrepulia/custom/website_torrepulia_theme/tools/navigation_content.py'
backup = '/var/lib/odoo/torrepulia-navigation-before.json'
runpy.run_path(tool, init_globals={'env': env, 'action': 'plan'})
# Dopo aver verificato il piano:
runpy.run_path(tool, init_globals={
    'env': env, 'action': 'apply', 'backup_path': backup,
})
```

Adattare solo i percorsi al deployment. La procedura risolve il website tramite
l'external ID della homepage del modulo e richiede una destinazione univoca per
ciascuna voce prevista. Rinomina/ordina le voci, esclude Home e Territorio dal
menu principale (rimangono raggiungibili da logo/footer), marca Olio nuovo come
stagionale. Non crea o elimina pagine, menu o prodotti. Non cambia URL delle
pagine, indicizzazione, pubblicazione o impostazioni commerciali. Le etichette
base sono aggiornate nel contesto `en_US`, già usato dai contenuti italiani del
modulo; le traduzioni esistenti restano intatte. Verificare le traduzioni nel menu
nativo per eventuali nuove etichette nelle altre lingue.

Il backup JSON è creato in modo esclusivo prima delle scritture, fuori dal modulo.
Una seconda applicazione non modifica nulla. Se il piano non coincide con le
personalizzazioni desiderate, configurare invece le voci dal backend nativo.

Ripristino dei soli campi modificati, con verifica di database, sito e stato:

```python
runpy.run_path(tool, init_globals={
    'env': env, 'action': 'restore', 'backup_path': backup,
})
```

Il ripristino si interrompe se i menu hanno subito ulteriori modifiche ai campi
interessati; non sovrascrive tali modifiche. Conservare il backup originale.

La voce stagionale è disattivata per default: nel form tecnico del website usare
**Show seasonal oil menu**. Nei form nativi `website.menu` sono disponibili
**Exclude from Torrepulia navigation** e **Torrepulia seasonal menu**.
Nessuna di queste opzioni legge disponibilità o giacenze. I campi sono per sito
o per record menu, mai parametri globali.

## Verifiche ripetibili

```powershell
$env:TORREPULIA_QA_IMAGES = 'C:/percorso/esterno/qa'
python custom/website_torrepulia_theme/tools/navigation_qa.py
python custom/website_torrepulia_theme/tools/final_builder_qa.py
```

Il primo script usa il DB locale `torrepulia_cinematic_install`, deriva il link
prodotto dallo shop e controlla 360/390/768/1440 px: overflow, HTTP, menu coerenti,
assenza di placeholder nei nuovi componenti, carrello, footer, tastiera e errori JS.
Il secondo crea una copia privata temporanea della home e un account QA,
prova editor/media/salvataggio e pulisce la copia; il suo report ordinario è in
`docs/qa-final`. Non conferma ordini né pagamenti.

Per il risultato della sessione vedere il report di verifica consegnato con
l'issue. Nessun deploy in produzione è incluso.
