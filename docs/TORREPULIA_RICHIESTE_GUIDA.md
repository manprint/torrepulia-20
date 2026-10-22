# Gestire le richieste di olio

Guida operativa per Odoo 20. Configurazioni e prodotti si gestiscono
dall'interfaccia; non occorre modificare codice o inserire ID numerici.
Il collaudo e i limiti dell'ambiente sono nella [matrice](TORREPULIA_RICHIESTE_COLLAUDO.md).

## Attivazione e prezzi

1. Con un amministratore aprire **Website → Configurazione → Impostazioni**.
   Selezionare il website corretto: ogni sito conserva la propria configurazione.
2. Nella sezione **Torrepulia — Richieste di preventivo**, scegliere un **Team
   commerciale destinatario** attivo e compatibile con l'azienda del sito.
   L'**Assegnatario predefinito** è facoltativo: deve appartenere al team e avere
   accesso all'azienda. Se necessario gestire prima team e membri in CRM.
3. Scegliere **Richiesta di preventivo** come modalità commerciale. Il flusso
   comprende tutti i prodotti pubblicati e accessibili del catalogo del sito.
   Non serve una seconda lista di prodotti ammessi.
4. Impostare **Mostra prezzi nelle richieste**. Se attivo si usano listino,
   valuta e imposte del contesto Odoo; il totale prodotti non include un trasporto
   ancora da definire. Se disattivo le superfici pubbliche e la ricevuta della
   richiesta non mostrano importi. Il backend e i preventivi autorizzati mantengono
   i loro prezzi commerciali.
   Sul sito locale Torrepulia è stato configurato il listino dedicato
   **Torrepulia - EUR**: la valuta pubblica è quindi l'euro tramite le regole
   native, senza sostituzioni grafiche del simbolo. Non cambiare la valuta
   dell'azienda o i prezzi dei prodotti per modificare la presentazione.
5. Lasciare **Pagina di riepilogo** a `/la-tua-richiesta`, salvo una destinazione
   locale concordata. I componenti usano questo unico percorso. Impostare i limiti
   delle quantità e la conservazione bozze: predefinita **30 giorni**, configurabile
   da 1 a 365. La pulizia giornaliera riguarda solo bozze scadute.
6. La fase CRM iniziale è configurabile. Senza selezione viene creata **Richiesta
   web ricevuta**, limitata al team, al primo invio; le pipeline esistenti non
   vengono riscritte. Salvare le impostazioni.
7. Esaminare **Carrelli aperti al passaggio di modalità**. Il responsabile Vendite
   può aprirli con **Esamina carrelli**. Controllare anche eventuali transazioni
   già avviate e email di recupero già nella coda nativa Odoo.

## Prodotti e campagne

1. Preparare nel catalogo Odoo i prodotti e le varianti reali, pubblicandoli nel
   sito appropriato. Usare fotografie autentiche del prodotto/confezione e dati
   commerciali verificati. Non creare varianti filtrato/non filtrato se non
   corrispondono a prodotti realmente gestiti.
2. Il contenuto in litri della confezione si configura nel campo **Litri per unità
   di vendita** del prodotto/variante. Il riepilogo non deduce litri dal nome o dal
   volume logistico e non mostra come totale un dato incompleto.
3. Aprire **Website → Sito → Campagne olio nuovo → Nuovo**. Gli editor del sito e i
   commerciali autorizzati possono gestire campagne nelle proprie aziende.
   Impostare nome, riferimento univoco per sito, website e stato.
4. In **Prodotti e varianti** scegliere dal picker i formati desiderati, inizialmente
   quelli filtrati configurati dal gestore. Riordinare con la maniglia. Varianti
   diverse hanno controlli quantità indipendenti. Contenuto della confezione e
   descrizione pratica sono editoriali e non sostituiscono attributi, UoM o prezzi.
5. Compilare, solo se disponibili, periodo indicativo di consegna e testi.
   In **Indicazioni commerciali approvate** gestire le tre note mostrate con icone:
   spedizione, pagamento e prezzo. Compilarle solo con condizioni approvate.
   La nota «Prezzo bloccato garantito» è editoriale: il preventivo continua a usare
   i prezzi nativi ricalcolati dal commerciale; il campo non congela alcun listino.
   Configurare il messaggio di chiusura e le eventuali date di apertura/chiusura;
   Odoo mostra le date nel fuso dell'operatore. Per aprire la vetrina impostare
   **Aperta**, con intervallo coerente. Una campagna nuova è chiusa e senza prodotti.
