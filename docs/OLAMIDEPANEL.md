# AfricanBrowser on Olamidepanel

The approved logo is `assets/branding/africanbrowser-logo.png`. The October 21,
2026 upload exactly matches this existing asset. Native icon generation uses
this artwork; the website also uses it as its background. Legal pages are
generated from TERMS.md, PRIVACY.md, COPYRIGHT.md, LICENSE and NOTICE.md.

On the existing hosting server, with GitHub CLI Actions credentials available
through GH_TOKEN or Ansible Vault:

```sh
git clone https://github.com/olamidebello/AfricanBrowser.git /opt/africanbrowser-publisher
cd /opt/africanbrowser-publisher
ansible-playbook -i ansible/localhost.ini ansible/pull-and-deploy.yml
```

The playbook pulls main into its build checkout, requests an exact-source
Chromium ARM64 build in GitHub Actions, waits for completion, verifies the
APK checksum and structure, and publishes the website download. It then pulls
the Apps Store tools and installs the verified browser listing in the existing
store database, preserving its visibility setting. It backs up the store
database before changing that listing. The store links to the immutable APK
hosted on africanbrowser.com, avoiding a second 500+ MB binary copy.

The document root defaults to
`/var/www/olamide-auto/africanbrowser.com/public_html`; override website_root
if the existing Olamidepanel nginx configuration uses a different path.
The site must already have working nginx routing and HTTPS. The playbook stops
on failed public verification. Store failure does not roll back a successful
browser website publication; rerun the store installer after resolving it.

The APK is a development build until private release signing and device
acceptance testing complete. A source push or passing Python tests does not
mean a new APK has been compiled or deployed. Full Chromium builds require
the configured CI workers and substantial disk space.

No deletion of old APKs, shortcuts or unrelated store listings is included:
the requested deletion scope still needs clarification.
