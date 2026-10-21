# Deploy a public APK without a server GitHub login

The Android APK builds on GitHub Actions. After the build and the
`Publish downloadable development APK` workflow succeed, the public release
contains the APK, SHA256SUMS and build-info.json. Server deployment can download
these public assets without gh login or GH_TOKEN.

On the existing Olamidepanel hosting server:

```sh
cd /opt/africanbrowser-publisher
git pull --ff-only
ansible-playbook -i ansible/localhost.ini ansible/public-release.yml -e release_run_id=39659254771
```

The run ID selects one exact Android build, not the release-publisher run.
Use a later successful Android build's run ID to deploy a later version.
If compilation or release publication is pending, this command stops before
changing the live site. It never falls back to an older APK. API rate limits
or a failed GitHub release publication can also prevent download; this script
does not bypass either condition.

The playbook pulls current public deployment code, downloads the selected
APK, verifies SHA-256 and archive structure, builds the branded site and legal
pages, and verifies the public APK URL before updating the homepage. It saves
backups of the homepage and deployment manifest. The existing site must already
be routed over HTTPS with an Olamidepanel document root at website_root.

Finally it pulls the public Apps Store publisher and registers the verified
native browser listing. A store failure leaves the successfully published
browser site in place. It does not remove other apps or old downloads.
Development signing and outstanding device testing are disclosed in the listing.

`ansible/pull-and-deploy.yml` remains an alternative when the server has a
GitHub CLI profile and should request a new build itself. The public-release
playbook deploys a published build; it does not start another compilation.
