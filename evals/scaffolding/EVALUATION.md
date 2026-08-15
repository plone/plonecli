# Scaffolding evaluation findings

> Historical baseline from before the fixes. A full verification run passed
> 245/245 cases with no warnings on 2026-08-13. The ignored
> `results/report.md` is mutable and may instead contain the latest quick or
> CI-validation run.

## Scope

The full run executed 245 cases against the development templates checkout:

- all 3 project templates;
- all 20 feature templates individually;
- explicit finite high-interaction matrices for backend/Svelte booleans, behavior booleans, REST booleans crossed with target mode, reachable content-type states, view choices/booleans, vocabulary types, all viewlet managers and template states, and Zope distribution/storage choices;
- combined, reversed-order, repeated-application, hostile-input, and command-chain cases;
- harmless root commands and the CLI command unit suite.

Open-ended strings, integers, and environment-discovered choices cannot have a literal exhaustive Cartesian product. They are covered with defaults, non-default valid values, manual-choice paths, and hostile quote/newline/backslash partitions. Finite domains are exhaustive only in the explicitly named high-interaction matrices; other templates receive individual non-default cases plus their focused unit tests.

Result: **237 passed, 8 failed**. See the ignored runtime report at `results/report.md` and per-case logs under `results/logs/`.

## Problems

### High: free text can generate invalid TOML

`backend_addon` and `zope-setup` interpolate title, description, and author values directly into quoted TOML. Quotes, newlines, and backslashes can produce an invalid `pyproject.toml`.

Evidence:

- `hostile-backend-toml-strings`: generation returned success, but TOML validation failed.
- `hostile-zope-toml-strings`: the generated TOML was invalid and the post-copy hook aborted while parsing it.

Use a TOML-safe Jinja filter or generate these values through `tomlkit` instead of interpolating raw strings.

### High: `zope_instance` cannot be added through plonecli

All four `zope_instance` CLI cases failed because `plonecli add` did not list `zope_instance` in a standalone `zope-setup` project. The generated project contains both `[tool.plone.project.settings]` and `[tool.plone.backend_addon.settings]`. Project detection checks backend settings first, classifies the project as `backend_addon`, and exposes the wrong subtemplate set.

Either avoid writing backend-addon settings for standalone Zope projects or make project detection prefer the substantive project settings in this mixed layout.

### High: chained `create` then `setup` fails

The CLI declares `chain=True`, but `chain-create-then-setup` failed after successfully creating the backend add-on. The group retains the project context detected before `create`, so `setup` still reports that it is outside a package.

Refresh project context after creation, or remove command chaining if cross-context chains are not supported.

### Medium: theme variants conflict without non-interactive resolution

The all-feature sequence failed when `theme_barceloneta` followed `theme`: both own `profiles/default/theme.xml` and related theme paths. Copier requested an interactive overwrite despite `--defaults`, then aborted in the non-TTY evaluation.

Treat theme templates as explicit alternatives and reject a second theme with a clear message, or add a documented overwrite/replacement flow.

### Medium: Barceloneta integration test uses a stale path

The root integration suite generated the test at `src/collective/mythemetest/tests/test_theme_my_test_theme.py`, but `tests/test_theme_barceloneta_integration.py` expects it under top-level `tests/`. Result: 23 integration cases passed and 1 failed.

Update the assertion and pytest target to the generated `src/<package>/tests/` layout.

## Optimization opportunities

- Copier template extensions emitted hundreds of deprecation warnings because `ContextHook.update` is deprecated. Migrate hooks to modify context in `hook`.
- `click_aliases` reads deprecated `click.__version__`; update or replace the dependency before Click 9.1.
- Feature generation inside these nested, `--no-git` workspaces reports the outer plonecli repository as dirty. Git cleanliness checks should be scoped to the detected generated project rather than walking into an unrelated parent repository.
- Keep the generated TOML/XML/Python validators as CI checks. They found failures that successful Copier exit codes did not detect.

## Resolution

All findings above have been addressed:

- free-text TOML values use serialization filters;
- standalone Zope projects are detected correctly;
- chained `create` → `setup` refreshes project context;
- theme variants reject conflicting overlays;
- the Barceloneta integration test uses the generated package test path;
- context hooks use the current in-place API;
- the deprecated command-alias dependency was removed;
- Git checks are scoped to the generated project;
- subtemplate validation tasks use Copier's `_copier_operation` value and no
  longer report files generated earlier in the same copy as pre-existing
  changes;
- generated TOML/XML/Python validation runs in CI.

## Baseline test receipts

- Root unit suite: **209 passed, 16 skipped**.
- Copier-template unit suite: **386 passed, 2 integration tests deselected**.
- Copier-template integration suite: **2 passed**.
- Root integration suite: **23 passed, 1 failed** (stale Barceloneta test path above).
- Full scaffolding matrix: **199 passed, 8 failed** (the eight cases map to four product problems above).
