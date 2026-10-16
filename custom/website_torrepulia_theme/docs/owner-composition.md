# Owner Composition, 2026-10-15

Authority: the saved homepage in `torrepulia_cinematic_install` on port 8069.
The external cleanup archive retains `home-owner-snapshot.xml`; the inactive
database view `website_torrepulia_theme.owner_before_snippet_repairs_20261015`
is the rollback reference. Do not overwrite this baseline by rerunning an old
whole-page refresh script.

The archived `home-owner-current.xml` records the original repairs. `views/cinematic.xml`
contains the same section copy and layout as reusable snippet defaults, with
uploaded photographs exported to `static/src/cinematic/owner/` for portability.
Local attachment IDs and local product selections are not installation defaults.

Home order: hero, La Regina, formats, Bag in Box, family, Peranzana, table, territory.
The family's uploaded photograph, bottle photograph, native bottle animation,
hero copy, long product copy and family copy have been retained.

## Scoped Changes

- Restore the Peranzana heading to "Peranzana. La nostra origine."
- Remove the de Sangro history band from the home, not institutional pages.
- Align La Regina's two introductory labels using layout rather than spaces.
- Remove the family's name timeline. Add an editorial Leone imprint beside the
  archive photograph, with the existing one-time photographic reveal.
- Format prices in `website.currency_id`, as Odoo 20's native sales-price API
  does. `request.pricelist` can legitimately be empty when pricelists are off.
  Do not enable pricelists or change the owner's commercial settings to fix it.
- Preserve current source photography during the snippet upgrade path; legacy
  campaign replacement is reserved for the original one-time page migration.

Existing published formats: Latta 5 LT and Bag in box 5 LT. No products, prices,
taxes, currencies or stock quantities were created or edited by this migration.

Browser and builder checks were authorized and executed on October 16;
see `STABILIZATION.md` and `qa-final/` for the current verification record.
