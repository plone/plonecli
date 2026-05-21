# Adapting an old/legacy package to fit plonecli

Older Plone packages (mr.bob / `bobtemplates.plone`, buildout, `setup.py`) often
have a structure that plonecli's copier subtemplates can't fully wire into. When
`plonecli add ...` would land files in the wrong place or fail to register them,
**do not hand-write the subtemplate output in the old style, and do not re-run
the `backend_addon` template over the package** — that template overwrites files
like `src/<package>/__init__.py` (it is *not* in `_skip_if_exists`) and would
destroy real code there.

Instead: **inspect the existing structure, compare it against what recent
plonecli + copier-templates actually need to function, and make only the minimal,
needed changes by hand** — preserving all existing code. Real package layouts
vary too much for a one-shot re-scaffold; a targeted edit is safer and an agent
can do it better.

## How the subtemplates wire in (so you know what to provide)

`plonecli add <subtemplate>` runs `copier copy` into the project root, then a
post-copy hook edits a few existing files. Those hooks (in
`shared/hooks/addon_context.py`, `shared/utils/xml_updater.py`,
`shared/utils/pyproject_updater.py`):

- **Detect the parent addon** from `pyproject.toml`'s
  `[tool.plone.backend_addon.settings]` (preferred) or fall back to
  `bobtemplate.cfg` / `setup.py` (package name inferred). On the legacy fallback
  they still run but print "Consider running the backend_addon template to
  modernize" and registration is less reliable.
- **Register the new feature** into
  `[tool.plone.backend_addon.settings.subtemplates]` (`content_types`,
  `behaviors`, `services`, …) — this needs a `pyproject.toml` to write to.
- **Extend ZCML by appending before the closing `</configure>` tag**, and add
  `<include package=".behaviors" />`-style lines to the package's
  `configure.zcml` — **but only if that file already exists** (`if
  parent_zcml.exists()`); otherwise the include is *silently skipped* and the
  feature never loads. There are **no special comment markers** — the anchor is
  the `</configure>` / `</object>` closing tag, and missing leaf files
  (`behaviors/configure.zcml`, `types.xml`) are auto-created. xmlns prefixes are
  auto-added as needed; edits are idempotent.

## What recent plonecli/copier-templates need to function

Check the package against this list and fix only what's missing:

1. **`pyproject.toml` with `[tool.plone.backend_addon.settings]`** — at minimum
   `package_name` and `package_folder` (folder = package name with `.`→`/`, e.g.
   `collective.todo` → `collective/todo`). Also add the empty subtemplates table
   so registration has somewhere to write:

   ```toml
   [tool.plone.backend_addon.settings]
   package_name = "collective.todo"
   package_folder = "collective/todo"

   [tool.plone.backend_addon.settings.subtemplates]
   content_types = []
   behaviors = []
   services = []
   ```

   This single block is what makes `plonecli` detect the project as a
   `backend_addon` (see `project.py`) and what subtemplate hooks read/write. If
   the package has only `setup.py`/`bobtemplate.cfg` and no `pyproject.toml`,
   adding this block is usually the highest-value minimal change. Leave the rest
   of an existing working `pyproject.toml` (deps, build-system) alone unless it's
   actually broken.

2. **`src/<package_folder>/` source layout.** If the package uses a flat or
   different layout, the subtemplates still target `src/<package_folder>/…`.
   Confirm this path exists and matches `package_folder`.

