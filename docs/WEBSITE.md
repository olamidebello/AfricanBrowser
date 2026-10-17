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

Deploy from this checkout using an existing authorized SSH connection:

```sh
ansible-playbook -i ansible/inventory.example.ini ansible/website.yml
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
