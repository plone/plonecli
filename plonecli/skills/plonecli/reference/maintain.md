# Running, testing, reconfiguring, updating

## Running & testing

These wrap the project's `invoke` tasks and must run inside the project:

| Command | Delegates to | Notes |
|---|---|---|
| `plonecli serve` | `uv run invoke start` | Serves at http://localhost:8080. **Do not run this yourself** — assume the instance is already running; if not, ask the user to start it. |
| `plonecli debug` | `uv run invoke debug` | Debug instance. **Do not run this yourself** either. |
| `plonecli test` | `uv run invoke test` | Safe to run. `-v`/`--verbose` for verbose output. Run after scaffolding/adding features; report real results; never skip. |

You may also call the underlying tasks directly with `uv run invoke <task>` if `plonecli` itself is unavailable.

## Reconfiguring an existing project

To change settings of an already-generated project, **do not re-run `create`** — re-run the template's questions via the `reconfigure` invoke task (wraps `copier recopy --trust --overwrite` against the right answers file):

```shell
uv run invoke reconfigure --target=addon                     # backend addon package metadata
uv run invoke reconfigure --target=zope-setup                # project-level Plone/Zope settings
uv run invoke reconfigure --target=instance                  # a Zope instance (port, DB, creds)
uv run invoke reconfigure --target=instance --name=instance2 # a specific named instance
```

| Target | Reconfigures | Answers file |
|---|---|---|
| `addon` | Backend addon package settings | `.copier-answers.yml` |
| `zope-setup` | Project-level Plone/Zope settings | `.copier-answers.zope-setup.yml` |
| `instance` | Zope instance (port, DB, credentials) | `.copier-answers.zope-instance-<name>.yml` |

Reconfigure **overwrites** generated config files with the new answers. Afterwards, review `git status`/diff and preserve any local edits worth keeping.

## Updating templates & plonecli

```shell
plonecli update
```

Pulls the latest copier-templates clone and checks PyPI for a newer plonecli. Run this if `create`/`add` reports missing or stale templates. The clone lives at `~/.copier-templates/plone-copier-templates`.

## Pointing at a different template repo/branch

Environment variables override `~/.plonecli/config.toml` and take precedence:

- `PLONECLI_TEMPLATES_REPO_URL` — template repository URL.
- `PLONECLI_TEMPLATES_BRANCH` — branch to track (default `main`).
- `PLONECLI_TEMPLATES_DIR` — local directory for the clone.

```shell
export PLONECLI_TEMPLATES_REPO_URL=https://github.com/myorg/my-templates
export PLONECLI_TEMPLATES_BRANCH=develop
plonecli create addon my.addon
```

Useful for testing custom template forks, CI with pre-cloned templates, or org-maintained template sets.

## Global config

`plonecli config` interactively sets author name/email, GitHub user, default Plone version, and templates repo/branch, saved to `~/.plonecli/config.toml`. On first run it offers to import legacy `~/.mrbob` settings.

## Troubleshooting

- **`NotInPackageError`** — you ran an in-project command (`add`/`setup`/`serve`/`test`/`debug`) outside a project. `cd` into the project root.
- **Template not found / empty `plonecli -l`** — templates clone missing or stale: run `plonecli update`. If `update` itself fails (e.g. `~/.plonecli` is read-only, or `[templates] local_path` in `config.toml` points at a non-existent path such as another user's home) but a templates clone already exists elsewhere, bypass the config by pointing `PLONECLI_TEMPLATES_DIR` at the existing clone, e.g. `export PLONECLI_TEMPLATES_DIR=~/.copier-templates/plone-copier-templates`.
- **Subtemplate not listed** — it does not match the current project type; run `plonecli -l` inside the correct project type.
- **`setup` rejected** — `setup` only runs inside a `backend_addon`.
