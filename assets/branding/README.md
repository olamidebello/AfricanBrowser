# AfricanBrowser artwork

`africanbrowser-logo.png` is the user's original uploaded artwork, preserved
byte-for-byte. It contains the Pan-African Africa emblem, AfricanBrowser
wordmark and “… browse the black ways” slogan.

`africanbrowser-icon.png` is a build preview of the emblem-only icon. Use the
full original for brand presentations; the emblem is used for small launchers
and browser product icons. The black background is intentional.

`scripts/logo_assets.py` converts the source artwork to the dimensions and
formats expected by existing Chromium resources. It preserves image dimensions
and does not replace incognito, PDF, document, or extension-specific icons.
On Android the layered foreground includes mask-safe padding. Apple tinted
legacy icons are grayscale; full-color defaults preserve the supplied palette.

The modern Apple icon composition reuses the tracked `Assets/ring.png` resource
as one artwork layer and preserves platform metadata. Its compilation and the
macOS precompiled `Assets.car` behavior must be reviewed on a native Apple build
before release. No browser binaries have been rebuilt in this workspace.
