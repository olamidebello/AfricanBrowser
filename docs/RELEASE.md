# Acceptance before calling a release operational

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
