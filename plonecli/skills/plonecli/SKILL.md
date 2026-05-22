---
name: plonecli
description: Scaffold and develop Plone packages with plonecli (copier-template based). Use this BEFORE hand-writing any Plone add-on code — including when a plan or task step decides to create/implement a Plone feature such as a behavior, content type, view, viewlet, portlet, vocabulary, indexer, subscriber, control panel, form, REST API service, theme, or upgrade step. Scaffold these with plonecli subtemplates instead of writing files by hand. Also for any plonecli command (create, add, setup, serve, test, debug, update, config); creating a backend add-on or Zope project; scaffolding a GenericSetup upgrade step after profile XML changes so they reach installed sites; adapting an old/legacy package (mr.bob, buildout, setup.py) to plonecli's structure. Triggers on "plonecli ...", "create a Plone addon", "add/create/implement a behavior (or content type / restapi service / ...)", "add upgrade_step", "migrate installed Plone sites", "zope-setup". The -d KEY=VALUE answers each template accepts are in reference/templates.md.
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
2. **Add a feature to an existing addon?** → `cd` into the project, then `plonecli add content_type` / `behavior` / `restapi_service`. Field/wiring specifics: [reference/add.md](reference/add.md). **Old/legacy package that doesn't fit the templates?** (no `[tool.plone.backend_addon.settings]`, `setup.py`/`bobtemplate.cfg`/buildout layout, `plonecli -l` lists nothing, or `add` lands files/registrations wrong) → don't hand-write subtemplate files, and don't re-run the `backend_addon` template (it overwrites `__init__.py` and real code). Inspect the structure and make the minimal edits the subtemplate hooks need. See the legacy rule below and [reference/migrate.md](reference/migrate.md).
3. **Changed GenericSetup profile XML (`profiles/default/*`) that must reach already-installed sites?** → `plonecli add upgrade_step` to scaffold the migration. See the upgrade-step rule below and [reference/add.md](reference/add.md).
4. **Need a runnable Plone instance around an addon?** → `plonecli setup` (inside the addon).
5. **Run / test it?** → `plonecli test` to test. For serving, follow the server rule below.
6. **Change settings of an already-generated project?** → don't recreate it; use reconfigure. See [reference/maintain.md](reference/maintain.md).
7. **Templates outdated, or want a different template repo/branch?** → `plonecli update`, or env overrides in [reference/maintain.md](reference/maintain.md).

## Critical rules

