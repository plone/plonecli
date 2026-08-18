# plonecli scaffolding evaluations

This directory contains a reusable, real-CLI evaluation of plonecli commands and
all copier templates in the development checkout. It is intentionally separate
from product and template source.

## Run

From the repository root:

```sh
uv run python evals/scaffolding/run_evals.py --quick
uv run python evals/scaffolding/run_evals.py --ci-validation
uv run python evals/scaffolding/run_evals.py
```

`--quick` runs a reduced smoke subset. `--ci-validation` runs every template
once plus hostile-input and command checks. With no flag, the runner executes
the explicit finite high-interaction matrices described below. It audits the
repository template inventory and fails when a new template has no lane. The runner itself invokes plonecli only as
`uv run --project /workspaces/plonecli plonecli`, so copied generated projects cannot shadow the checkout with their own environment. It sets:

```text
PLONECLI_TEMPLATES_DIR=/workspaces/plonecli/develop/plone/src/copier-templates
```

`run_git_evals.py` is the complement. Because the matrix above passes
`--no-git` everywhere, it never exercises auto-commit — the behaviour users get
by default. This harness runs the same commands with git enabled and asserts,
after each one, that the project is a git repository, that `git status
--porcelain` is empty, and that the expected commit was created:

```sh
uv run python evals/scaffolding/run_git_evals.py --quick
uv run python evals/scaffolding/run_git_evals.py
```

`--quick` runs only the project-level cases (`create` × 3, `skill install
--scope project`, `setup`); the full run adds every subtemplate plus
`zope_instance`. It writes to `workspaces-git/` and `results-git/`, so the two
harnesses never share state.

Generated trees are disposable and always live beneath `workspaces/`. Reports
and per-case command logs are written beneath `results/`:

- `results/report.json` — machine-readable case inventory, commands, coverage,
  validation results, counts, and failures.
- `results/report.md` — human-readable coverage table and problem summary.
- `results/logs/*.log` — captured stdout/stderr for every case.

Both output directories are ignored by git and replaced at the start of a run.

## Coverage

The full run covers:

- harmless root commands: help, template list, versions, and bash/zsh/fish
  completion output;
- real non-default creation of `backend_addon`, `zope-setup`, and the `addon`
  composite, plus a real standalone `setup` application;
- every currently shipped backend subtemplate individually against a copied
  clean parent, plus `zope_instance` against a copied Zope parent;
- both backend headless states and both Svelte custom-element states;
- the complete behavior boolean matrix (4 cases);
- all REST boolean states crossed with normal/manual registration targets
  (64 cases);
- all reachable content-type gated boolean/choice states;
- every view base class × template × marker × normal/manual target state;
- both vocabulary implementation choices;
- all 26 viewlet managers with both template values (52 cases);
- both Zope distributions × all three storage modes, and all three
  `zope_instance` storage modes;
- one all-backend-subtemplates project, reversed-order pairs, and representative
  repeated-application/idempotency cases;
- TOML-hostile quote/newline/backslash partitions and a real chained
  `create` → `setup` command.

Names are unique per isolated project to make collisions deterministic. The
report records the full planned and actually executed counts by category, and
each matrix case records its parameter values.

## Validation and safety

Every generated project receives deterministic syntax and duplicate-registration
checks without installing Plone. The template unit suite supplies
feature-specific semantic assertions:

- every TOML file is parsed with `tomllib`;
- every XML and ZCML file is parsed;
- every Python file is compiled;
- exact duplicate direct-child XML registrations are reported where practical;
- every subprocess exit code is checked;
- stdin is disabled and every command has a configurable timeout.

The harness does **not** run `serve` or `debug`, and does not run a generated
project's `test` task because those branches can start services or resolve a
full Plone environment. Instead it runs the repository's root CLI command unit
test suite, which covers `serve`, `debug`, and `test` dispatch and error paths
with mocked subprocesses. Template hooks may still ask native `uv` to resolve
small hook-only tools (`tomlkit`, Copier extensions); use a warmed uv cache for
the most network-independent run.

## Reading failures

A nonzero runner exit means at least one case failed or was blocked. Start with
`results/report.md`, then inspect the referenced log. Failures are retained as
evaluation findings rather than hidden or retried with defaults. Reports include
repository commits, dirty state, Python, and uv provenance.