6. Per chiudere scegliere **Chiusa**, oppure usare la scadenza configurata.
   La chiusura ferma solo la vetrina stagionale: catalogo e richiesta generale
   restano disponibili e i prodotti già scelti non vengono rimossi.

## Snippet della pagina stagionale

1. Aprire `/prenotailtuoolio` nel website corretto e scegliere **Modifica**.
   Selezionare lo snippet **Richiesta del nuovo raccolto**.
2. Nell'opzione **Campagna** selezionare il record dal picker. Senza scelta
   esplicita viene usata la campagna predefinita del sito. **Gestisci campagna e
   prodotti** apre la gestione dei formati in una nuova scheda; dopo le modifiche
   salvare, tornare al Builder e usare **Aggiorna
   anteprima**.
3. Modificare titolo, introduzione e fotografia direttamente nella pagina.
   Scegliere due o tre colonne desktop. L'anteprima zero/uno/più prodotti è
   dimostrativa e non altera la selezione del visitatore.
4. Si possono spostare o duplicare gli snippet. Al salvataggio vengono rimossi i
   contenuti dinamici; la pagina conserva configurazione ed editoriali, senza
   quantità personali o prezzi materializzati. Salvare e ricaricare.
5. Verificare in una sessione visitatore separata: un'aggiunta dal catalogo
   incrementa; il controllo stagionale imposta il totale. Passare da 2 a 3
   significa 3 confezioni. I prodotti estranei alla campagna restano nella richiesta.

## Ricezione, CRM e preventivo

1. Il visitatore rivede tutto in **La tua richiesta** oppure nel modulo sotto le
   card di **Olio nuovo**, modifica quantità e lascia
   nome/email, telefono, **CAP o Città** e note facoltativi. Non serve account o indirizzo completo.
   CAP o Città è testo libero per una stima della spedizione: può contenere il CAP,
   la città o entrambi. Viene riportato nelle note della richiesta e nella
   descrizione CRM con etichetta «CAP o Città», ricercabile dal commerciale.
   Non attiva verifiche stradali o una tariffazione automatica.
   Solo **CONFERMA LA MIA PRENOTAZIONE** crea l'opportunità; non conferma ordini o
   pagamenti. Entrambe le pagine usano lo stesso servizio e lo stesso invio protetto.
   Nel catalogo è possibile scegliere la quantità prima dell'aggiunta; i pulsanti
   più/meno della pagina stagionale e del riepilogo impostano la quantità totale.
   Nel catalogo e nello snippet formati, invece, il pulsante **AGGIUNGI ALLA
   RICHIESTA** aggiunge la quantità scelta sopra il pulsante (predefinita 1).
   Se configurate, scegliere esplicitamente le varianti disponibili; quelle
   complesse richiedono la scheda prodotto. Non vengono create varianti fittizie.
   La conferma mostra solo la quantità appena aggiunta e il relativo subtotale;
   **Continua a scegliere** la chiude, **VAI AL RIEPILOGO** apre la pagina contatti.
   Il clic ordinario su **La tua richiesta** nell'header apre prima una sidebar
   con il contenuto aggiornato. Usare **VAI AL RIEPILOGO** per modificarlo e
   compilare i recapiti; chiudere con la croce, Esc o clic sullo sfondo su desktop.
2. Il commerciale apre in CRM l'opportunità del team, oppure **CRM → Richieste
   website**. Nella richiesta controlla riferimento, sito, origine, recapiti,
   note e righe strutturate. La fotografia inviata rimane immutabile.
3. Usare **Prepara preventivo**. Se manca il cliente, selezionarlo o crearlo dal
   picker dopo la qualificazione: non associare automaticamente un account sulla
   sola email fornita dal visitatore.
4. **Prepara e rivedi** crea una bozza Odoo collegata all'opportunità, con prodotti,
   varianti, quantità, UoM e configurazioni supportate. Controllare cliente, azienda,
   listino, valuta, posizione fiscale, imposte, consegna e condizioni. I prezzi
   vengono ricalcolati secondo il contesto del preventivo.
5. Ripetere **Prepara preventivo** riapre il documento attivo. Per un'altra versione
   usare **Nuovo preventivo / revisione**, indicando una motivazione. La modifica
   del preventivo non riscrive la richiesta originale.

## Accettazione

- **Accordo via email:** registrare l'accettazione e gli estremi nel chatter del
  preventivo, controllare il documento e usare **Conferma** nativo.
