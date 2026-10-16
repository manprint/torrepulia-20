# Torrepulia Content And Geographic Sources

Homepage revision: 13 October 2026. Competitor references inform composition and
rhythm only. No competitor claims, awards, certifications or phrasing are reused.

## Facts

- https://torrepulia.it/aboutus : Santino Vincenzo's inherited olives, Michele's
  expansion, Franco and Salvatore, the brand founded in 2020 and its name.
- https://torrepulia.it/l-olio : Peranzana growing area, October-November harvest,
  aerated containers, milling within six hours, cold extraction, filtration,
  sensory profile and serving suggestions.
- https://torrepulia.it/ : own-company olives, 500ml dark-glass bottle, tin and
  bag-in-box formats. Catalogue pricing remains the responsibility of Odoo data.
- https://www.museosansevero.it/il-principe-di-sansevero/biografia : Raimondo di
  Sangro's birth in Torremaggiore in 1710 and title of Prince of Sansevero.

The Peranzana introduction story is explicitly attributed to local tradition.
The original Torrepulia account associates it with Raimondo; other accounts name
other members of the de Sangro family. We do not describe the attribution as an
established botanical or archival fact. The portrait/castle illustration is the
existing Torrepulia image: https://torrepulia.it/web/image/1321-736ec222/raimondo-castello-tm.jpg .

## Map

Boundaries: https://github.com/guglielmo/geojson-italy , derived from ISTAT under
CC BY, with attribution attached to the map. Simplified with Shapely for display.
The map point is the town of Torremaggiore, not surveyed farm coordinates.
Town coordinate reference: https://www.tuttitalia.it/puglia/64-torremaggiore/ .

## Direction

https://klimtwine.com/en : geographic storytelling and controlled map reveal.
https://www.oliovisconti.com/ : family and place-led narrative structure.
https://olioalbori.com/ : progression from people and olives toward the table.

Brand palette: olive #2e493b, label gold #b4931e, white #ffffff, pale #eef2ed,
light pink #f1e7e8 (formats section and native palette slot 3),
vegetal black #18231f. The native Odoo palette and custom surfaces share these
values. The hero is full-screen and static; map motion is one-time and optional
through the visitor's reduced-motion preference.

Builder integration: bake the map SVG into the homepage's editable structure.
A live QWeb t-call inside that structure distributes its ownership metadata to
individual sections and disables the native block insertion zones. Existing
user changes must be preserved when expanding the map call.
