# plonecli / copier-templates — DX improvement ideas

Smoothness / developer-experience ideas gathered while scaffolding the
`derico.todos` addon end-to-end with **plonecli 7.0.0b10** /
**copier-templates @ 8f5fabb** (Plone 6.2.0). These are *enhancements* —
the concrete bugs (failing generated tests, `copier`-on-PATH, gitignored
`*.pot`, ruff `S602` in `update.py`, etc.) are tracked separately in
`TODO.md`. Ordered by how much manual work they would have saved.

- plonecli: https://github.com/plone/plonecli
- templates: https://github.com/plone/copier-templates

---

## High impact — these forced hand-editing of generated files

### 1. `content_type` should be able to scaffold **fields** (templates)
Today the subtemplate emits a schema body of `pass` plus commented examples and
asks nothing about fields. Every real content type then needs the whole schema
hand-written. We hand-wrote `priority` (Choice+vocab), `done` (Bool),
`description` (RichText) for `Todo`.

**Suggestion:** accept a repeatable field spec, ideally via `--data-file` so it
stays non-interactive, e.g.

```yaml
fields:
  - {name: priority, type: choice, vocabulary: "derico.todos.Priorities", default: normal, required: true}
  - {name: done,     type: bool,   default: false}
  - {name: description, type: richtext, required: false}
```

Map `type` → the right import (`schema.Choice`, `schema.Bool`,
`plone.app.textfield.RichText`, `NamedBlobImage`, …) and generate the `import`
lines + field declarations. Even supporting the common scalar types
(text/textline/bool/int/choice/datetime/richtext) would remove the single
biggest manual step. (Cf. the `plone-ct-plan` field-definition format.)

### 2. When `global_allow=false` + a parent, wire the **parent's** allowed types (templates)
`add content_type ... -d global_allow=false -d parent_content_type="Todos"`
correctly sets the child FTI to non-global, but it does **not** add the child to
the parent's `allowed_content_types`. We had to hand-edit `Todos.xml` to add
`<element value="Todo"/>`. The subtemplate already knows
`parent_content_type_resolved` — it should append the child to that parent FTI's
`allowed_content_types` (and set `filter_content_types=true` there), so the
containment relationship actually works after install.

### 3. `restapi_service` `service_for` can't target a package's own type (templates)
`service_for` is a fixed 4-item choice list (`IDexterityContainer`,
`IDexterityContent`, `IPloneSiteRoot`, `Interface`) with no `<enter manually>`.
To register `@todos` on the `Todos` type we had to generate for
`IDexterityContainer` and then hand-edit `configure.zcml` to
`for="derico.todos.content.todos.ITodos"`.

**Suggestion:** mirror the `view` subtemplate — scan the addon's content-type
interfaces (`shared/utils/content_types_scanner`) and append them + an
`<enter manually>` option to `service_for`'s choices.

### 4. i18n is half-wired — finish the wiring (templates)
The package ships a `locales/` skeleton and a `registerTranslations` directive,
but turning that into a working *German* translation took several manual steps
that the template could own:

- **No `MessageFactory`.** `src/<pkg>/__init__.py` is just a docstring. Every
  i18n-aware addon needs `_ = MessageFactory("<domain>")`; scaffold it, and have
  `content_type` / `view` / `vocabulary` import and use it for titles/labels
  instead of bare strings.
- **`.po`/`.pot` aren't generated from code.** `update.sh`/`update.py` rely on a
  system `gettext`/`i18ndude` that may be absent (no `msgfmt` here). Consider a
  pure-Python path (`pythongettext` is already in the dep tree) and/or a
  `plonecli i18n` wrapper task.
- **`registerTranslations` won't compile `.mo`** unless
  `zope_i18n_compile_mo_files` is set (default unset). The generated
  `zope-setup` instance doesn't set it, so a fresh instance silently shows no
  translations. **Suggestion:** add
  `<environment> zope_i18n_compile_mo_files true </environment>` to the dev
  instance's `zope.conf` (at least in debug mode), and set the same env var in
  the generated `tests/conftest.py` so translation tests pass on a fresh
  checkout (where `*.mo` is gitignored).