- **Accettazione online:** configurare le opzioni native di firma e pagamento
  pertinenti, verificare il preventivo e inviarlo con Odoo. Il cliente autorizzato
  accetta nel portale secondo il comportamento standard; non c'è una seconda
  approvazione obbligatoria Torrepulia. In sviluppo usare esclusivamente provider
  Demo/non live e SMTP intercettato o destinatari di prova.

Ordine, consegna e fatturazione proseguono con i moduli Odoo installati. Una
richiesta iniziale o un preventivo appena preparato non li genera automaticamente.

## Ripristino della vendita online

Nelle impostazioni dello stesso website scegliere **Acquisto online standard** e
salvare. Carrello, checkout e recuperi tornano alle regole native. I vecchi
carrelli validi rimangono disponibili secondo sessione, accessi e stato Odoo;
non vengono fusi con le richieste. Le richieste inviate restano consultabili
internamente e non diventano ordini. Nessun dato personale viene ripubblicato.
Gli altri website mantengono le rispettive modalità.

## Vecchie pagine e aggiornamento tecnico

L'aggiornamento sostituisce i soli blocchi stagionali riconosciuti di
`/prenotailtuoolio`, preservando URL, metadati SEO, altre sezioni e foto compatibili.
Conserva un backup delle architetture originali per vista/lingua nel campo tecnico
privato `torrepulia_campaign_page_backup` del website. Un secondo aggiornamento
non riscrive i nuovi testi del selettore. Non vengono convertiti o cancellati
i lead CRM storici. I vecchi POST stagionali sono rifiutati anche da schede già
aperte; il modulo contatti generale resta indipendente.

`/richiesta-inviata` non è più una conferma generica di prenotazione: indirizza
alla ricevuta solo se la sessione ha una richiesta inviata autorizzata. Per un
messaggio contatti appena ricevuto mostra un riscontro generico per **15 minuti**,
senza recapiti o ID; negli altri casi mostra un testo neutro. Non legge ID o email
dalla query string. La pagina storica resta nel database e non viene riscritta
dal controller; i siti senza tema Torrepulia conservano la propria pagina.

Per l'amministratore tecnico, con backup DB/filestore e solo sviluppo/staging:

```sh
odoo -d <database_sviluppo> \
  -u website_torrepulia_request,website_torrepulia_request_theme,website_torrepulia_request_campaign \
  --stop-after-init
```

Riavviare Odoo per caricare i controller. Non aggiornare il tema originale per
questa consegna: il bridge inizializza tramite ORM i campi menu del tema anche
nei database storici, senza aggiornare le pagine del tema. Aggiornare quindi
anche `website_torrepulia_request_theme`, non solo l'addon campagna.
Nessuna modifica a dominio, HTTPS o indicizzazione. Il collaudo è stato eseguito
su `torrepulia_request_test` e su una copia temporanea di `odoo_dev`, poi rimossa.
Il database originale, staging e produzione non sono stati aggiornati.


## Catalogo esaurito e prenotazione stagionale — aggiornamento locale 20/10/2026

Nell'anagrafica del prodotto, nelle impostazioni ecommerce, usare i campi nativi
«Vendi quando esaurito» e «Messaggio per esaurito». Per prodotti con inventario
tracciato, con il flag disattivato e senza disponibilità, il catalogo, il dettaglio
e lo snippet «Scegli i formati» nascondono l'aggiunta. Le varianti rimangono
indipendenti. Il messaggio HTML viene mostrato anche nelle card, con sfondo rosso
chiaro e collegamenti visibili senza passare il mouse. Il pulsante va a capo se
necessario. Se il messaggio è vuoto, non viene inventato un testo promozionale.

Per indirizzare al nuovo raccolto, configurare nel messaggio il collegamento a
`/prenotailtuoolio` e gestire l'apertura della campagna dall'app Website. La
campagna continua a raccogliere prenotazioni senza stock fisico; la sua chiusura
non cambia automaticamente il messaggio del prodotto. Tenere aggiornati i testi
e i collegamenti in base alla campagna realmente disponibile.

Con «Vendi quando esaurito» attivo, le richieste restano possibili. Nessuna
modifica automatica a prezzi, giacenze o flag prodotto. Le selezioni già raccolte
non vengono eliminate; non sono prenotazioni di magazzino. Disattivando la
modalità richiesta, torna il comportamento nativo dello shop.

Questa correzione è installata esclusivamente sull'ambiente locale `:8069`,
database `torrepulia_cinematic_install`; il collaudo automatico usa
`torrepulia_request_test`. [Report e screenshot](qa-20261020-stock/REPORT.md).


