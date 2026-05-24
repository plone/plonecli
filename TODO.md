# plonecli / copier-templates — issues to fix

Issues found while scaffolding the `derico.todos` addon with `plonecli 7.0.0b9`
and `copier-templates @ 12bcbdb` (Plone 6.1.2). Grouped by the repo that owns
the fix.

- plonecli: https://github.com/plone/plonecli
- templates: https://github.com/plone/copier-templates

---

## Re-test status — `plonecli 7.0.0b10`, `copier-templates @ 8f5fabb` (2026-05-24)

Re-scaffolded `derico.todos` (Todos container + Todo item + views + vocabulary +
restapi_service, Plone 6.2.0). Status of the issues below in b10:

**Fixed in b10 ✅**
- plonecli #1 — composite `create addon` now runs non-interactively: `.gitignore`
  is `overwrite`d and `pyproject.toml`/`README.md` are `skip`ped, no
  `InteractiveSessionError`.
- templates #3 — generated `content_type`/`view` tests now request the correct
  `integration` fixture (not `integration_testing`).
- templates #4 — `content_type` tests now use
  `queryUtility(IDexterityFTI, name=...)` (the interface, not the `DexterityFTI`
  class) and pass.
- templates #6 — `view` hook now writes a second `browser:page` with the same
  `name="view"` but a different `for=` (both Todos and Todo `view`s registered).

**Still broken in b10 ❌**
- templates #5 — `content_type` tests still create the type in the portal root
  and ignore `global_allow=false`. For the `Todo` item (addable only inside
  `Todos`) `test_factory`/`test_adding`/`test_deleting` fail with
  `InvalidParameterError: Disallowed subobject type: Todo`. Fix must create a
  `parent_content_type` container first and add the item inside it.
- plonecli #2 / templates #2 — the `zope-setup` `create_initial_instance` hook
  still shells out to a bare `copier`, which is not on PATH when plonecli is a
  `uv tool`. Had to run `create` with
  `PATH="$(dirname $(command -v plonecli))/../...plonecli/bin:$PATH"` so the
  `copier` console script from plonecli's own venv is found.
- notes — `plonecli test` (`uv run invoke test`) still can't find pytest; the
  `dev` extra lacks it. Must run `uv run --extra test pytest`.

**New finding (b10)**
- templates (backend_addon) — the generated `.gitignore` ignores `*.pot`
  (line ~50), but the addon ships `src/<pkg>/locales/<domain>.pot` as the
  canonical message catalog that the per-language `.po` files derive from
  (i18ndude `update.sh`). The `.pot` should be tracked; `*.pot` should be
  dropped from `.gitignore` (or the locales `.pot` force-added).
- templates (backend_addon) — the shipped `locales/update.py` helper trips the
  project's own ruff config: 3× `S602` (`subprocess.call(..., shell=True)`) and
  an `E501` long line. Either rewrite the calls without `shell=True` or add
  `locales/update.py` to `[tool.ruff.lint.per-file-ignores]` so a fresh addon
  passes `ruff check` out of the box.

---

## plonecli (the CLI)

### 1. Non-interactive composite/overlay aborts on file conflicts
- [ ] `plonecli create addon <name>` (composite `backend_addon` → `zope-setup`)
      fails non-interactively: the second step hits files the first step
      already wrote (`.gitignore`, `.github/workflows/ci.yml`) and copier
      raises `InteractiveSessionError: Consider using --overwrite`.
- **Where:** `plonecli/templates.py` → `run_create()` / `run_add()` call
  `run_copy(...)` without `overwrite=True`; `plonecli/cli.py` `create`/`add`/
  `setup` expose no `--overwrite`.
- **Fix options:**
  - Pass `overwrite=True` for composite sub-steps (the second template
    legitimately layers onto the first), and/or
  - Add an `--overwrite` flag to `create`/`add` and a non-interactive path
    (`--defaults`/`-d`/`--overwrite`) to `setup` (it currently takes no
    options and only runs interactively, requiring a clean git tree).
- **Note:** also see templates item #1 (`.gitignore` should be in
  `_skip_if_exists`) — the two fixes are complementary.

### 2. `copier` CLI not reachable from template hooks
- [ ] The `zope-setup` `create_initial_instance` hook shells out to a bare
      `copier` executable. When plonecli is installed as a `uv tool`, only
      plonecli's own entry point is put on PATH — the `copier` console script
      from its dependencies is not — so the hook dies with
      `FileNotFoundError: 'copier'`. After installing it, a second failure
      appears: `No module named 'copier_template_extensions'`.
- **User intent:** copier is already a library dependency of plonecli, so the
  `copier` CLI should be guaranteed available rather than assumed on PATH.