- **Scaffold at least one non-`en` locale** (or a `plonecli add language <code>`
  subtemplate) so adding German doesn't mean creating
  `de/LC_MESSAGES/<domain>.po` by hand.

---

## Medium impact — papercuts that cost a test run or a workaround

### 5. Generated tests should respect `global_allow=false` (templates)
`test_factory/adding/deleting` always create the type in the portal root, so for
an item addable only inside a parent they fail with
`InvalidParameterError: Disallowed subobject type`. When `global_allow=false`,
the generated test should create a `parent_content_type` container in `_setup`
and add the item there. (Also tracked in `TODO.md`.) Bonus: assert the type
shows up in the parent's `allowedContentTypes()`.

### 6. `create_initial_instance` hook should not depend on a bare `copier` (plonecli/templates)
When plonecli is a `uv tool`, only its own entry point is on PATH; the hook's
`subprocess.run(["copier", ...])` dies with `FileNotFoundError`. We had to
prepend the tool venv's bin to PATH. **Suggestion:** invoke via
`sys.executable -m copier` (same interpreter, guaranteed import), which also
fixes the `copier_template_extensions` import.

### 7. A fresh addon should pass its own `ruff` (templates)
`locales/update.py` trips the project's bundled ruff config (3× `S602`
`shell=True`, 1× `E501`). Either rewrite the `subprocess.call(..., shell=True)`
helpers as list-arg calls, or add `locales/update.py` to
`[tool.ruff.lint.per-file-ignores]` so `ruff check` is green out of the box.

### 8. `plonecli test` should find pytest (plonecli/templates)
`invoke test` runs `uv run pytest`, but pytest lives only in the **`test`**
extra (the `dev` extra has just invoke/watchdog), so it fails with
`Failed to spawn: invoke`/pytest-not-found. Either add the test deps to the
extra the task uses, or make the `test` task run `uv run --extra test pytest`.
Until then the working invocation is `uv run --extra test pytest`.

### 9. Composite `plone_version` is asked once but means two things (templates)
`backend_addon` wants a **minor** (`6.1`) while `zope-setup` wants a **full**
version (`6.1.2`), so a single `-d plone_version=…` can't satisfy both in
`create addon`. Derive the full version from the minor (or vice-versa) inside
the composite so it stays consistent without the user guessing.

---

## Low impact / nice-to-have

### 10. Honor `github_organization` in URLs
We passed `-d github_organization=MrTango`, but the generated `pyproject.toml`
URLs still point at `collective/derico.todos`. Either wire the answer into the
`[project.urls]` block or drop the unused question.

### 11. Make `*.pot` tracked, `*.mo` build-only (templates)
`.gitignore` ignores both `*.pot` and `*.mo`. The `.pot` is the canonical
message catalog source (the `.po` files derive from it) and is normally
committed; only `*.mo` (a build artifact) should be ignored.

### 12. Truthful subtemplate output
The `add` steps print success lines like "Extended configure.zcml with
browser:page 'view'" unconditionally. When a hook actually skips a write
(dedupe, `_skip_if_exists`), say so — silent "success" on a no-op is misleading.

---

## What already works well in b10 (don't regress)
- `create addon` composite runs cleanly non-interactively (`.gitignore`
  overwrite, pyproject/README skip) — the old b9 `git rm .gitignore` dance is
  gone.
- Generated content_type/view tests use the correct `integration` fixture and
  `queryUtility(IDexterityFTI, …)` and pass.
- The `view` hook now registers a second `browser:page` with the same
  `name="view"` but a different `for=` (both Todos and Todo views land).
- Per-subtemplate auto-commit keeps a clean, reviewable history.
