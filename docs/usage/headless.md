# Headless mode

`ana print` runs a single non-interactive turn: send a prompt, print the
reply, exit. It auto-starts the backend just like `ana chat`, so it works cold
in scripts and CI. That backend stops itself about two minutes after its last
client leaves (`ANA_BACKEND_IDLE_TIMEOUT_S`).

## Basics

```bash
ana print "explain the auth flow"            # plain text reply
git diff | ana print -                       # prompt from stdin ("-")
ana print -s <session-id> "and now fix it"   # continue an existing session
```

With `--session`, only the new turn counts: the reply and any `stream-json` events
are this turn's, not the session's history. If the session is still busy with another
turn, `ana print` says so and exits non-zero.

`ana print` exits non-zero when the turn ends in a non-recoverable error,
so it composes with `&&`/`set -e` in scripts.

Nobody can answer a prompt here, so a project's `.ana` config stays off unless you pass
`--trust`, and Ana prints a line to stderr saying it skipped it. On a machine with no
sandbox, `--trust` also lets lint and test checks run. See
[Project trust](../reference/security.md#project-trust).

## Output formats

| Flag | Output |
|---|---|
| *(default)* | The reply as plain text |
| `-f json` | The full transcript as a single JSON document |
| `-f stream-json` | One JSON event per line as the turn executes |

```bash
ana print -f json "summarise this repo" | jq '.messages[-1].content'
ana print -f stream-json "…" | jq .type    # follow events live
```

## Recipes

**Review a diff in CI:**

```bash
ana ci "review this diff for correctness" --diff HEAD~1 --output-format json
```

**Commit-message generator:**

```bash
git diff --cached | ana print - <<'EOF'
Write a one-line conventional commit message for this staged diff.
EOF
```

**Continue a session across script steps:**

```bash
SESSION=$(ana session new --project . | awk '{print $NF}')
ana print -s "$SESSION" "read the failing test output in test.log"
ana print -s "$SESSION" "now propose a fix"
```

## Permissions in headless runs

Headless turns run under the session's permission mode like any other turn.
An `ask` [permission rule](../configuration/permissions.md) pauses for
confirmation even in headless mode — reserve `ask` rules for genuinely
sensitive patterns, or run scripted work in a session whose rules and mode
don't require prompts.

## Related

- [CLI reference](cli-reference.md)
- [Watch & CI review](../features/watch.md)
