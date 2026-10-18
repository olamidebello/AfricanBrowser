# Public website

The static homepage is maintained in `website/index.html`. It includes the
published Android ARM64 development APK, release notes and checksums, accurate
platform status, keyboard navigation, responsive layouts, and legal pages built
from the repository policies. No analytics or third-party scripts are loaded.

Build on the Ansible controller:

```sh
python3 scripts/build_website.py
python3 -m unittest discover -s tests -v
```

Deploy from this checkout using an existing authorized SSH connection. The
playbook rebuilds the site automatically before publishing, verifies public
branding and legal pages, and repairs the legacy `/logo.png` URL:

```sh
ansible-playbook -i ansible/hosting.example.ini ansible/website.yml
```

Set inventory host/user for the hosting server first. Confirm `website_root`
against the active nginx document root; override it with `-e website_root=...`
if necessary. The default is the existing hosting-panel document root at
`/var/www/olamide-auto/africanbrowser.com/public_html`. For a local run on that server, use an inventory file containing:

```ini
[africanbrowser]
localhost ansible_connection=local
```

The playbook preserves nginx, certificates, and unrelated files, and backs up
every replaced file. It publishes assets and policies before atomically replacing
the homepage and verifies the public download action. Restore the backup index
file created beside `index.html` to roll back the homepage. Review/update the
pinned APK URL and release date when a newer verified release is published.

To repair the website directly from an SSH terminal on the hosting server
without rebuilding Chromium or requiring a GitHub token:

```sh
git clone https://github.com/olamidebello/AfricanBrowser.git /opt/africanbrowser-website
cd /opt/africanbrowser-website
# On later deployments use git pull --ff-only in this checkout instead.
printf '[africanbrowser]\nlocalhost ansible_connection=local\n' > /tmp/africanbrowser-local.ini
ansible-playbook -i /tmp/africanbrowser-local.ini ansible/website.yml
```
