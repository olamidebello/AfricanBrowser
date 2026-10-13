# Platform and feature scope

This describes inherited architecture and remaining integration work, not
browser acceptance test results. No platform binary has yet been compiled here.

| Capability | Desktop | Android | iOS/iPadOS |
| --- | --- | --- | --- |
| Full upstream browser UI | Chromium target | Chromium Android target | Chromium iOS target |
| Web engine | Blink/V8 | Blink/V8 | Upstream iOS engine configuration |
| Tabs, bookmarks, history, downloads | Upstream | Upstream mobile support | Upstream mobile support |
| Private browsing and permissions | Upstream | Upstream | Upstream |
| Desktop extensions and DevTools | Upstream desktop support | Desktop parity unavailable | Desktop parity unavailable |
| AfricanBrowser product strings | Overlay | Overlay | Overlay |
| Signed public distribution | Pending | Pending | Pending; initial build is simulator only |
| Tested runtime behavior | Pending | Pending | Pending |
| Own secure automatic updates | Pending | Pending | Store distribution pending |
| Google account/Chrome Sync | Not provisioned | Not provisioned | Not provisioned |
| Google service credentials | Not provisioned | Not provisioned | Not provisioned |
| Widevine / proprietary media distribution | Requires separate authorization and validation | Requires separate validation | Platform dependent; requires validation |
| Proprietary Chrome AI features | Not implemented | Not implemented | Not implemented |

Google credentials must not be checked into this repository. Google service
availability is governed by its current API rules; owning an API key does not
automatically grant Chrome Sync access. Browser defaults, localized resources,
app icons, OS associations, accessibility, privacy disclosures, and distribution
identities must be reviewed on each target before public release.
