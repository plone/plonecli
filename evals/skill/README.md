# plonecli skill evals

Behavioral evals for the Agent Skills bundled under `plonecli/skills/`
(`plonecli` and `plone-schema-fields`).
They measure whether an agent, given a realistic task, follows the process the
skill prescribes — scaffold with plonecli instead of hand-writing, run
non-interactively (`--defaults` + `-d`), add upgrade steps after profile-XML
changes, never start the dev server, adapt legacy packages minimally.

## How it works

- Each case copies a fixture project into a sandbox and runs headless Claude
  Code (`claude -p --dangerously-skip-permissions`) with a task prompt.
- A shim `plonecli` (and `uv run invoke`) sits first on `PATH`: it logs every
  invocation to a command log and fakes plausible output/files. No real
  scaffolding, network or Plone install — runs take 1–3 minutes each.
- Grading is mechanical: regexes over the command log, fixture files and the
  transcript. See the `checks` per case in `run_evals.py`.
- `--mode both` runs every case with the skill installed (project scope) and
  without it, to measure what the skill actually changes. Runs use an isolated
  `CLAUDE_CONFIG_DIR` (credentials only), so user-scope skills and the global
  CLAUDE.md never leak in. `--skill-src <dir>` installs a different skill
  checkout — use it to A/B an edited skill against the shipped one.

## Usage

As pytest (skill mode; gated so the normal suite never bills — the tests skip
unless `RUN_SKILL_EVALS=1` is set and the `claude` CLI is installed):

```shell
RUN_SKILL_EVALS=1 uv run --extra test pytest -m evals -v
RUN_SKILL_EVALS=1 SKILL_EVAL_MODEL=haiku uv run --extra test pytest -m evals -k fields
```

Or via the CLI runner (needed for skill-vs-baseline comparisons):

```shell
python evals/skill/run_evals.py --list                 # show cases
python evals/skill/run_evals.py --mode skill           # all cases, skill on
python evals/skill/run_evals.py --mode both --cases restapi-implicit,upgrade-step
python evals/skill/run_evals.py --model haiku          # cheaper smoke run
```

Requires the `claude` CLI logged in. Runs bill real model usage — a full
`--mode both` sweep is ~16 agent runs. Sandboxes and transcripts land in
`<tmpdir>/plonecli-skill-evals/<timestamp>/` (outside the repo on purpose:
a sandbox inside this repo lets the baseline agent *find* the skill by
searching the project); `results.json` there summarizes. Each run prints
`skills fired: [...]` — in `noskill` mode it must be `none`, anything else
means a skill leaked into the baseline.

## Cases

| Case | Verifies |
|---|---|
| `create-addon` | New add-ons are scaffolded via `plonecli create`, non-interactively |
| `add-behavior` | Features go through `plonecli add <subtemplate> --defaults -d ...` |
| `add-contenttype` | Content types go through the subtemplate |
| `add-vocabulary` | Vocabularies go through the subtemplate |
| `add-view` | Browser views go through the subtemplate |
| `restapi-implicit` | The skill *triggers* when the prompt never says "plonecli" |
| `fields-manual` | Fields are hand-edited into the schema (`plone-schema-fields` skill) |
| `upgrade-step` | Profile-XML edits for installed sites get `plonecli add upgrade_step` |
| `no-serve` | The agent never starts the dev server itself |
| `legacy-adapt` | Legacy packages get minimal adaptation, not re-scaffolding |
| `reconfigure` | Settings changes use `invoke reconfigure`, not `create` |

## Caveats

- Headless runs can't answer `AskUserQuestion` — prompts are written to be
  self-sufficient, so a run that stalls on a question shows up as a FAIL.
- The shim approximates plonecli's behavior (including `NotInPackageError`
  outside a plonecli project and failing without `--defaults` on no TTY). If
  real plonecli semantics change, update the shim.