- **Fix options:**
  - Ensure `copier` **and** `copier-template-extensions` are declared deps and
    that the CLI is reachable (e.g. document / enforce
    `uv tool install plonecli --with copier --with copier-template-extensions`,
    or expose the script), **and/or**
  - Make the hooks invoke copier through a guaranteed interpreter instead of a
    bare PATH lookup — see templates item #2.
- **Workaround used:** `uv tool install copier --with copier-template-extensions`.

---

## copier-templates (the templates)

### 1. `zope-setup` `_skip_if_exists` is incomplete
- [ ] `zope-setup/copier.yml` lists only `pyproject.toml` and `README.md` under
      `_skip_if_exists`, but `backend_addon` also writes `.gitignore` and
      `.github/workflows/ci.yml`. Layering `zope-setup` over an existing
      `backend_addon` therefore conflicts on those files (root cause of
      plonecli item #1).
- **Fix:** add `.gitignore` (and the `.github/workflows/ci.yml` it would
  overwrite) to `_skip_if_exists`, or otherwise reconcile the two templates'
  shared files.

### 2. `create_initial_instance` hook calls a bare `copier`
- **Where:** `zope-setup/copier_hooks.py` (`create_initial_instance`, ~L87–110)
  builds `cmd = ["copier", "copy", "--trust", ...]` and `subprocess.run(cmd)`.
- [ ] Invoke copier in a way that does not depend on a bare `copier` being on
      PATH and that includes the required Jinja extension, e.g.
      `python -m copier ...` (same interpreter) or
      `uv run --with copier --with copier-template-extensions copier copy ...`.

### 3. Generated tests request a non-existent `integration_testing` fixture
- **Where:**
  - `content_type/template/tests/test_ct_{{content_type_module}}.py.jinja`
  - `view/template/tests/test_view_{{view_module}}.py.jinja`
- [ ] They use `def _setup(self, integration_testing): self.portal =
      integration_testing["portal"]`, but `pytest-plone` provides a fixture
      named **`integration`** (not `integration_testing`). Tests error with
      `fixture 'integration_testing' not found`.
- **Fix:** rename the fixture parameter/usages to `integration`.
- **Note:** `backend_addon`'s own `tests/test_setup.py` already uses the correct
  `integration` fixture — only the sub-template tests are wrong.

### 4. Content-type tests look up the FTI by the wrong object
- **Where:** `content_type/template/tests/test_ct_{{content_type_module}}.py.jinja`
- [ ] Uses `from plone.dexterity.fti import DexterityFTI` and
      `queryUtility(DexterityFTI, name="<Type>")`, which returns `None`
      (`DexterityFTI` is the class, not the lookup interface).
- **Fix:** use `from plone.dexterity.interfaces import IDexterityFTI` +
  `queryUtility(IDexterityFTI, name=...)`, or
  `portal.portal_types.get("<Type>")`.

### 5. Content-type tests ignore `global_allow=false`
- **Where:** `content_type/template/tests/test_ct_{{content_type_module}}.py.jinja`
- [ ] `test_factory`/`test_adding`/`test_deleting` always create the type in the
      portal root. For a type with `global_allow=false` (added under a specific
      parent) this is not addable in the root and the tests fail.
- **Fix:** when `global_allow` is false, create a parent container of
  `parent_content_type` first and create the item inside it (the template
  already knows `parent_content_type_resolved`). Consider also asserting the
  type appears in the parent's `allowedContentTypes()`.

### 6. `view` hook dedupes `browser:page` by `name` only
- **Where:** `view/copier_hooks.py` → `extend_configure_zcml(...,
  identifying_attr="name", identifying_value=view_name, ...)`.
- [ ] Registering a second view with the same `name` (e.g. two content-type
      `view`s named `view`) but a different `for=` is silently skipped:
      `browser:page with name='view' already exists ...`. The second
      registration is never written.
- **Fix:** dedupe by the composite key (`name` **and** `for`) so distinct
  `for=` registrations sharing a `name` are both emitted (extend
  `extend_configure_zcml` to accept multiple identifying attributes, or pass a
  composite identifier from the view hook).

---

## Notes / nice-to-haves
- The `dev` optional-dependency extra only contains `invoke`/`watchdog`, so
  `plonecli test` (`uv run invoke test`) fails with `Failed to spawn: invoke`
  unless that extra is synced. Either have `invoke test` run under the right
  extra, or document `uv run --extra test pytest`.
- `plone_version` is asked once for the composite but `backend_addon` expects a
  minor (`6.1`) while `zope-setup` expects a full version (`6.1.2`); a single
  `-d plone_version=...` cannot satisfy both. Consider deriving the
  zope-setup full version from the backend minor (or vice versa) so the
  composite stays consistent.
