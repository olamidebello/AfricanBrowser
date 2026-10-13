# AfricanBrowser

An open source Chromium browser distribution project for Android, Windows,
macOS, Linux, and iOS/iPadOS. It builds the upstream browser, not a WebView or
Electron wrapper. Local code is BSD-3-Clause; upstream Chromium and its bundled
dependencies retain their own licenses and attribution.

**Current status: source/build tooling, not a compiled or production-ready browser.**
No APK, installer, signed Apple application, verified browser release, automatic
update service, or Chrome feature-parity certification is provided yet.

## Foundation

`config/upstream.json` pins Chromium 155.0.8059.39 and an immutable depot_tools
revision. The Chromium revision was obtained from ChromiumDash's Linux Stable
release feed on October 13, 2026. It is a starting baseline, not a guarantee that
all platforms use that version in their own stable channel. Review upstream
security updates before each release.

The browser source is downloaded into a separate checkout when building. The
repository contains the distribution overlay and reproducible build commands;
it does not vendor Chromium's enormous source tree. Branding updates product
names and English product strings, retaining upstream identifiers and legal
attribution. Android uses `org.africanbrowser.browser`; iOS uses the
`org.africanbrowser` bundle prefix; Linux's default profile is
`~/.config/africanbrowser`; macOS uses `org.africanbrowser.AfricanBrowser`.
Complete icon replacement, localized branding, Windows installer/profile
identity isolation, and platform branding review remain release work.

## Browser features

Using the full upstream browser preserves its implementation of tabs, navigation,
bookmarks, history, downloads, private browsing, site permissions, accessibility,
password and autofill UI, printing/PDF, developer tools, and web platform APIs
where supported on the selected platform. Desktop extension support follows
upstream Chromium. Android and iOS do not have desktop Chrome's full extension
and DevTools experience. These inherited capabilities still require runtime
verification on each AfricanBrowser build.

Chrome's Google account sync, Google service access, proprietary DRM/codecs,
Google branding, proprietary AI features, and Google's update infrastructure
are not included merely by building Chromium. Never claim that this project
implements every exact Chrome feature. See [feature scope](docs/FEATURES.md).

## Build

Use a dedicated native build machine with at least 200 GiB of free SSD storage,
32 GiB RAM recommended, Git, Python 3.11+, and the native SDKs required by the
pinned upstream documentation. The preflight enforces 120 GiB free as a lower
bound, not a promise that the complete build will fit. Android builds on Linux;
Apple builds on macOS; Windows builds on Windows. Install Linux dependencies
after checkout using the pinned upstream instructions; the script does not
silently install packages as root.

```sh
python3 scripts/browser.py plan --target android --cpu arm64
python3 scripts/browser.py doctor --target android
python3 scripts/browser.py checkout --target android --cpu arm64 --work /large-disk/africanbrowser
# Follow work/android/src/docs/android_build_instructions.md to install build dependencies.
python3 scripts/browser.py build --target android --cpu arm64 --work /large-disk/africanbrowser
python3 scripts/browser.py package --target android --cpu arm64 --work /large-disk/africanbrowser
```

For desktop use `--target linux`, `windows`, or `macos` and `--cpu x64` or
`arm64` as supported by the host toolchain. On Windows use `python` in a native
command prompt, install the required Visual Studio/SDK, and set
`DEPOT_TOOLS_WIN_TOOLCHAIN=0`. Use short paths without spaces. Do not share
depot_tools or a source checkout between native Windows and WSL.

For iOS use `--target ios --cpu arm64` on an Apple Silicon Mac. This initial
configuration builds for the **simulator**, not an installable signed IPA.
iPhone/iPad device distribution requires Apple signing identities, entitlements,
and provisioning profiles. Consult the pinned source's
`docs/ios/build_instructions.md` for device settings and supported engine options.

Compiled development artifacts go to `dist/` with build metadata and SHA-256
checksums. Packaging fails if required build outputs are absent. Output remains
development software until [release acceptance](docs/RELEASE.md) is completed.

## Continuous integration

Hosted CI checks the Python tooling. The manually dispatched native build
workflow needs separately provisioned self-hosted workers labeled
`africanbrowser` and the platform name. Those workers must already have all SDKs
and OS dependencies installed. The workflow does not publish releases or claim
signing, runtime tests, or automatic updates. A dirty upstream checkout is not
reset automatically: use a fresh work directory for a new checkout/release.

```sh
python3 -m unittest discover -s tests -v
```

## Upstream documentation

- https://chromium.googlesource.com/chromium/src/+/155.0.8059.39/docs/linux/build_instructions.md
- https://chromium.googlesource.com/chromium/src/+/155.0.8059.39/docs/android_build_instructions.md
- https://chromium.googlesource.com/chromium/src/+/155.0.8059.39/docs/windows_build_instructions.md
- https://chromium.googlesource.com/chromium/src/+/155.0.8059.39/docs/mac_build_instructions.md
- https://chromium.googlesource.com/chromium/src/+/155.0.8059.39/docs/ios/build_instructions.md
- https://www.chromium.org/developers/how-tos/api-keys/
