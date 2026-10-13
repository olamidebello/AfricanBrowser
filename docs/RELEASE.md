# Acceptance before calling a release operational

## Automated Android download publication

`production-android.yml` follows a successful hosted Chromium APK build. Configure
a dedicated Linux release runner with labels `africanbrowser-release` and
`android-device`, Android SDK tools (`adb`, `aapt`, `zipalign`, `apksigner`) on PATH,
GitHub CLI, Python 3.11+, and a clean, authorized ARM64 Android test device using
English onboarding. Set repository variables `ADB_SERIAL` and
`ANDROID_SIGNING_CERT_SHA256` (the public certificate fingerprint).

Store the private release keystore as repository secret `ANDROID_KEYSTORE_BASE64`,
its password as `ANDROID_KEYSTORE_PASSWORD`, and alias as `ANDROID_KEY_ALIAS`.
If the key password differs, set `ANDROID_KEY_PASSWORD`. Never commit the private
keystore or paste its password into a public issue. Configuration is done in
GitHub repository Settings → Secrets and variables → Actions.

The pipeline aligns and signs the APK, verifies its certificate, refuses to use
a device with an existing AfricanBrowser installation, installs the test APK,
checks that an HTTPS page appears through the real browser, records a screenshot
and test report, removes its own test installation, and publishes an APK asset
only after success. It does not make a source archive or failed build downloadable
as a production browser. The smoke test is narrower than the release acceptance
checks below; expand native validation for all supported browser functions.

The repository's latest-release APK endpoint becomes usable only after successful
publication. No production asset currently exists; do not present the endpoint
as a ready download before the release job succeeds. No private signing identity
or release device has been supplied in this session.

Build logs and successful compilation alone do not establish working behavior.
Record device/OS versions, upstream revision, test results, and artifact hashes.

1. Compile each platform on its native build host; retain complete build logs.
2. Finish and audit platform identities, icons and translated product names.
   Verify installs do not overwrite another browser or reuse its profile.
3. Install and launch as an ordinary user with the Chromium sandbox enabled.
   Verify HTTPS navigation, TLS error handling, navigation history, multiple
   tabs/windows, crash recovery, and clean process shutdown.
4. Verify bookmarks/history persistence, private browsing separation, downloads,
   password storage, cookies, cache clearing and site permission persistence.
5. Exercise microphone/camera prompts, WebRTC, audio/video, PDF, accessibility,
   keyboard navigation, default-browser selection and OS link handling.
6. On desktop test extensions, DevTools, printing, profile separation and imports.
   On mobile test background/resume, deep links, rotation and low-memory recovery.
7. Run upstream unit/browser/instrumentation tests relevant to all changed code.
   Investigate failures rather than disabling security features to pass tests.
8. Sign Android with a private release keystore; retain APK/AAB signing lineage.
   Sign and notarize macOS builds; sign Windows installers; provision and sign
   iOS device builds and verify their app/extension entitlements.
9. Include Chromium/third-party license notices and source/license disclosures
   required by each bundled dependency. Preserve upstream `chrome://credits`.
10. Provide security contact, vulnerability triage, privacy policy, a reviewed
    security update process, and a secure update/distribution mechanism.

Do not publish the initial APK's development signing key as a release identity.
The iOS simulator archive cannot be installed on a physical iPhone or iPad.
The desktop installer/profile identity and Android package identity require
platform review before any public release; string branding alone is insufficient.