## Scheda prodotto, altri formati e nastri — 20/10/2026

Aprire il prodotto dal backend e la scheda **Torrepulia**. Nel gruppo
**Scheda prodotto sul sito** si trovano il titolo web e i tre campi HTML
**Il Profilo Sensoriale**, **Abbinamenti in Cucina**, **Spedizione e Conservazione**.
Il titolo parte da «La Regina» e può essere cambiato per ciascun prodotto;
lasciandolo vuoto viene usato il nome dell'articolo. Solo i campi editoriali
compilati generano sezioni espandibili sotto il prezzo. Gli esempi del backend
non sono testi pubblicati: inserire contenuti approvati e condizioni reali.

Il nastro configurato nel campo nativo **website_ribbon_id** e gli eventuali
nastri automatici ritornano anche nello snippet in modalità richiesta, con
colori e priorità nativi. I badge editoriali del tema sono separati e mantengono
la configurazione del gestore. «Gli altri formati» esclude ora l'articolo che si
sta consultando, senza cambiare la selezione dello snippet salvata nel Builder.

Spaziature minime consegnate: **16 px** fra quantità e aggiunta e **20 px** prima
di «Scegli le opzioni e scopri il prodotto». Gli avvisi esaurito occupano lo
spazio del testo, fino alla larghezza disponibile, con arrotondamento uguale al
dettaglio prodotto. Nello shop sono allineati in basso alle altre azioni.

Aggiornamento locale: `website_torrepulia_request` 20.0.1.10.1 e bridge
`website_torrepulia_request_theme` 20.0.1.3.0.
[Report dei controlli](qa-20261020-product/REPORT.md).


## Presentazione disponibilità unificata — 21/10/2026

Catalogo, snippet dei formati e dettaglio prodotto condividono ora la stessa
presentazione: stato discreto, testo configurato e pulsante verde a tutta
larghezza. Il box rosso e il pulsante a pillola descritti negli aggiornamenti
precedenti sono sostituiti da questa presentazione.

Continuare a usare il campo nativo **Messaggio per esaurito** per testo e link.
Il pulsante **PRENOTA IL NUOVO RACCOLTO** compare soltanto quando la campagna
predefinita del website è aperta, anche senza un pulsante HTML nel messaggio. Con campagna chiusa, futura, scaduta o assente non compare questa CTA.
Gli altri collegamenti informativi restano leggibili. Il campo salvato non viene
riscritto, ma i suoi vecchi stili grafici non determinano più la forma della CTA.

Lo stock e «Vendi quando esaurito» mantengono la logica nativa; la selezione
stagionale rimane distinta. Verificare che nastri e badge editoriali configurati
abbiano un significato coerente: non vengono cancellati automaticamente.

Gli stili del componente valgono anche durante l'uso dell'editor, evitando
l'overlay delle azioni sopra la fotografia. Aggiornare i tre addon richiesta,
bridge e campagna e riavviare Odoo. [Report e screenshot](qa-20261021-stock-design/REPORT.md).


## Pagina stagionale senza riepiloghi duplicati — 21/10/2026

In `/prenotailtuoolio` scegliere i formati con i pulsanti delle card. Sotto la
griglia si trovano direttamente i recapiti e il box **Riepilogo Prenotazione**,
con tutti i prodotti della selezione, quantità e subtotali. Non compaiono il
vecchio elenco prodotti a sinistra né il pulsante intermedio di prosecuzione.
Le modifiche aggiornano il riepilogo senza ricaricare la pagina e senza perdere
i recapiti già digitati.

Nel modulo stagionale sono obbligatori nome, email, telefono, CAP o Città e la
presa visione privacy. Il campo geografico rimane libero: non richiede un CAP
numerico o un indirizzo completo e viene salvato nelle note CRM. La pagina
estesa «La tua richiesta» mantiene le proprie quantità modificabili, rimozione
e campi telefono/località facoltativi.

Il riepilogo usa prezzi nativi del contesto corrente. Con prezzi disabilitati
non mostra subtotali o lo zero monetario: informa che oggi non è richiesto un
pagamento. Nessuna variazione a prezzi, giacenze o condizioni dei preventivi.
L'invio finale rimane l'unica azione che crea l'opportunità, con protezione dai
ritentativi e senza creare automaticamente ordini o pagamenti.

Aggiornare `website_torrepulia_request` 20.0.1.12.0 e
`website_torrepulia_request_campaign` 20.0.1.4.0, poi riavviare il servizio.
[Report e screenshot](qa-20261021-seasonal-summary/REPORT.md).
