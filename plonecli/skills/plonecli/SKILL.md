---
name: plonecli
description: Scaffold and develop Plone packages with plonecli (copier-template based). Use when creating a Plone backend add-on or Zope project, adding features like content types, behaviors, or REST API services, running/testing a Plone instance, or updating/reconfiguring a plonecli-generated project. Triggers on "plonecli", "create a Plone addon", "add a content type/behavior/restapi service", "plone scaffold", "zope-setup".
---

# plonecli

`plonecli` scaffolds and develops Plone packages using [copier](https://copier.readthedocs.io/) templates. It creates backend add-ons and Zope project setups, adds features (content types, behaviors, REST API services) via subtemplates, and wraps the project's `invoke` tasks for serving and testing.

## How to invoke it

- **End users:** `uvx plonecli <command>` (no install needed).
- **Inside this repo (plonecli's own source):** it is not on `PATH` — use `uv run plonecli <command>`.

On first run, plonecli clones the copier-templates to `~/.copier-templates/plone-copier-templates`. If a command complains about missing templates, run `plonecli update` first.

## Command map

| Command | Scope | What it does |
|---|---|---|
| `create <template> <name>` | anywhere | Scaffold a new project (`backend_addon`, `addon` = backend_addon+zope-setup, or `zope-setup`). See [reference/create.md](reference/create.md). |
| `add <subtemplate>` | inside a project | Add a feature. Gated by project type. See [reference/add.md](reference/add.md). |
| `setup` | inside a `backend_addon` | Apply `zope-setup` in place (run a Plone instance around the addon). |
| `serve` | inside a project | `uv run invoke start` → http://localhost:8080. **See server rule below.** |
| `test [-v]` | inside a project | `uv run invoke test`. |
| `debug` | inside a project | `uv run invoke debug`. |
| `update` | anywhere | Pull latest copier-templates + check PyPI for plonecli updates. |
| `config` | anywhere | Interactive global settings → `~/.plonecli/config.toml`. |

`add`, `setup`, `serve`, `test`, `debug` require being inside a plonecli-generated project (detected from `pyproject.toml`); otherwise they fail with `NotInPackageError`. Subtemplates are filtered by the project's type, so `plonecli -l` shows different options depending on where you are.

`serve`, `test`, `debug` additionally need the `invoke` harness (`tasks.py`), which only the **`zope-setup`** layer provides. A project made with `create backend_addon` alone has no `tasks.py` — run `plonecli setup` first (or scaffold with the `addon` composite / `zope-setup`) before these commands work.

## Decision flow

1. **New project?** → `create`. Pure backend add-on: `plonecli create backend_addon my.addon`. Add-on **with** a runnable instance in one step: `plonecli create addon my.addon` (composite = `backend_addon` + `zope-setup`). Zope project: `plonecli create zope-setup my-project`. `addon` is **not** an alias of `backend_addon` — they are different templates. Details and template list: [reference/create.md](reference/create.md).
2. **Add a feature to an existing addon?** → `cd` into the project, then `plonecli add content_type` / `behavior` / `restapi_service`. Field/wiring specifics: [reference/add.md](reference/add.md).
3. **Changed GenericSetup profile XML (`profiles/default/*`) that must reach already-installed sites?** → `plonecli add upgrade_step` to scaffold the migration. See the upgrade-step rule below and [reference/add.md](reference/add.md).
4. **Need a runnable Plone instance around an addon?** → `plonecli setup` (inside the addon).
5. **Run / test it?** → `plonecli test` to test. For serving, follow the server rule below.
6. **Change settings of an already-generated project?** → don't recreate it; use reconfigure. See [reference/maintain.md](reference/maintain.md).
7. **Templates outdated, or want a different template repo/branch?** → `plonecli update`, or env overrides in [reference/maintain.md](reference/maintain.md).

## Critical rules

- **Never start the dev server yourself.** Do not run `plonecli serve` / `plonecli debug` / `invoke start`. Assume the instance is already running; if it is not, ask the user to start it. (`plonecli test` is fine to run.)
- **Use native `uv`.** Run things as `uv run <command>`; never `uv pip` or `pip` unless explicitly told.
- **Tests must pass — never skip them.** After scaffolding or adding a feature, run `plonecli test` and report real results.
- **Profile XML changes need an upgrade step — scaffold it automatically.** Whenever you edit GenericSetup profile XML under `profiles/default/` (e.g. `catalog.xml`, `types/*.xml`, `types.xml`, `workflows.xml`, `registry.xml`, `rolemap.xml`) in a way that must propagate to already-installed sites, run `plonecli add upgrade_step` as part of the same change — don't leave it to the user to remember. It bumps `profiles/default/metadata.xml` and registers a GS upgrade handler; then fill that handler so existing sites actually get the change (reapply the relevant import step or migrate data). Never hand-edit `metadata.xml`'s version to "do an upgrade" — that bumps the number without a registered step. Details and what does/doesn't need a step: [reference/add.md](reference/add.md).
- **Don't recreate to change settings.** Re-running `create` over an existing project is wrong; use the reconfigure flow ([reference/maintain.md](reference/maintain.md)).
- After `create`/`add`/reconfigure, generated files change — review `git status`/diff and preserve intentional local edits.

## Quick start

```shell
# new backend add-on (package only — no runnable instance yet)
plonecli create backend_addon collective.todo
cd collective.todo

# add features
plonecli add content_type
plonecli add behavior
plonecli add restapi_service

# wrap it in a runnable Plone instance (adds the zope-setup / invoke harness)
plonecli setup

# verify (needs the zope-setup layer added above)
plonecli test
```

Shortcut: `plonecli create addon collective.todo` scaffolds `backend_addon` **and** `zope-setup` in one step — use it instead of `create backend_addon` + `setup`. Do not run both; that applies zope-setup twice.

For anything beyond this happy path, read the matching file in `reference/`.
