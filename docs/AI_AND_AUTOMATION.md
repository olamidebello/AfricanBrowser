# Local AI and Ansible automation

The local assistant uses Ollama and Qwen2.5 1.5B. There is no paid cloud AI API,
API key, or subscription requirement. Hardware, storage, electricity and the
initial runtime/model downloads are still required. Model weights are downloaded
on deployment, not embedded inside the Chromium APK. After the model is installed,
chat inference runs locally without sending prompts to a cloud provider.

The assistant answers browser support questions and can summarize or translate
text that the user explicitly pastes. It has no automatic access to pages,
history, accounts or passwords, and cannot perform browser/device actions.
Answers come from a local language model and may be wrong. Requests are limited
in size, concurrency and generated tokens. Conversations stay in page memory;
the service does not log prompts or responses.

## Linux deployment

The Ansible playbook supports Debian/Ubuntu x86_64. It provisions a dedicated
account, isolated Python environment, checksum-verified pinned Ollama runtime,
model download, systemd services and model readiness checks. Both APIs bind to
loopback; no firewall port is opened. Use the assistant on the same desktop.
Installing it on a remote VPS does not install an on-device Android model.

```sh
python3 -m pip install 'ansible-core>=2.18,<2.19'
cp ansible/inventory.example.ini ansible/inventory.ini
# Set the actual SSH host and user in inventory.ini.
ansible-playbook -i ansible/inventory.ini ansible/site.yml --tags ai --ask-become-pass
```

For a full Android build worker, provide sufficient SSD storage and RAM, then:

```sh
ansible-playbook -i ansible/inventory.ini ansible/site.yml --tags build --ask-become-pass
# Both build and AI:
ansible-playbook -i ansible/inventory.ini ansible/site.yml --ask-become-pass
```

Build provisioning is resumable at the script level, but checkout deliberately
refuses a dirty Chromium source tree. A second complete playbook run after
branding/building requires a fresh work directory or skipping checkout. Do not
expect Ansible to discard source changes or replace existing artifacts.
Use `--check --diff` to preview system configuration; downloads, source compilation
and live model readiness cannot be fully validated in check mode.

## Browser UI

Open `http://127.0.0.1:8765` on the provisioned Linux computer. For a desktop
Chromium side panel, go to `chrome://extensions`, enable Developer mode, choose
Load unpacked and select `extensions/africanbrowser-support` from this repository.
Click its toolbar button to open the assistant. This is an explicit desktop
extension integration, not an Android/iOS extension or packaged native assistant.

For manual setup, install Ollama using its official instructions and run:

```sh
OLLAMA_HOST=127.0.0.1:11435 OLLAMA_NO_CLOUD=1 ollama serve
# In a second terminal:
OLLAMA_HOST=127.0.0.1:11435 ollama pull qwen2.5:1.5b
python3 ai/server.py
```

The local HTTP service accepts its own origins and Chromium extension origins,
checks the Host header to resist DNS rebinding, and rejects arbitrary website
origins. It provides no shell execution, remote administration or credential
access. The Stop button stops waiting on a response; the model may continue its
bounded inference request until it finishes.

## Validation status and remaining work

Service routing, origin checks, request validation, UI JavaScript, logo generation
and Ansible syntax are tested separately. Live inference and deployment still
require the model runtime and a target host. The full Chromium APK is not yet
compiled. Embedding model weights and an inference runtime inside Android/iOS,
native support UI integration, packaged desktop extension installation, and
native release signing remain work; this is not full embedded AI on every platform.

References:
- https://github.com/ollama/ollama/releases/tag/v0.40.3
- https://docs.ollama.com/linux
- https://docs.ollama.com/api/chat
- https://ollama.com/library/qwen2.5
