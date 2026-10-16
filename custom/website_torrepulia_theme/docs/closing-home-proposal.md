# Home Closing Proposal, 2026-10-16

Status: approved and deployed on 2026-10-16. The owner's saved closing copy has been
archived in `closing-owner-copy-20261016.xml` and synchronized to the reusable
Torremaggiore snippet/source without changing the homepage layout.

## Direction

Implementation: `static/src/scss/home_closing.scss`, scoped to
`.territory.mc-home-closing`. The latest owner-selected background photograph
`FOT_9362-HDR.webp` (attachment 706) is preserved and made a native editable
image. The original desktop crop position is retained; mobile focuses on the
sun within the narrow composition. The selected photograph is also bundled
as `static/src/cinematic/owner/closing-landscape-706.webp` for portability.

The entire original `.territory-copy` subtree is preserved verbatim, including
the `mailto:info@torrepulia.it` link. Content determines the section height;
there is no fixed maximum that could truncate the owner's paragraph. The
shade cannot intercept clicks and the copy container allows clicks through
its empty space, preserving native image editing. The pause button sits on
the section above the shade, away from the copy. The breathing cycle uses
18-second legs and retains reduced-motion, visibility and offscreen handling.

Backup view: `website_torrepulia_theme.before_emotional_closing_20261016` (2551).
Only home and the reusable territory snippet were updated; other sections and
pages are untouched. Browser checks/test suites remain deferred by the owner.

CSS compatibility repair: Odoo's LibSass evaluates lowercase `min()` as a
Sass function and rejects mixed `%`/`px` arguments. The closing's equivalent
constraints now use `width: 100%` and breakpoint-specific `max-width` values.
The exact stylesheet is compiled with the container's own Sass package, and
the served frontend CSS bundle is checked as an error diagnostic, not a UI
or interaction test. Only generated CSS cache attachments are invalidated.

Close the journey on the place, not on a second product pitch. Replace the
photo/text split with a single full-width authentic landscape, leading into
the dark-green footer. Keep the existing title, paragraph and CTA verbatim:

- Torremaggiore. Da qui, ogni giorno.
- The owner's paragraph beginning "Il nome Torrepulia custodisce le nostre radici".
- Vieni a conoscerci.

Use the real olive-grove photograph, approximately 640px tall on desktop and
auto height with generous space on mobile. White copy sits on a localized,
quiet dark-green shade at the left, never in a floating card. Keep the grove
visible rather than darkening the whole photo. Body copy has a constrained
measure and no line longer than the mobile container.

Keep the existing minimal photographic breathing with its pause control and
reduced-motion handling. No letter-by-letter animation, parallax, rotating
graphics, scroll hijacking or additional invented company claims. One calm
entrance for the copy is sufficient. The preserved contact CTA connects the
emotional close with an authentic human conversation, not another catalog.

The photograph remains a native editable image; overlays cannot intercept
builder image clicks. Mobile places the text over the shaded lower part, with
content-driven height so the owner's whole paragraph and link remain visible.

## Separate Asset Update

The owner supplied `bag_box_vettorale_senza_sfondo.png`, RGBA 1199 x 1312.
It is converted losslessly to `bag-box-transparent.webp`, preserving alpha,
original pixels and any embedded ICC profile. Only the Bag image URL and its
responsive sizing metadata change. Its label is not regenerated or retouched.
