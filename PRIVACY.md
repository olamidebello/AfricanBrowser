# AfricanBrowser privacy policy

Effective date: October 13, 2026.

Project owner: Olamide Olatayo Bello.

## Scope and current implementation

This policy describes the AfricanBrowser repository, Chromium distribution
tooling, desktop local AI support extension, and default loopback AI service.
It does not describe every website, upstream service, modified distribution or
future feature. Review the policy and release notes for the particular build
you install. A production browser release has not yet been validated in this
repository at the date of this policy.

The current project code does not implement an owner-operated account service,
advertising network, analytics collection endpoint, or central store of users'
browsing histories or chat prompts. That statement does not mean Chromium or
web browsing creates no network traffic, or that external services cannot collect
information. The project has not audited every upstream network path or disabled
every upstream background service.

## Browser profile and browsing data

Chromium browser functions may store browsing history, bookmarks, cookies, cached
pages, downloads, saved passwords, autofill details, site permissions, preferences,
and session information in the device's browser profile, according to your
settings and the platform. Operating-system protections, backups, extensions and
other users with device access can affect who can access that data. Local storage
is not a blanket guarantee that all data is encrypted.

Use the browser's settings to review permissions, clear browsing data, delete
saved credentials or remove the profile. Removing the application may leave
profile files, backups, downloaded files or OS-managed records behind. Private
browsing limits some local persistence; it does not hide your activity from
websites, your network provider or other connection observers.

## Network requests and external services

Browsing sends requests to sites and related services, which may receive your
IP address, requested URL, browser/device information, cookies and other data
you provide. Search queries are sent to the search provider you use. DNS and
network operators can receive connection information according to your network
and browser configuration.

Enabled upstream features such as protective browsing services, network
prediction, certificate checks or optional third-party integrations may create
additional network requests. This project does not promise these are absent.
Review the actual build's privacy settings and network behavior. Google account
sync and proprietary Google service access are not provisioned simply by the
current build tooling.

## Local AI support

The provided UI sends text you type or paste and recent conversation messages to
the loopback support service on 127.0.0.1:8765. That service sends the messages,
together with project support instructions, to the local Ollama service on
127.0.0.1:11435. In the default deployment, inference runs on the same computer;
the provided configuration does not send chat prompts to a cloud AI API.

The extension currently has side-panel permission and permission to contact its
loopback support endpoint. It does not request browsing-history, all-site,
password-manager, contact-list, location, microphone or camera access. It does
not automatically read page contents. Text pasted by you is processed only
because you choose to submit it.

Conversation messages are kept in the UI's memory, not saved by the project's
code to browser storage or a project chat database. Reloading or closing the
page clears that UI memory; Clear chat also removes it when no request is active.
The support service disables its HTTP access log and does not intentionally
persist prompts or responses. Prompts can still be present temporarily in process
memory, runtime buffers, OS swap, crash diagnostics, or independently configured
logs. No guarantee of forensic erasure is made. Ollama and the OS have separate
logging and diagnostic behavior.

The Stop button stops the UI waiting for an answer; it does not necessarily cancel
inference already running in Ollama. Afterward, reload or Clear chat to remove
the UI's displayed history. Do not submit secrets or unnecessary sensitive data.

## Downloads, updates and support

Initial browser source, packages, runtime and model downloads contact GitHub,
Chromium infrastructure, package repositories, Ollama/model distributors and
their delivery networks. Those operators may receive IP addresses and download
request details. Their policies apply to those requests. Model files persist
locally after download. Remove the model/runtime files to free storage when you
stop using the assistant. No automatic browser update service has been implemented
by this project.

If you submit a GitHub issue or other support communication, the hosting provider
and people who can see it receive the content and associated account information.
Public issue content is public. Avoid posting credentials, private documents or
unnecessary personal details. The project does not offer a confidential public
issue channel or a stated support-record retention period.

## Sharing, choices and security

There is no sale, ad profiling, or owner-operated sharing of browser histories or
chat prompts implemented by the current project code. This is a description of
the current implementation, not a claim about every external service, modified
build, device administrator, or legal requirement.

You can decline to use AI, stop its local services, remove the extension, clear
chat memory, review site permissions, clear the browser profile, and manage local
model files. These actions do not delete copies retained independently by websites,
hosting providers, backups or third parties. Exercise any applicable privacy rights
with the party actually holding the relevant data.

Loopback binding and request-origin validation reduce unintended network access
to the assistant. They do not protect against every malicious local process,
extension, device administrator or compromised operating system. Security and
privacy depend on your configuration and the actual installed release.

## Children, changes and contact

The current code does not implement age verification, a children's account
service, or parental consent collection. Do not treat this policy as a claim
that the application has been reviewed for children's privacy compliance.

Material changes will be reflected in this policy's effective date and repository
history. Third-party service policies may change independently.

Owner profile: https://github.com/olamidebello
Project: https://github.com/olamidebello/AfricanBrowser

For non-confidential policy questions, contact the owner through the project's
public GitHub channels. A dedicated private privacy-request address has not been
designated here. Do not post confidential privacy requests in a public issue.
