[![CI](https://github.com/plone/plonecli/actions/workflows/python-package.yml/badge.svg)](https://github.com/plone/plonecli/actions/workflows/python-package.yml)
[![PyPI](https://img.shields.io/pypi/v/plonecli.svg)](https://pypi.python.org/pypi/plonecli/)

# Plone CLI

![Plone CLI Logo](https://raw.githubusercontent.com/plone/plonecli/master/docs/plone_cli_logo.svg)

**A Plone CLI for creating Plone packages**

The Plone CLI is meant for developing Plone packages. It uses [copier](https://copier.readthedocs.io/) templates to scaffold Plone backend addons, Zope project setups, and add features like content types, behaviors, and REST API services.




## Compatibility

Starting from version 7.x, we use copier templates instead of bobtemplates.plone or cookiecutter templates.
This brings some UX advantages and flexibility to the templates and is future-proof.

- Versions >= 7.x use the new copier templates (UV/pyproject.toml instead of buildout) and support Plone >= 6.x.
- Versions == 3.x **(current stable version)** use bobtemplates.plone and some cookieplone templates and also support Plone >= 6.x.
    - When using bobtemplates.plone for Plone 5.x and Python 3, you can use plonecli together with bobtemplates.plone == 6.x. They support Plone 5 and Plone 6, except for the theming templates, which are made for Plone 6. If you really need to create a theming package for Plone 5.x, use bobtemplates.plone < 6.x.


## Installation

### UV Tool (Recommended)

The recommended way to install plonecli is as a UV tool, which makes it available globally:

```shell
uv tool install plonecli
```

To upgrade:

```shell
uv tool upgrade plonecli
```

### Run Without Installing (uvx)

You can run plonecli without installing it using `uvx`:

```shell
uvx plonecli create addon my.addon
```

### In a Virtual Environment

```shell
uv venv
source .venv/bin/activate
uv pip install plonecli
```

### With pipx

```shell
pipx install plonecli
```


## Shell Completion

plonecli supports tab-completion for commands and template names in **bash**, **zsh**, and **fish**.

### Quick Install

```shell
plonecli completion --install
```

This auto-detects your shell and appends the activation line to your `~/.bashrc`, `~/.zshrc`, or fish completions directory. Restart your shell afterward.

### Manual Setup

If you prefer to set it up yourself:

**Bash** (add to `~/.bashrc`):
```shell
eval "$(_PLONECLI_COMPLETE=bash_source plonecli)"
```

**Zsh** (add to `~/.zshrc`):
```shell
eval "$(_PLONECLI_COMPLETE=zsh_source plonecli)"
```

**Fish** (add to `~/.config/fish/completions/plonecli.fish`):
```shell
env _PLONECLI_COMPLETE=fish_source plonecli | source
```

### Faster Startup (Optional)

The `eval` approach generates the completion script on every shell start. For faster startup, save it to a file:

```shell
# Generate once
_PLONECLI_COMPLETE=bash_source plonecli > ~/.plonecli-complete.bash

# Then source from your ~/.bashrc instead of eval
source ~/.plonecli-complete.bash
```


## First Run

On first run, plonecli will clone the copier-templates repository to `~/.copier-templates/plone-copier-templates`.

Configure your author defaults:

```shell
plonecli config
```

This creates `~/.plonecli/config.toml` with your settings.


## Usage

### Available Commands

```shell
plonecli --help

Commands:
  add         Add features to your existing Plone package
  completion  Show or install shell completion
  config      Configure plonecli global settings
  create      Create a new Plone package
  debug       Start the Plone instance in debug mode
  serve       Start the Plone instance
  setup       Run zope-setup inside an existing backend_addon
  skill       Install/update the bundled Agent Skills for AI coding agents
  test        Run the tests in your package
  update      Update copier-templates and check for plonecli updates

Options:
  -l, --list-templates   List available templates
  -V, --versions         Show plonecli and copier-templates versions
  -h, --help             Show this message and exit.
```

The list is context-aware: outside a Plone project only the global commands
(`completion`, `config`, `create`, `skill`, `update`) are shown; inside one,
`create` is replaced by the project commands.

`create`, `add` and `setup` share the non-interactive options, so a package can
be bootstrapped from a script or CI:

```shell
plonecli create addon collective.todo --defaults -d description="Todo lists"
plonecli add content_type --defaults --data-file answers.yml
plonecli setup --defaults -d plone_version=6.1.1
```

| Option              | What it does                                                       |
|---------------------|--------------------------------------------------------------------|
| `-d KEY=VALUE`      | Pre-fill a template answer (repeatable), skipping its prompt        |
| `--data-file FILE`  | Load answers from a YAML/JSON file (`-d` wins on conflicts)        |
| `--defaults`        | Use template defaults for unanswered questions instead of prompting |
| `--allow-dirty`     | Run even if the git repository has uncommitted changes              |
| `--no-git`          | Skip the auto-commit (`create`, `add`)                              |

On a repository with uncommitted changes, an interactive run asks whether to
continue, and a non-interactive one (`--defaults`, or no terminal) aborts so
generated files never silently mix into your work in progress. Pass
`--allow-dirty` when that mixing is intended.


### Creating a Plone Add-on

```shell
plonecli create addon collective.todo
```

Or create a Zope project setup:

```shell
plonecli create zope-setup my-project
```


### Adding Features to Your Plone Add-on

Inside your addon directory, you can add features through subtemplates:

```shell
cd collective.todo

plonecli add content_type
plonecli add behavior
plonecli add restapi_service
```


### Setting Up a Zope Project

Inside an existing addon, set up the Zope project infrastructure:

```shell
cd collective.todo
plonecli setup
```


### Running Your Application

```shell
plonecli serve
```

This delegates to `uv run invoke start` which is configured by the project templates.


### Running Tests

```shell
plonecli test
```

With verbose output:

```shell
plonecli test --verbose
```

Run a single test, or restrict the run to one package:

```shell
plonecli test -t test_behavior_installed
plonecli test -s src/collective/todo
```

Both are passed to the project's `invoke test` task: `-t/--test` becomes pytest's
`-k`, and `-s/--package` becomes the pytest target path. `plonecli test` exits
with the test run's exit code, so it can gate a script or a CI job.

Projects generated before the task gained these parameters need their `tasks.py`
refreshed with `plonecli update && plonecli setup`.


### Debug Mode

```shell
plonecli debug
```


### Updating Templates

```shell
plonecli update
```

This pulls the latest copier-templates and checks PyPI for plonecli updates.


### AI Coding Agent Skills

plonecli ships [Agent Skills](https://www.anthropic.com/news/skills) that teach AI coding agents how to use it: `plonecli` (scaffolding and developing packages) and `plone-schema-fields` (hand-editing Dexterity schema fields and widgets). Because the skills follow the Agent Skills open standard, the same `SKILL.md` files are loaded by Claude Code, Codex, Gemini CLI, Cursor and other compatible agents.

```shell
# install globally for your user (~/.agents/skills + ~/.claude/skills)
plonecli skill install

# install into the current project (.agents/skills + .claude/skills)
plonecli skill install --scope project

# refresh after upgrading plonecli
plonecli skill update

# show where they are installed
plonecli skill status
```

Each skill is written to `~/.agents/skills/<name>` (the open-standard discovery path) and linked from `~/.claude/skills/<name>` for Claude Code. Use `--scope project` to install into the current project instead. Pass `--copy` if your environment cannot create symlinks, and `--force` to overwrite an existing install.


### Reconfiguring an Existing Project

After initial creation, you can re-run a template's questions to change settings without recreating the project. The zope-setup template provides an `invoke reconfigure` task that wraps `copier recopy --trust --overwrite` and points at the right answers file for each target.

```shell
# Reconfigure the backend addon (package metadata, author, etc.)
uv run invoke reconfigure --target=addon

# Reconfigure zope-setup (Plone version, database storage, etc.)
uv run invoke reconfigure --target=zope-setup

# Reconfigure a Zope instance (port, database connection, etc.)
uv run invoke reconfigure --target=instance

# Reconfigure a specific named instance
uv run invoke reconfigure --target=instance --name=instance2
```

Available targets:

| Target       | What it reconfigures                              | Answers file                                  |
|--------------|---------------------------------------------------|-----------------------------------------------|
| `addon`      | Backend addon package settings                    | `.copier-answers.yml`                         |
| `zope-setup` | Project-level Plone/Zope settings                 | `.copier-answers.zope-setup.yml`              |
| `instance`   | Zope instance configuration (port, DB, credentials) | `.copier-answers.zope-instance-<name>.yml`  |

Reconfigure overwrites generated config files with the new answers, so review the diff with `git status` afterwards and keep any local edits you want to preserve.


### Listing Templates

```shell
plonecli -l

Available templates:

  Project templates (plonecli create <template> <name>):
    - backend_addon (alias: addon)
        - behavior
        - content_type
        - restapi_service
    - zope-setup
        - zope_instance
```

When inside a project, only the applicable subtemplates are shown.


## Configuration

### Config File

plonecli stores its configuration at `~/.plonecli/config.toml`:

```toml
[author]
name = "Your Name"
email = "your@email.com"
github_user = "yourgithub"

[defaults]
plone_version = "6.1.1"

[templates]
repo_url = "https://github.com/plone/copier-templates"
branch = "main"
local_path = "~/.copier-templates/plone-copier-templates"
```

The default Plone version is fetched from `https://dist.plone.org/release/` and cached for 24 hours.

Run `plonecli config` to (re)write the file interactively. If it ever becomes
unreadable, plonecli says so and names the path — delete it and run
`plonecli config` again to start fresh.

### Environment Variables

You can override template configuration using environment variables. These take precedence over the config file:

- **`PLONECLI_TEMPLATES_REPO_URL`** — Override the copier-templates repository URL.
- **`PLONECLI_TEMPLATES_BRANCH`** — Override the branch to track (default: `main`).
- **`PLONECLI_TEMPLATES_DIR`** — Override the local directory for the templates clone.

Example:

```shell
export PLONECLI_TEMPLATES_REPO_URL=https://github.com/myorg/my-templates
export PLONECLI_TEMPLATES_BRANCH=develop
plonecli create addon my.addon
```

This is useful for:

- Testing custom template forks
- CI/CD environments with pre-cloned templates
- Organizations maintaining their own template sets


## Template Registry

plonecli discovers available templates dynamically by scanning for `copier.yml` files in the templates directory. Each template must include a `_plonecli` metadata section in its `copier.yml` so that plonecli knows how to classify and present it.

### Metadata Convention

Add a `_plonecli` key to your template's `copier.yml`. Copier ignores unknown `_`-prefixed keys, so this is safe and non-breaking.

**Main template** (used with `plonecli create`):

```yaml
# backend_addon/copier.yml
_plonecli:
  type: main
  aliases:
    - addon
  description: "Create a Plone backend add-on package"

# ... regular copier questions below ...
package_name:
  type: str
  help: "Package name (e.g. collective.todo)"
```

**Subtemplate** (used with `plonecli add`):

```yaml
# content_type/copier.yml
_plonecli:
  type: sub
  parent: backend_addon
  description: "Add a Dexterity content type"

# ... regular copier questions below ...
```

### Metadata Fields

- **`type`** *(required)* — Either `main` or `sub`.
  - `main`: A project template, available via `plonecli create <template> <name>`.
  - `sub`: A feature template, available via `plonecli add <template>` when inside a matching project.

- **`parent`** *(required for sub, ignored for main)* — The `project_type` of the parent project this subtemplate applies to. This must match the project type that plonecli detects from the project's `pyproject.toml` (e.g. `backend_addon`, `project`). A subtemplate only appears when you are inside a project of the matching type.

- **`aliases`** *(optional, default: [])* — A list of alternative names users can type instead of the directory name. For example, `aliases: [addon]` lets users run `plonecli create addon my.addon` instead of `plonecli create backend_addon my.addon`.

- **`description`** *(optional)* — A short human-readable description shown in `plonecli -l` output.

- **`deprecated`** *(optional, default: false)* — Set to `true` to mark a template as deprecated. Deprecated templates still work but show a warning.

- **`info`** *(optional)* — An informational message displayed when the template is used (e.g. migration instructions for deprecated templates).

### How Discovery Works

1. plonecli clones the configured copier-templates repository to `~/.copier-templates/plone-copier-templates` on first run.
2. The template registry scans each subdirectory for a `copier.yml` file.
3. It reads the `_plonecli` metadata section from each `copier.yml`.
4. Templates without a `_plonecli` section are still discovered but treated as subtemplates with no parent assignment (they won't appear in any listing).

### Template Directory Structure

A copier-templates repository should follow this layout:

```text
copier-templates/
├── backend_addon/
│   ├── copier.yml          # Must contain _plonecli metadata
│   └── {{package_name}}/   # Copier template files
├── content_type/
│   ├── copier.yml
│   └── ...
├── behavior/
│   ├── copier.yml
│   └── ...
└── zope-setup/
    ├── copier.yml
    └── ...
```

Each subdirectory with a `copier.yml` is treated as a template. The directory name is the canonical template name.

### Example: Adding a New Template

To add a new subtemplate (e.g. a `viewlet` template for backend addons):

1. Create a `viewlet/` directory in your copier-templates repository.
2. Add a `copier.yml` with the `_plonecli` metadata and your copier questions:

   ```yaml
   _plonecli:
     type: sub
     parent: backend_addon
     description: "Add a viewlet"

   viewlet_name:
     type: str
     help: "Name of the viewlet"
   ```

3. Add your template files (Jinja2 templates rendered by copier).
4. Commit and push. Users pick it up with `plonecli update`.

No changes to plonecli itself are needed -- the new template is discovered automatically.

### Roadmap

See [ROADMAP.md](ROADMAP.md) for planned features including multi-package template support via Python entrypoints and publishing `plone-copier-templates` on PyPI.


## Developer Guide

### Setup Developer Environment

```shell
git clone https://github.com/plone/plonecli/
cd plonecli
uv sync --extra dev --extra test
plonecli --help
```


### Shell Completion for Development

When developing plonecli or copier-templates from a git checkout, the installed `plonecli` entry point may not reflect your local changes. Use `uv run` to run the development version, but note that tab-completion only works for the installed `plonecli` command, not `uv run plonecli`.

For development, temporarily install the package in editable mode so that the `plonecli` entry point uses your local code:

```shell
uv tool install --editable .
```

This makes the global `plonecli` command point to your working copy, and shell completion works normally. When done, reinstall the released version:

```shell
uv tool install plonecli
```


### Running Tests

```shell
# Using tox
tox

# Or directly with pytest
uv run pytest tests/

# A single test
uv run pytest tests/ -k test_find_project_root
```


## Contribute

- Issue Tracker: https://github.com/plone/plonecli/issues
- Source Code: https://github.com/plone/plonecli


## License

This project is licensed under the BSD license.
