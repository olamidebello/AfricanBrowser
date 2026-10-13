# Resumable Android compilation

The previous hosted job reached ARM64 compilation but was cancelled at the
350-minute job limit. It produced no APK artifact. Increasing a standard hosted
job beyond GitHub's maximum duration would not fix the build.

The Android workflow now uses up to four sequential compilation segments. Each
segment stops the compiler after 270 minutes, before the worker expires, and
saves completed Ninja outputs and dependency state. Later segments restore the
most recent checkpoint for the exact same project commit and immutable Chromium
revision. Inputs receive stable timestamps, so rechecking out identical source
does not invalidate every saved object file. Genuine compiler errors stop the
build; a timed compilation segment is marked incomplete and continues next.

Checkpoints use Zstandard compression, SHA-256 validation, path validation,
matching GN arguments and matching absolute workspace paths. A checkpoint is
capped at 9 GiB; the workflow does not increase GitHub's repository cache quota
or provision a paid runner. If that cap or the four-segment limit is insufficient,
a persistent native build worker is required. This is a build recovery mechanism,
not a promise that Chromium compiles within any particular time.

The workflow succeeds only when compilation finishes and the APK is packaged.
The downloadable artifact is named `AfricanBrowser-Android-ARM64-development`.
Its signing/runtime validation status remains development until the separate
production release steps have been completed. The production signing and device
test workflow follows a successful APK workflow; it requires the configured
private signing identity and dedicated Android release device described in
RELEASE.md.

After a successful compiled APK workflow, `downloadable-apk.yml` publishes the
actual APK and checksum as a public GitHub prerelease. It clearly identifies the
development signing and incomplete device/production validation. This provides
a direct binary download once compilation finishes; it does not label a failed
build, checkpoint, source archive or development APK as a production release.

Do not restart a running workflow just to check its progress. A retry of the
same commit can reuse a completed checkpoint; changes to the project commit
intentionally invalidate checkpoints so source changes cannot be hidden by a
stale binary.