- **Scaffold Plone features with plonecli — don't hand-write them.** The moment a task or plan calls for a behavior, content type, view, viewlet, portlet, vocabulary, indexer, subscriber, control panel, form, REST API service, theme, upgrade step, or any other Plone artifact, the first step is `plonecli add <subtemplate>` (inside the addon), not creating `.py`/`.zcml`/`.xml` files by hand. The templates wire up registration, profiles, and tests correctly; hand-rolled files miss those. Only fall back to manual edits for the legacy-package case below, and even then only the minimal hooks plonecli needs.
- **`create`/`add` are interactive by default — always run them non-interactively here.** copier opens prompts you cannot answer in Claude Code / CI (they hang or fail). Pass `--defaults` (use template defaults for unasked questions) plus `-d/--data KEY=VALUE` (repeatable) for each answer the user specified — or `--data-file PATH` for a YAML/JSON file of answers (`-d` overrides matching keys). Required answers without a default (`content_type_name`, `behavior_name`, `service_name`, `upgrade_step_title`) **must** be given via `-d`. **The full catalogue of every template's `-d` keys, defaults, choices, conditional/computed answers and which are required is [reference/templates.md](reference/templates.md)** — consult it to build the invocation instead of guessing or triggering a prompt. Example: `plonecli add upgrade_step --defaults -d upgrade_step_title="Reimport viewlets"`. **Never give up on a prompt and hand-write the files the subtemplate would generate** — drive plonecli non-interactively instead. Don't invoke `copier` directly. See [reference/add.md](reference/add.md).
- **Never start the dev server yourself.** Do not run `plonecli serve` / `plonecli debug` / `invoke start`. Assume the instance is already running; if it is not, ask the user to start it. (`plonecli test` is fine to run.)
- **Use native `uv`.** Run things as `uv run <command>`; never `uv pip` or `pip` unless explicitly told.
- **Tests must pass — never skip them.** After scaffolding or adding a feature, run `plonecli test` and report real results.
- **Profile XML changes need an upgrade step — scaffold it automatically.** Whenever you edit GenericSetup profile XML under `profiles/default/` (e.g. `catalog.xml`, `types/*.xml`, `types.xml`, `workflows.xml`, `registry.xml`, `rolemap.xml`) in a way that must propagate to already-installed sites, run `plonecli add upgrade_step --defaults -d upgrade_step_title="<what changed>"` as part of the same change — don't leave it to the user to remember. It bumps `profiles/default/metadata.xml` and registers a GS upgrade handler; then fill that handler so existing sites actually get the change (reapply the relevant import step or migrate data). Never hand-edit `metadata.xml`'s version to "do an upgrade" — that bumps the number without a registered step. Details and what does/doesn't need a step: [reference/add.md](reference/add.md).
- **Don't recreate to change settings.** Re-running `create` over an existing project is wrong; use the reconfigure flow ([reference/maintain.md](reference/maintain.md)).
- **Old/legacy package: adapt the structure minimally, never hand-roll old-style files.** If `plonecli add` won't wire features into an old package (mr.bob/`bobtemplates.plone`, buildout, `setup.py` — typically missing `[tool.plone.backend_addon.settings]` or a `src/<package_folder>/configure.zcml`), don't fall back to writing the subtemplate's files by hand, and don't re-run the `backend_addon` template over it (it overwrites `__init__.py` and other real code). Inspect what's there, then make only the minimal edits the subtemplate hooks need to function — chiefly the `[tool.plone.backend_addon.settings]` block (so plonecli detects the addon and can register subtemplates) and a stub `src/<package_folder>/configure.zcml` if absent (hooks append `<include>`s before `</configure>` and silently skip it when the file is missing). Preserve existing code; recommend but don't force broader modernization. Then run `plonecli add` normally. **A migrated package should also end up with the same complete, working `tasks.py` a freshly generated one has — but `tasks.py` comes from the `zope-setup` layer, so never hand-write it: if there's no compatible zope-setup yet, run `plonecli setup` to get it (that lays down the package-fitting `tasks.py`); if a zope-setup exists with a stale `tasks.py`, regenerate via `uv run invoke reconfigure --target=zope-setup`.** Details: [reference/migrate.md](reference/migrate.md).
- `create` and `add` auto-commit by default (`create` also `git init`s the package); review with `git log`/`git show`. Any uncommitted local edits get swept into that commit, so commit/stash your work first, or pass `--no-git` to skip the commit. On a dirty repo, `create`/`add`/`setup` warn and prompt to continue (default: cancel); `--defaults` (or no tty) skips the prompt and proceeds after the warning. `reconfigure` does not commit — review its changes with `git status`/diff and preserve intentional local edits.

## Quick start

```shell
# new backend add-on (package only — no runnable instance yet)
plonecli create backend_addon collective.todo
cd collective.todo

# add features (non-interactive: --defaults + -d for each answer)
plonecli add content_type --defaults -d content_type_name="Talk"
plonecli add behavior --defaults -d behavior_name="IFeatured"
plonecli add restapi_service --defaults -d service_name="@todos"

# wrap it in a runnable Plone instance (adds the zope-setup / invoke harness)
plonecli setup

# verify (needs the zope-setup layer added above)
plonecli test
```

Shortcut: `plonecli create addon collective.todo` scaffolds `backend_addon` **and** `zope-setup` in one step — use it instead of `create backend_addon` + `setup`. Do not run both; that applies zope-setup twice.

For anything beyond this happy path, read the matching file in `reference/`.
