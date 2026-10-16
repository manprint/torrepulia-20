# Interactive Bag in Box

## Current Artwork, 2026-10-16

The owner selected `bag_box_vettorale_senza_sfondo.png`.
The current native editable image is
`static/src/cinematic/images/bag-box-transparent.webp`: lossless RGBA,
1199 x 1312. Label, branding, proportions and printed callouts are unchanged.
No generated typography, vector pouch or synthetic drop overlays the artwork.

The invisible button over the printed Aroma callout opens an explanatory
tooltip by pointer hover, focus or touch. Escape dismisses it. Each snippet
receives a unique tooltip ID; interaction cleanup restores original attributes.
Obsolete SVG paint-server handling, pouch filters, drop timers, observer and
shape CSS were removed after verifying no active view in either local database
still uses that diagram. Earlier artwork and code remain in the external archive.

## Layout And Commercial Link

Native Odoo snippet `s_torrepulia_packaging`, in the Torrepulia builder group.
Two columns, vertically aligned, stacked below 900px. Ivory background,
night-green copy, original owner artwork and Lucide pillar icons.
Editorial copy, photo and CTA stay native builder content.

The CTA uses the real published product's native website URL locally.
Portable defaults use a native catalog search when product IDs are unavailable.
No products, prices, taxes, currency or stock are changed.

The territory section now uses the separate approved full-background closing
composition documented in `closing-home-proposal.md`, preserving the owner's
Torremaggiore copy and mail CTA. The earlier map remains in inactive backups.

## Technical Copy Decisions

No zero-oxidation guarantee, thermal-insulation promise, unsupported completely
recyclable claim, or suggestion that tins admit light was introduced.
Copy describes reduced air contact, opaque packaging, measured dispensing
and label-guided disposal. Confirm material claims with the packaging supplier.

Sources consulted during implementation on 2026-10-16:
- https://ucfoodquality.ucdavis.edu/olive-oil/olive-oil-packaging
- https://www.smurfitkappa.com/uk/products-and-services/bag-in-box/edible-oils
- https://www.smurfitwestrock.com/products/packaging/bag-in-box

Browser and builder checks are now authorized and recorded in
[the final verification report](qa-final/report.md).
