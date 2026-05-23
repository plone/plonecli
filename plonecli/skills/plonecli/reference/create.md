# Creating projects — `plonecli create <template> <name>`

```shell
plonecli create backend_addon collective.todo   # backend add-on package only
plonecli create addon collective.todo            # backend add-on + zope-setup (composite)
plonecli create zope-setup my-project            # Zope project setup
```

Like `add`, `create` is interactive by default. In Claude Code / CI run it non-interactively with `--defaults` (use template defaults) plus `-d/--data KEY=VALUE` for any answer you want to set, e.g. `plonecli create backend_addon collective.todo --defaults -d package_description="Todo manager"`. Do not call `copier` directly. The `-d` keys each project template accepts (`backend_addon`, `zope-setup`, the `addon` composite) — defaults, choices, and conditional questions like `db_storage`/`distribution` — are catalogued in [templates.md](templates.md).

## Project templates

Discover them live with `plonecli -l` (this is authoritative — the registry scans `copier.yml` files in the templates clone, so available templates depend on the configured template repo/branch).

| Template | Alias | Purpose |
|---|---|---|
| `backend_addon` | — | A Plone backend add-on package (the thing you develop). No alias. |
| `addon` | `add-on` | **Composite** — applies `backend_addon` then `zope-setup` in one go. |
| `zope-setup` | `project` | A Zope/Plone project setup that can run an instance. |

`create` accepts either a template name or an alias (e.g. `add-on` → `addon`, `project` → `zope-setup`). Note `addon` and `backend_addon` are **different** templates: `addon` is the composite that also lays down the runnable zope-setup layer, while `backend_addon` is just the add-on package.

## Composite templates

A template may define **composite steps** — `create` then applies several sub-templates in sequence, echoing each step. `addon` is exactly this: it walks `backend_addon` then `zope-setup`. You do not need to do anything special; just run `create` once and let it walk the steps. Because `addon` already includes `zope-setup`, do **not** also run `plonecli setup` afterward — that would apply zope-setup twice.

## Naming

- Backend add-on names use dotted package notation: `collective.todo`, `my.addon`. This becomes the Python package and the project directory.
- Zope-setup names are plain project directory names: `my-project`.

## What gets generated

A scaffolded project includes `pyproject.toml` (plonecli detects the project type from this) and a `.copier-answers*.yml` recording the answers — used later by reconfigure. Do not hand-edit the answers files; change settings via reconfigure ([maintain.md](maintain.md)).

The `tasks.py` for `invoke` (which drives `serve`/`test`/`debug`/`reconfigure`) is provided by the **`zope-setup`** layer — not by a bare `backend_addon`. So a project made with `create backend_addon` alone has no `tasks.py`, and `plonecli test`/`serve`/`debug` won't work in it until you add zope-setup via `plonecli setup`. Projects made with `create addon` (composite) or `create zope-setup` already include `tasks.py`.

## After creating

1. `cd` into the new project directory.
2. Add features with `plonecli add ...` ([add.md](add.md)).
3. Run `plonecli test` and report results — do not skip tests.
4. `create` initialises a git repo and commits the generated package (one commit per template; the `addon` composite makes two). Review it with `git log`/`git show`. Pass `--no-git` to skip both the init and the commit.
5. Do **not** auto-start the server; if a running instance is needed, ask the user.

## Adding a Zope instance to an existing addon

If you already have a `backend_addon` and need a runnable Plone instance around it, do **not** create a separate project — run `plonecli setup` inside the addon. It applies `zope-setup` in place. `setup` only works inside a `backend_addon`; elsewhere it errors.
