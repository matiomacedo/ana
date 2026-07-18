# Watch & CI review

Ana can review code changes **outside** an interactive session: live as you
save files (`ana watch`), or as a one-shot review of a git diff (`ana ci`).

## `ana watch` — background review on save

```bash
ana watch [path]   # requires a git repo; runs in the foreground until Ctrl-C
```

Ana watches the project directory (ignoring `.git`, `node_modules`, and
similar), debounces file saves, takes a `git diff HEAD` of the changed
files plus the project's `ana.md` conventions, and sends them to the
[background-role model](../configuration/models.md#model-roles) for a
constrained JSON review — at most **4 findings per save**, so the output
stays scannable.

```
$ ana watch
watching ~/myapp (git) — Ctrl-C to stop
14:02:11  src/auth.py saved
  ⚠ login() ignores the `remember_me` flag it accepts
  ⚠ new query interpolates user input — use a bound parameter
```

Reviews run on the background model, so your interactive session's chat
model stays loaded and fast.

## `ana ci` — one-shot diff review

```bash
ana ci "review this diff for correctness" --diff HEAD~1 --output-format json
```

Designed for CI pipelines: reviews the given git range headlessly and exits
with the findings on stdout. With `--output-format json` the findings are
machine-readable for posting as PR comments or gating a pipeline step.

```yaml
# Example GitHub Actions step (self-hosted runner with Ollama):
- name: Ana review
  run: ana ci "review for correctness and security" --diff origin/main --output-format json
```

## In-session review

For reviewing uncommitted work *inside* a chat, use `/review [focus]` — it
reviews the current diff in the session's full project context. See
[Interactive mode](../usage/interactive-mode.md).

## Related

- [Models & presets](../configuration/models.md#model-roles) — the
  background model role
- [Headless mode](../usage/headless.md) — scripting `ana print`
