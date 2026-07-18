# Security model

Ana executes code and shell commands on your machine. Its defenses are
layered: a constitutional pre-check on every message, permission gating on
every tool call, path safety on every file access, sandboxing on execution,
and secrets redaction on everything the model reads back.

## Constitutional principles

Ana checks every user message against eight constitutional principles
before the agent graph runs.

| ID | Name | Severity | Example trigger |
|----|------|----------|-----------------|
| P01 | no_prompt_injection | block | "Ignore all previous instructions" |
| P02 | no_path_traversal | block | "../../etc/passwd" |
| P03 | no_destructive_system_commands | block | "rm -rf /" |
| P04 | no_credential_exfiltration | block | "cat ~/.ssh/id_rsa" |
| P05 | no_network_in_restricted_mode | warn | `requests.get()` appearing in generated code |
| P06 | no_shell_escape_from_python | block | `subprocess.run()` in run_python |
| P07 | no_self_modification | block | Writing to Ana's own source |
| P08 | no_recursive_agent_spawn | warn | A sub-agent tries to spawn agents |

**block** — the request is rejected and a security-warning event is
emitted. **warn** — the request continues; the event is emitted and
logged.

Every violation — blocked or warned — is appended to a persistent audit
trail at `~/.ana/audit/constitution.jsonl`, recording the principle,
severity, action taken, source, session ID, and a snippet of the matching
text.

## Secrets scanner

Ana scans all tool output (file reads, web search results, shell output)
for credential patterns **before** the output enters the LLM context.
Detected secrets are redacted in place:

```
AKIAIOSFODNN7EXAMPLE  →  [REDACTED:aws_access_key]
```

Patterns detected: AWS access/secret keys, GitHub tokens, private key
headers, generic API keys, bearer tokens, database URLs with credentials,
Slack tokens, Stripe keys, and environment-variable assignments with
secret-like names. The agent continues but never sees the raw secret.

## Sandbox

Code submitted to `run_python` always runs in a **RestrictedPython**
sandbox: no `subprocess`, `socket`, or `os.system`; `open()` is
path-scoped to the project directory; 30-second timeout
(`ANA_SANDBOX_TIMEOUT_SECS`); output truncated at 8,000 characters.

`shell_command` and `run_shell_readonly` run through a pluggable sandbox
factory, selected by `ANA_SANDBOX_MODE` (`auto` by default):

| Mode | Isolation |
|------|-----------|
| `docker` | Container via `docker run --rm`, `--network=none` unless network access is requested |
| `bubblewrap` | Linux namespaces via `bwrap`, `--unshare-net` unless network access is requested (Linux only) |
| `local` | Direct host execution — **no isolation** |
| `auto` | Probes Docker → Bubblewrap → local once at startup and caches the result |

!!! warning "macOS / Windows without Docker"
    On macOS/Windows without Docker installed, `auto` falls back to
    `local` — shell commands run unsandboxed on the host. Install Docker
    for container isolation, or set `ANA_SANDBOX_MODE=docker` to fail
    loudly instead of falling back.

All modes share: `cwd` set to the project directory, timeout via
`ANA_SANDBOX_TIMEOUT_SECS`, output truncated at 8,000 characters.

## Bearer token

The backend generates a 32-byte hex token on first start, written to
`~/.ana/session.token` with `chmod 600` (Unix) or a Windows ACL restricted
to the current user. All HTTP and WebSocket connections must present this
token. The backend binds `127.0.0.1` only — never expose it to a network.

## Path safety

All file tools check every path before access:

1. The path must resolve within the session's project directory
2. It must not point into `~/.ana/` (Ana's own data)
3. It must not match known sensitive prefixes (`/etc/`, `~/.ssh/`,
   `~/.aws/`, …)
4. It must not match `.anaignore` patterns

## `.anaignore`

Files matching `.anaignore` patterns are never read, listed, indexed, or
written. There is no built-in default ignore list — patterns come entirely
from your `.anaignore` file, matched with fnmatch semantics (basename or
full path). See [Settings](../configuration/settings.md#anaignore) for an
example.

## Permission rules

Independent of the active permission mode, a persistent store
(`~/.ana/permissions.db`) holds allow/deny/ask wildcard rules per action
type. Seeded defaults deny `rm -rf *` and reads of `./.env*`. See
[Permission modes](../configuration/permissions.md#permission-rules-allowdenyask).

## Extensibility trust boundaries

- **MCP servers** run as local subprocesses (stdio transport) and their
  tools are exposed to the agent exactly like built-in tools — only
  configure servers you trust.
- **Plugins** are **not sandboxed**. Installing a plugin runs arbitrary
  Python at load time — treat plugin sources the same as any other trusted
  dependency, not as untrusted input.
- **Skills** are plain markdown — but auto-crystallized skills still
  require explicit human approval (`ana skills approve`) before they are
  ever injected into a prompt.

## Reporting a vulnerability

Please do not open a public issue for security problems — use GitHub's
private vulnerability reporting on this repository instead.
