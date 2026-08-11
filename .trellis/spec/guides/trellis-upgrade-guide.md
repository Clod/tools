# Trellis Upgrade Thinking Guide

> **Purpose**: Run a Trellis version upgrade without silently ending up
> half-migrated.

---

## The Problem

**`trellis update` reports success while skipping files it could not verify.**

Trellis hash-tracks most managed files in `.trellis/.template-hashes.json`
(108 entries as of v0.6.14). Files **not** in that registry cannot be
hash-verified, so the updater conservatively classifies them as
`Modified by you (need your decision)` — and if you do not decide, it
**skips them and still prints `Update complete!`**.

The result is a project where the new files landed but the wiring that
activates them did not. That is what happened in the v0.3.10 → v0.6.8
migration: it reported success, and four things were broken afterwards.

Worst of them was silent: agents had been renamed to `trellis-*`, but the
skipped `inject-subagent-context.py` still matched the old names, so every
sub-agent was dispatched with **zero context injected** and no error
anywhere.

---

## The Unregistered Files

These 7 are not in the hash registry. Verified still unregistered after a
clean v0.6.14 adoption — this is permanent, not a one-off:

| File | Why it matters if skipped |
|------|---------------------------|
| `.claude/hooks/inject-subagent-context.py` | Sub-agents get no PRD/spec context — fails silently |
| `.claude/hooks/session-start.py` | Session context stops matching the task layer |
| `.trellis/workflow.md` | Missing `[workflow-state:*]` blocks → per-turn breadcrumb degrades to a generic line |
| `.trellis/scripts/task.py` | Active-task pointer written to the wrong layer |
| `.trellis/scripts/add_session.py` | Journal/session recording drifts |
| `.trellis/scripts/common/config.py` | Config parsing drifts from `config.yaml` |
| `.trellis/config.yaml` | New knobs never appear |

Also check `.claude/settings.json`: it is **never** managed and holds the
hook wiring. A migration that deletes a hook script leaves a dangling
reference here.

---

## Before Upgrading

- [ ] Working tree committed — git is the real safety net, not `.trellis/.backup-*`
- [ ] `trellis update --dry-run` — read the `Modified by you` list in full
- [ ] `trellis update --migrate --dry-run` — check for pending renames/deletions

---

## The Procedure

Never run a bare `trellis update` and trust the exit message.

```bash
trellis update --create-new     # writes <file>.new, touches nothing else
```

Then diff **every** `.new` file before adopting it. In practice the diffs
are upstream-only (new sections, added platform names, encoding fixes), but
that is the thing worth confirming, not assuming.

```bash
diff .trellis/config.yaml .trellis/config.yaml.new
```

For `config.yaml`, compare the **actual values**, not the comments — most of
the churn is comment reordering:

```bash
grep -vE "^\s*#|^\s*$" .trellis/config.yaml
```

### Gotcha: adopting the `.new` files

`trellis update` writes a backup to `.trellis/.backup-<timestamp>/` that
**contains the `.new` files too**. A repo-wide glob will reach into it and
overwrite the backup's pristine copies:

```bash
# Wrong — also renames files inside .trellis/.backup-*/
find . -name "*.new" | while read f; do mv "$f" "${f%.new}"; done

# Correct — skip the backup directories
find . -name "*.new" -not -path "./.trellis/.backup-*" | \
  while read f; do mv "$f" "${f%.new}"; done
```

---

## After Upgrading — Verify Behavior, Not Exit Codes

A clean `Update complete!` proved nothing in the v0.3.10 → v0.6.8 migration.
Run the hooks and check they emit real content:

```bash
# Every hook referenced in settings.json must exist on disk...
grep -o '\.claude/hooks/[a-z-]*\.py' .claude/settings.json | sort -u | \
  while read h; do [ -f "$h" ] || echo "MISSING $h"; done

# ...and every hook on disk should be wired to something
ls .claude/hooks/*.py | while read h; do
  grep -q "$(basename $h)" .claude/settings.json || echo "UNWIRED $h"; done
```

```bash
# Sub-agent injection must return thousands of bytes, not 0
echo '{"hook_event_name":"PreToolUse","tool_name":"Task","tool_input":
{"subagent_type":"trellis-check","prompt":"t"},"cwd":"'$PWD'"}' | \
  python3 .claude/hooks/inject-subagent-context.py | wc -c
```

```bash
# Breadcrumb must name the task, not fall back to a generic line
echo '{"hook_event_name":"UserPromptSubmit","prompt":"t","cwd":"'$PWD'"}' | \
  python3 .claude/hooks/inject-workflow-state.py
```

| Check | Healthy | Broken |
|-------|---------|--------|
| Sub-agent injection | thousands of bytes | `0` |
| Workflow-state hook | `Task: <name> (<status>)` | `Refer to workflow.md for current step.` |
| Broken/unwired hooks | none | any |
| `trellis update --dry-run` | `Already up to date` | files still listed |
| `trellis update --migrate --dry-run` | no cleanup entries | deprecated files listed |

A `0`-byte injection is the signature failure: nothing errors, agents just
work blind.

---

## Two Layers That Must Agree

Since v0.6.x the active task lives in `.trellis/.runtime/sessions/*.json`,
resolved by `common/active_task.py`. The legacy `.trellis/.current-task`
file is **not** consulted by the newer hooks.

If `task.py` is stale it writes the legacy file while the hooks read the
runtime one, and the breadcrumb reports `no_task` forever even though
`task.py list` shows a current task. Re-point it with:

```bash
python3 .trellis/scripts/task.py start <task-name>
python3 .trellis/scripts/task.py current   # must print the task path
```

---

## Do Not Wipe And Reinstall

When the tooling looks messy, `trellis uninstall` + `trellis init` is
tempting. It removes `.trellis/` **entirely**, including:

- `.trellis/spec/` — the hand-authored guidelines for this codebase
- `.trellis/tasks/` — active and archived task history
- `.trellis/workspace/` — developer journals

A fresh `init` replaces those with empty placeholder templates. The mess is
always in the managed tooling files, which the `--create-new` procedure
above already fixes without touching data.

---

**Core Principle**: The updater's exit message describes what it wrote, not
what still works. Verify behavior.
