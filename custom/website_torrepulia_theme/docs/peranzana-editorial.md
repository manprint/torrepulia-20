# Peranzana Editorial Composition

## Current Revision, 2026-10-16

The owner requested a return to a full-width photographic opening with their
uploaded `FOT_9784.webp` (attachment 683 and its existing responsive sources).
The image remains a native editable `img`, not a CSS background. The shading
pseudo-element cannot intercept clicks; heading and caption remain editable.
The generated botanical plate was removed from the live home and snippet.

Sensory tabs now have 48px of space beneath their upper divider (32px on
mobile), left-aligned labels, and gold Lucide strokes at 2.25px. The body has
120px bottom padding before the process band, 80px on mobile. Process icons
sit in restrained 64px pale-green circles (56px mobile).

The family's dark-green surface is `#203b2f`; titles, links and body copy use
light colors. The owner's family photographs and all copy remain unchanged.

The La Regina heading labels had been merged into one span during an editor
save. They are now two differently named block elements, preserving the
original left/right alignment without relying on mergeable adjacent spans.

Backup view: `website_torrepulia_theme.before_fullbleed_refinement_20261016`.
Browser checks and tests remain deferred at the owner's request.

## Original Revision

Approved by the owner on 2026-10-15. Published only to the saved homepage and
the reusable Peranzana snippet in `torrepulia_cinematic_install` on port 8069.

The migration preserves every nonempty owner text node verbatim. It checks
the current section against the captured snapshot before changing it; saves
an inactive backup view; and replaces only `section#peranzana`. Other homepage
sections, photographs and the catalog are untouched.

## Direction

An asymmetric opening with the original title and caption on pale white and
an unobscured, native editable image. No overlay or click-intercepting artwork.
Origin copy and a small generated botanical plate sit beside the three sensory
tabs. Native tab semantics, arrow-key navigation and visible focus are retained.
All panels remain visible for text editing inside the builder.

The two production passages use Lucide line icons, generous spacing and the
owner's original labels. Icons are vendored alongside the existing ISC license.
No new production claims, numbers, captions or commercial facts were added.

Motion: one-time 850ms photo/botanical entrances and a 280ms sensory-panel
change for pointer clicks only. Reduced motion cancels active animations.
No loops, parallax, pinning or scroll effects over text. Layout defaults visible
without JavaScript. Responsive typography uses fixed breakpoints, not vw sizes.

Browser verification and test suites remain deferred at the owner's request.

## Generated Asset

Built-in image generation, transparent PNG, copied into:
`static/src/cinematic/images/peranzana-botanical-v1.png`.
The plate is decorative illustration, not documentary company photography.

Prompt:

> Create a premium botanical illustration asset for the Torrepulia Italian olive oil website. One graceful botanically credible olive twig with narrow silver-green leaves and a small cluster of elongated green and purple olives, inspired by Peranzana olives. Sophisticated natural history plate, exceptionally fine ink and restrained watercolor, realistic botanical proportions, muted olive green and touches of soft golden ochre, crisp detailed edges. Not a logo, not an icon, not a photograph of a farm. A single airy diagonal composition with generous transparent negative space, no paper, no solid background, genuinely transparent alpha background. No text, letters, numbers, labels, frames, decorative circles or shadows. Portrait-ish square asset, suitable for a small editorial botanical accent beside real text. Save generated asset for use in the local project.
