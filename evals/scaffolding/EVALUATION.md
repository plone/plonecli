# Scaffolding evaluation findings

Run on 2026-08-15 against plonecli `7.0.0b16.dev0` (`c8ebe13`) and
copier-templates `2705bf3`. The ignored `results/` and `results-git/` trees hold
the runtime reports; they are replaced on every run and may contain a later
quick or CI-validation run instead.

The three Medium problems were fixed in plonecli after the run; each carries its
fix and its regression test below. The three Low problems live in
copier-templates and are still open.

## Scope

Two harnesses were executed.

`run_evals.py` (full mode, 245 cases) covers:

- all 3 project templates;
- all 20 feature templates individually;
- explicit finite high-interaction matrices for backend/Svelte booleans,
  behavior booleans, REST booleans crossed with target mode, reachable
  content-type states, view choices/booleans, vocabulary types, all viewlet
  managers and template states, and Zope distribution/storage choices;
- combined, reversed-order, repeated-application, hostile-input, and
  command-chain cases;
- harmless root commands and the CLI command unit suite.

`run_git_evals.py` (25 cases, new in this round) covers the auto-commit path
that `run_evals.py` deliberately disables — see "Auto-commit verification".

Open-ended strings, integers, and environment-discovered choices cannot have a
literal exhaustive Cartesian product. They are covered with defaults,
non-default valid values, manual-choice paths, and hostile
quote/newline/backslash partitions. Finite domains are exhaustive only in the
explicitly named high-interaction matrices; other templates receive individual
non-default cases plus their focused unit tests.

## Result

**245 passed, 0 failed** in the scaffolding matrix (1050s), and **25 passed, 0
failed** in the auto-commit harness (40s).

Every problem in the previous round is fixed and stayed fixed: free-text TOML
values serialize safely, standalone Zope projects are detected as such,
`create` → `setup` chains refresh the project context, conflicting theme
overlays are rejected, and the Barceloneta integration test targets the
generated package path. The copier-template suite now emits **zero** warnings,
so the deprecated `ContextHook.update` and `click.__version__` opportunities are
also closed.

## Auto-commit verification

`plonecli` promises that every generated or modified file is committed, so a
package always has reviewable history. `run_evals.py` cannot check that: it
passes `--no-git` on every case to keep generated trees disposable, which left
the default user-facing path with no coverage at all.

`run_git_evals.py` closes that gap. It runs the same commands with git enabled
and, after each one, asserts the project is a git repository, that
`git status --porcelain` is empty, and that the run produced the expected new
commit.

| Command | Cases | Result |
|---|---|---|
| `create backend_addon` / `zope-setup` / `addon` | 3 | clean tree, one commit per template step |
| `skill install --scope project` | 1 | clean tree, `Add plonecli skills` |
| `setup` | 1 | clean tree, `Add zope-setup template` |
| `add <subtemplate>` (all 19) + `add zope_instance` | 20 | clean tree, `Add <name> subtemplate` |

`serve`, `debug`, and `test` delegate to invoke and write only into gitignored
paths (`runtime/*/var/`, `.pytest_cache/`, `.coverage`); they are not expected
to commit and are covered by the root CLI command unit suite. `config`,
`update` and `completion` do not touch a project tree.

Two commands did **not** hold the contract — both are fixed, see problems 1 and
2 below.

## Problems

### Fixed, was Medium: `plonecli setup` ignored `auto_commit = false` and had no `--no-git`

`cli.py` called `run_create()` without a `git_commit` argument, and
`templates.py:139` defaults it to `True`. `create` and `add` both compute
`config.auto_commit and not no_git`; `setup` computed nothing and always
committed. It was also the only file-writing command with no `--no-git` flag,
and it discarded `run_create`'s return value, so it never printed the
`Committed: ...` line the other two print.

Evidence: with `auto_commit = false` in `~/.plonecli/config.toml`, `create`
correctly produced a package with no repository, and the following `setup` ran
`git init` and committed it anyway — as `Create package with zope-setup
template`, for a package it did not create.

**Fixed.** `setup` now passes `git_commit=config.auto_commit and not no_git`,
accepts `--no-git`, carries a chained `--no-git` across `create ... setup`, and
echoes the returned commit message. Re-verified end to end: with
`auto_commit = false` the package still has no repository after `setup`; with
the default it commits `Add zope-setup template` and leaves a clean tree.
Covered by `tests/test_setup_command.py` and `tests/test_plonecli.py`.

### Fixed, was Medium: `plonecli skill install --scope project` left the repo dirty