3. **`src/<package_folder>/configure.zcml` must exist** and contain a
   `<configure …> … </configure>` block. Without it, every `<include package=…/>`
   the hooks try to add is dropped silently. If it's missing, create a minimal
   one (don't overwrite an existing one):

   ```xml
   <configure
       xmlns="http://namespaces.zope.org/zope"
       xmlns:genericsetup="http://namespaces.zope.org/genericsetup"
       xmlns:plone="http://namespaces.plone.org/plone"
       i18n_domain="collective.todo">

   </configure>
   ```

   The hooks add missing xmlns prefixes themselves, so a basic root is enough.

4. **`profiles/default/metadata.xml` with a `<version>`** — required for
   `plonecli add upgrade_step` (the hook reads and bumps `<version>`). `types.xml`
   is auto-created for content types if absent.

5. **Preserve real code.** If `src/<package>/__init__.py` contains a message
   factory, namespace declaration, or imports, keep them. If `configure.zcml` /
   `setuphandlers.py` already exist, keep them — only extend. This is exactly why
   we migrate by hand rather than re-running the template.

## The invoke task harness (`tasks.py`)

A migrated package should end up with the **same complete, working `tasks.py`**
that a freshly generated project has — the one that drives `serve`/`test`/
`debug`/`reconfigure` (`uv run invoke <task>`). The current template ships these
tasks: `install`, `start`, `debug`, `shell`, `test`, `create_instance`,
`reconfigure`, `create_site`, `format`, `lint`. A legacy package usually has
*no* `tasks.py`, or an old buildout/mr.bob-era one missing most of these.

**`tasks.py` belongs to the `zope-setup` layer, not to `backend_addon`** — it is
rendered from `zope-setup/template/tasks.py.jinja` with the project's own
variables (`project_name`, `base_path`, `distribution_name`, …), so it
automatically fits the package structure. **Never hand-write or hand-patch
`tasks.py`** — a hand-rolled file won't match the template (stale task set, wrong
paths) and drifts on the next update.

The rule, by state of the package:

- **No compatible `zope-setup` yet** (no `.copier-answers.zope-setup.yml`, no
  runnable instance, `tasks.py` absent or legacy) → the invoke tasks don't apply
  yet, so **don't add them**. First create the zope-setup layer with
  `plonecli setup` (run inside the `backend_addon` — it applies `zope-setup` in
  place). That lays down the complete, package-fitting `tasks.py` as a side
  effect. Only *after* the zope-setup exists do `serve`/`test`/`debug`/
  `reconfigure` make sense. `tasks.py` is **not** in zope-setup's
  `_skip_if_exists` (only `pyproject.toml` and `README.md` are), so `setup`
  overwrites a legacy `tasks.py` with the fresh one — which is what we want.
  Still review the diff; the build/dev harness is meant to be replaced, but
  confirm nothing project-specific was lost.

- **A `zope-setup` already exists** but its `tasks.py` is stale or incomplete
  (missing tasks compared to the list above, or pointing at old paths) →
  regenerate it from the current template with
  `uv run invoke reconfigure --target=zope-setup` ([maintain.md](maintain.md)),
  which overwrites `tasks.py` with the up-to-date version. Don't edit it by hand.

Do **not** run `plonecli setup` just to get `tasks.py` if the user only wants the
add-on package and no runnable instance — `setup` brings the whole zope-setup
layer. Confirm a runnable instance is wanted before adding it.

## Workflow

1. **Start from a clean git state** so every change is a reviewable diff.
2. **Inspect:** list `src/`, read `pyproject.toml` (or `setup.py`/`setup.cfg`/
   `bobtemplate.cfg`), and check for the four items above. Identify the gap.
3. **Apply the minimal fix(es)** by hand — typically just the
   `[tool.plone.backend_addon.settings]` block, and a stub `configure.zcml` only
   if absent. Do not touch working config you don't need to.
4. **Verify detection:** `plonecli -l` inside the package should now list the
   `backend_addon` subtemplates.
5. **Add the feature the normal way** ([add.md](add.md)), e.g.
   `plonecli add behavior --defaults -d behavior_name="IFeatured"`, then review
   the diff to confirm files landed under `src/<package_folder>/…` and the
   include/registration were added.
6. **Ensure a complete `tasks.py`** if the package should be runnable/testable.
   If there's no compatible zope-setup yet, run `plonecli setup` to create it —
   that supplies the full, package-fitting `tasks.py`; don't hand-write one. If a
   zope-setup exists with a stale `tasks.py`, regenerate via
   `uv run invoke reconfigure --target=zope-setup`. See the invoke-task-harness
   section above.
7. **Run `plonecli test`** and report real results (this needs the zope-setup
   layer / `tasks.py` from step 6; see [maintain.md](maintain.md)). Never skip
   tests.

## What to recommend but not force

You may *recommend* modernizing outdated config (buildout/tox → uv, `setup.py` →
hatchling `pyproject.toml`, `*.rst` → `*.md`) and explain the benefit, but if it
still works with current plonecli, **don't change it on your own** — leave it and
let the user decide. The migration's goal is to make `plonecli add` work with the
least disruption, not to rewrite the package.
