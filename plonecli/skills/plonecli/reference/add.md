# Adding features — `plonecli add <subtemplate>`

Run from **inside** a plonecli-generated project. If you are not in one, the command fails with `NotInPackageError` — `cd` into the project root first.

If you *are* inside an addon but it's an **old/legacy package** (mr.bob/`bobtemplates.plone`, buildout, `setup.py`) where `add` lands files in the wrong place or doesn't register them, the structure doesn't yet fit the templates. Don't hand-write the files and don't re-run the `backend_addon` template — make the minimal structural edits first. See [migrate.md](migrate.md).

```shell
cd collective.todo
plonecli add content_type
plonecli add behavior
plonecli add restapi_service
```

## Non-interactive use (required in Claude Code / CI)

By default `add` (and `create`) drop into copier's **interactive prompts**, which cannot be driven from a non-tty environment — they will hang or fail. **Never work around this by hand-rolling the files copier would generate.** Instead drive plonecli non-interactively:

- `--defaults` — answer every question from the template's defaults (no prompts).
- `-d/--data KEY=VALUE` — pre-fill a specific answer (repeatable); overrides the default and skips that prompt.
- `--data-file PATH` — load answers from a YAML/JSON file (handy for many answers); inline `-d` overrides matching keys.

```shell
# fully non-interactive: defaults for everything, override the few you care about
plonecli add content_type --defaults -d content_type_name="Talk" -d content_type_description="A conference talk"
plonecli add behavior --defaults -d behavior_name="IFeatured"
plonecli add restapi_service --defaults -d service_name="@todos"
```

Pass `-d` for every answer the user has specified; `--defaults` covers the rest. Required answers that have no default (e.g. `content_type_name`, `behavior_name`, `service_name`, `upgrade_step_title`) **must** be supplied with `-d` or copier still has to prompt. Don't invent values the user hasn't given — ask first, then pass them via `-d`. The per-template question/answer keys are listed below and shown by the prompts themselves.

## Subtemplates are gated by project type

plonecli detects the project type from `pyproject.toml` (e.g. `backend_addon`, `project`). Only subtemplates whose `parent` matches that type are offered. So:

- Inside a **`backend_addon`**: `content_type`, `behavior`, `restapi_service`, `upgrade_step`, and more (`indexer`, `subscriber`, `vocabulary`, `view`, `viewlet`, `portlet`, `controlpanel`, `form`, `theme*`, `site_initialization`, …).
- Inside a **`zope-setup`** project: `zope_instance`.

Always confirm what is actually available here with `plonecli -l` (run inside the project) — it lists only the applicable subtemplates and reflects the configured template repo/branch.

## The three common backend_addon subtemplates

| Subtemplate | Adds | Typical follow-up |
|---|---|---|
| `content_type` | A Dexterity content type (schema, FTI, registration). | Restart/reinstall the addon so the new type is registered; add tests for the type. |
| `behavior` | A behavior (reusable schema/marker applied to content types). | Wire the behavior onto a content type; add tests. |
| `restapi_service` | A `plone.restapi` service (endpoint, adapter, registration). | Add tests exercising the endpoint. |

copier asks for the specifics (names, fields, options). In Claude Code / CI you cannot answer prompts, so run non-interactively with `--defaults` and pass the user's choices via `-d KEY=VALUE` (see "Non-interactive use" above). Do not invent answers; if the user hasn't specified e.g. field names, ask, then pass them via `-d`.

## After adding

1. Review `git status`/diff — `add` writes new files and may touch existing ones (e.g. `configure.zcml`, `profiles`). Preserve intentional local edits.
2. Run `plonecli test` and report real results. Never skip tests.
3. If a running instance is needed to see the change, ask the user to (re)start it — do not start the server yourself.

## upgrade_step — required after profile XML changes

When you change GenericSetup profile XML under `profiles/default/` in a way that must reach **already-installed** sites, add an upgrade step in the same change. Reinstalling the profile is not an option on real sites, so the migration has to be an upgrade step.

```shell
cd collective.todo
# non-interactive: title is required, the rest default from the addon
plonecli add upgrade_step --defaults -d upgrade_step_title="Reimport viewlets"
```

Questions (defaults injected from the addon — pass `-d` to override any):

| Question | Default | Meaning |
|---|---|---|
| `upgrade_step_title` | (required) | Human-readable title, e.g. "Add catalog index". |
| `upgrade_step_description` | "A custom upgrade step" | What the step does. |
| `source_version` | current `metadata.xml` version | Version being upgraded **from**. |
| `destination_version` | `source + 1` | Version being upgraded **to**. |

`upgrade_step_title` has no default, so it **must** be passed with `-d` — otherwise copier still prompts. Do not skip the command and hand-write the upgrade step files yourself; run it non-interactively as above.

What it does (so you don't do it by hand):

- Bumps `profiles/default/metadata.xml` to `destination_version`.
- Creates `src/<package>/upgrades/` with a handler stub + ZCML registration, and includes `.upgrades` from `configure.zcml`.
- Registers the step in `pyproject.toml` addon settings.

After scaffolding, **fill the generated handler** so existing sites actually get the change — bumping the version alone does nothing. Typically the handler reapplies the relevant GenericSetup import step (e.g. reimport `catalog`, `typeinfo`, `workflow`, `plone.app.registry`) and/or migrates existing data, then add a test under `tests/test_upgrade_<destination_version>.py`.

### Which profile changes need an upgrade step

Need one (change must propagate to live sites):

- `catalog.xml` — new/changed indexes or metadata columns (add index + reindex).
- `types/*.xml`, `types.xml` — FTI changes, new content types, behaviors added to a type.
- `workflows.xml`, `workflows/*.xml` — workflow definition or state changes.
- `registry.xml` — new/changed `plone.registry` records.
- `rolemap.xml` — new roles or permission mappings.

Usually don't:

- Brand-new addon whose profile has never been installed anywhere (initial install covers it).
- Changes that only affect fresh installs and have no existing-site impact.
- `metadata.xml` itself — that's the version marker the upgrade step bumps, not a thing you migrate.

If unsure whether a given profile edit needs migrating to existing sites, add the upgrade step — it's cheap and safe; a missing one silently leaves installed sites stale.

## zope_instance

Inside a `zope-setup` project, `plonecli add zope_instance` adds an additional named Zope instance. Each instance has its own `.copier-answers.zope-instance-<name>.yml` and can later be reconfigured by name ([maintain.md](maintain.md)).