The installer writes `.agents/skills/<name>` and `.claude/skills/<name>` into
the project root and never committed. Neither path is in the generated
`.gitignore`, so the working tree was left with two untracked directories.

That broke the next command: `plonecli add <sub> --defaults` aborted with
"Refusing to run on a git repository with uncommitted changes", so plonecli's
own command put a project into a state plonecli refuses to work in.

**Fixed.** A project-scope `install`/`update` now commits the installed skills
under the same `auto_commit` contract, as `Add plonecli skills` /
`Update plonecli skills`, with `--no-git` to opt out. It uses the new
`git.commit_paths()`, which commits only the skill directories: it never runs
`git init` and never sweeps unrelated user changes into the commit. User-scope
installs are untouched. Covered by `tests/test_skill.py` and
`tests/test_git.py`.

### Fixed, was Medium: the root integration suite silently skipped 23 of its 24 cases

`_templates_dir()` in `tests/test_theme_barceloneta_integration.py` and
`tests/test_all_templates_data.py` resolved the template checkout from
`PLONECLI_TEMPLATES_DIR` or two hard-coded `/home/node/...` paths. This
repository keeps its development checkout at `develop/plone/src/copier-templates`
(per `AGENTS.md`), which is neither.

So a plain `uv run pytest -m integration` reported "1 passed, 2 skipped" —
green, and almost entirely empty, because the parametrized template sweep
collapsed to an empty parameter set.

**Fixed.** All three integration modules now share
`tests/helpers.find_templates_checkout()`, which tries `PLONECLI_TEMPLATES_DIR`,
the repo-relative `develop/plone/src/copier-templates`, the configured
`PlonecliConfig().templates_dir`, then the devcontainer paths. A plain
`uv run pytest -m integration --collect-only` now collects 24 cases with no
environment variable set. Covered by `tests/test_templates_checkout.py`, whose
last test asserts the sweep is populated whenever a checkout exists — the
regression itself.

### Low: the template git warning prints a mangled filename

`shared/hooks/git_check.py` calls `.strip()` on the whole `git status
--porcelain` output before splitting it into lines. Porcelain lines are
`XY<space><path>`, so stripping removes the leading status space of the *first*
line and shifts every subsequent slice by one: ` M .gitignore` is reported as
`gitignore`.

Observed in the clean-tree `setup` run:

```text
Modified files:
  - gitignore
```

Split with `splitlines()` on the unstripped output. `plonecli/git.py` already
does this correctly; only the template hook is affected.

### Low: the git warning fires on changes plonecli itself just made

The same warning appears during `setup` and `add zope_instance` even when the
tree was clean before the command, because `zope-setup` invokes the
`zope_instance` template from a post-copy hook after the current copy has
already written files. The user is told to commit or stash changes that
plonecli made moments earlier and is about to commit itself.

Scope the check to the state before the copy operation, or suppress it for
nested template invocations.

### Low: `plonecli setup` replaces the backend addon's `.gitignore` wholesale

`backend_addon` and `zope-setup` each ship a full `.gitignore.jinja`, and
`setup` overwrites the first with the second. Today the loss is only
`Thumbs.db` — `dist/` and `.cache` are still matched by the remaining bare
patterns, verified with `git check-ignore` — so there is no functional impact.
But the two files are independently maintained copies, so any backend-only
ignore rule added later disappears on `setup` without a signal.

Share one base fragment between the two templates, or append instead of
overwrite.

## Optimization opportunities

- CI runs only `run_evals.py --ci-validation`. Add `run_git_evals.py --quick`
  so the auto-commit contract cannot regress unnoticed. The integration suite no
  longer needs `PLONECLI_TEMPLATES_DIR` to find the checkout, but setting it in
  CI still pins which checkout is used.
- The five `WARNING: Git repository has uncommitted changes!` entries in the
  matrix report are the two Low findings above, not template failures; fixing
  them removes the noise from the report's warning section.
- Keep the generated TOML/XML/Python validators as CI checks. They caught
  failures in the previous round that successful Copier exit codes did not.

## Test receipts

- Root unit suite: **280 passed, 12 skipped** (the skips are the model-billing
  skill evals; 216 passed / 1 skipped before the third fix, which restored the
  template sweep and added the new tests).
- Root integration suite: **24 collected and passed**, with or without
  `PLONECLI_TEMPLATES_DIR`.
- Copier-template unit suite: **391 passed**, 2 integration tests deselected,
  **0 warnings**.
- Copier-template integration suite: **2 passed**.
- Full scaffolding matrix: **245 passed, 0 failed**.
- Auto-commit harness: **25 passed, 0 failed**.
