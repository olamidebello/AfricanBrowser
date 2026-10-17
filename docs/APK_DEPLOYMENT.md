# Rebuild and deploy the Android download

This playbook pulls the current AfricanBrowser source onto the hosting server,
requests an Android ARM64 rebuild on GitHub Actions, waits for that exact run,
and downloads its artifact back to the server. The existing website remains
available during compilation. It publishes the APK under a versioned download
URL, then publishes the new home page, branding, and legal pages. Desktop and
iOS installers are not built by this command.

## Requirements

- Debian/Ubuntu hosting server, existing nginx/HTTPS configuration, authorized
  SSH access, and Ansible Core 2.18 or later on the controller.
- GitHub CLI authentication: provide `GH_TOKEN` with repository read and Actions
  write access (or use Ansible Vault variable `deploy_github_token`). The token
  is passed only through the build process environment and masked in Ansible
  output; it is not written into inventory or the repository.
- Outbound HTTPS from the server to GitHub and artifact storage; enough free
  storage for the project, downloaded artifact, staging, and retained releases.
  Chromium compilation uses GitHub runners rather than the hosting server.
- The workflow can take many hours. Default wait limit is 28 hours including
  queue time. GitHub Actions minutes/storage limits still apply.

## Run from your controller

Copy `ansible/hosting.example.ini` to a private inventory and confirm the SSH
user/address. Supply your token through your credential manager or environment,
then run:

```sh
ansible-playbook -i ansible/hosting.example.ini ansible/rebuild-deploy.yml
```

The default document root is
`/var/www/olamide-auto/africanbrowser.com/public_html`. Override it if the active
nginx configuration uses another path:

```sh
ansible-playbook -i ansible/hosting.example.ini ansible/rebuild-deploy.yml \
  -e website_root=/your/existing/document/root
```

For a local run on the hosting server, use an inventory containing
`localhost ansible_connection=local`, install Ansible, and provide GH_TOKEN in
that server's environment. The playbook installs Git, GitHub CLI and Python.

## Verification and recovery

Only a successful workflow with the unique request ID and exact pulled commit
is accepted. The downloaded SHA-256, ARM64 browser ZIP structure, upstream lock,
platform and CPU metadata are checked before publication. Source updates during
startup cause a failure; rerun to pull the current commit. Custom user homepages
and existing nginx configuration are not overwritten by this deployment.

Versioned downloads remain available for rollback. The homepage is copied
atomically with a backup; public homepage and APK HEAD checks run afterward.
If activation fails, the previous homepage is restored. Download bytes are
verified on the server; the public HEAD check verifies availability and size.
This produces a **development-signed APK**, not a production-tested release.

An exclusive `/opt/africanbrowser-deploy/deploy.lock` directory prevents competing
runs. Normal failures release it automatically. If the Ansible controller is
forcibly terminated, check that the remote rebuild has ended before removing a
stale lock or starting another deployment. Temporary staging is removed on normal
completion; published versioned downloads are retained intentionally.
