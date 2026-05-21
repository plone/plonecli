# Record plonecli screencasts — instructions for the demo driver

Three short, focused screencasts — one per template category — instead of one
long monolithic video. Each video is **a one-shot scripted sequence**: the tape
driver types every command *and* answers every copier prompt (Enter, arrow
keys, y/n, typed strings). Nothing waits for a human to confirm anything, but
the visual experience is fully interactive: the viewer sees copier's prompts
render, the cursor move in choice lists, and answers get entered at reading
speed.

## Pacing

- **Between plonecli commands:** `Sleep 5s`. This is the only idle gap — gives
  the viewer time to read the finished output before the next headline.
- **Inside a copier prompt sequence:** ~1.5 s between keypresses. Fast enough
  to keep the video moving, slow enough that a viewer can read each prompt
  and see the answer land.
- **After sending a command (`Enter`) and before the first prompt answer:**
  `Sleep 2s` so the first copier prompt has time to render before we start
  driving it.
- **Typing speed:** ~80 ms/char.

## Tooling & setup (all three videos)

- Recorder: [`vhs`](https://github.com/charmbracelet/vhs) tape file.
- Terminal: 120 × 36, dark theme, JetBrains Mono 16 pt.
- Shell: `bash` with plonecli completion active:
  `eval "$(_PLONECLI_COMPLETE=bash_source plonecli)"`
- Scratch cwd: `/tmp/plonecli-demo` (each tape wipes its own addon dir).
- Headline banner between each step:

  ```bash
  echo -e "\n\033[1;46m ▶ STEP $N — $DESCRIPTION \033[0m\n"; sleep 2
  ```

- For every `create` / `add`: type a **partial token**, press `<Tab>` (or
  `<Tab><Tab>` to list), pause ~1 s, then continue.

## Template categories

### Backend (8) — pure server-side building blocks

`behavior`, `content_type` (shown twice — see scenario below), `controlpanel`,
`indexer`, `site_initialization`, `subscriber`, `upgrade_step`, `vocabulary`

### REST API (2) — headless API + a frontend that consumes it

`restapi_service`, `svelte_app`

### Classic UI (8) — views, themes, portlets, forms

`form`, `mockup_pattern`, `portlet`, `theme`, `theme_barceloneta`,
`theme_basic`, `view`, `viewlet`

## Video matrix

| # | Video        | Addon package                | `zope-setup` storage          |
|---|--------------|------------------------------|-------------------------------|
| 1 | Backend      | `collective.backenddemo`     | FileStorage (`instance`)      |
| 2 | REST API     | `collective.restapidemo`     | ZEO                           |
| 3 | Classic UI   | `collective.classicuidemo`   | RelStorage (PostgreSQL)       |

## Common intro (every video)

1. `plonecli -V`
2. `plonecli -l`
3. `plonecli --help`
4. `plonecli <Tab><Tab>` — list top-level commands, abort with `<Ctrl-C>`
5. `plonecli create <Tab><Tab>` — list main templates, then `add<Tab>`
   completes to `addon`, abort with `<Ctrl-C>`
6. `plonecli create addon <package>` — create the video's addon
   (answer the ~8 `backend_addon` prompts with defaults)

## Common outro (every video)

- `ls -la`
- `ls .copier-answers*.yml`
- `ls src var`
- Closing banner naming the category and the storage backend used.

## Content-type scenario (Backend video only)

`content_type` is demonstrated **twice in a row** to showcase copier's
choice UI and the interplay between `content_type_base`, `global_allow`
and `parent_content_type`.

### First `plonecli add content_type` — a Container, globally addable

Answers:

| Prompt                         | UI kind     | Answer                      |
|--------------------------------|-------------|-----------------------------|
| `content_type_name`            | text        | `Project`                   |
| `content_type_description`     | text        | `A project folder`          |
| `content_type_base`            | **choice**  | **`Container`** (default — demonstrate arrow-key navigation even when accepting default: `Up` / `Down` / `Up` / `Enter`) |
| `content_type_icon`            | text        | `folder`                    |
| `global_allow`                 | **bool**    | **`yes`** (default)         |
| `filter_content_types`         | bool        | `yes`                       |
| `activate_default_behaviors`   | bool        | `yes`                       |
| `enable_dublin_core`           | bool        | `yes`                       |
| `enable_navigation`            | bool        | `yes`                       |

Note: `parent_content_type` is **skipped** here (it's gated on
`global_allow == false`).

### Second `plonecli add content_type` — an Item, not globally addable, parented on the first CT

Answers:

| Prompt                         | UI kind     | Answer                                                     |
|--------------------------------|-------------|------------------------------------------------------------|
| `content_type_name`            | text        | `Task`                                                     |
| `content_type_description`     | text        | `A task inside a Project`                                  |
| `content_type_base`            | **choice**  | **`Item`** (arrow `Down` then `Enter`)                     |
| `content_type_icon`            | text        | `check2-square`                                            |
| `global_allow`                 | **bool**    | **`no`** — opposite of the first CT                        |
| `parent_content_type`          | **choice**  | **`Project`** — the CT we just created must appear in the list; navigate to it and `Enter` |
| `activate_default_behaviors`   | bool        | `yes`                                                      |
| `enable_dublin_core`           | bool        | `yes`                                                      |
| `enable_navigation`            | bool        | `no` — demonstrate a `n`/`Enter` answer                    |

This second run is what the user explicitly asked to see: **Item vs Container,
both `globally_addable` values, and picking the parent CT from copier's choice
list.**

## Copier UI widgets demonstrated

- **Text input** — almost every prompt.
- **Choice (single-select)** — copier renders with arrow navigation:
  - `content_type_base` (Container / Item) — shown twice, different answers
  - `parent_content_type` (Folder / Document / … / Project) — shown once
  - `plone_version` — shown during every `create addon` and `setup`
  - `distribution` (plone.volto / plone.classicui) — shown during `setup`
  - `db_storage` (instance / zeo / relstorage) — shown during `setup`,
    answered differently per video
- **Bool (yes/no)** — many prompts. Demonstrate both `yes` and `no` answers
  across the content_type scenario and `enable_navigation`.

**Multi-select / multichoice is *not* available** in the current
`copier-templates` — none of the 20 template `copier.yml` files define a
`multiselect: true` question. If showing copier's multichoice widget is a
must-have, we need to add such a prompt to a template first (e.g., a
`behaviors:` multi-select on `content_type`); otherwise, drop that goal from
the script.

## Video 1 — Backend (FileStorage)

Steps:

1. Common intro → create `collective.backenddemo`.
2. `cd collective.backenddemo`
3. `plonecli add behavior` (defaults)
4. `plonecli add content_type` — **Container scenario** above
5. `plonecli add content_type` — **Item + parent scenario** above
6. `plonecli add controlpanel` (defaults)
7. `plonecli add indexer` (defaults)
8. `plonecli add site_initialization` (defaults)
9. `plonecli add subscriber` (defaults)
10. `plonecli add upgrade_step` (defaults)
11. `plonecli add vocabulary` (defaults)
12. `plonecli setup` — choose **`instance`** at `db_storage`, defaults for the rest.
13. Common outro.

## Video 2 — REST API (ZEO)

Steps:

1. Common intro → create `collective.restapidemo`.
2. `cd collective.restapidemo`
3. `plonecli add restapi_service` (defaults — many prompts, shows the
    service name / route / view class questions).
4. `plonecli add svelte_app` (defaults — demonstrate a front-end that will
    consume the REST API).
5. `plonecli setup` — choose **`zeo`** at `db_storage`, accept
   `zeo_address=localhost:8100`, defaults elsewhere.
6. Common outro.

## Video 3 — Classic UI (RelStorage / PostgreSQL)

Steps:

1. Common intro → create `collective.classicuidemo`.
2. `cd collective.classicuidemo`
3. `plonecli add form` (defaults)
4. `plonecli add mockup_pattern` (defaults)
5. `plonecli add portlet` (defaults)
6. `plonecli add theme` (defaults)
7. `plonecli add theme_barceloneta` (defaults)
8. `plonecli add theme_basic` (defaults)
9. `plonecli add view` (defaults)
10. `plonecli add viewlet` (defaults)
11. `plonecli setup` — choose **`relstorage`** at `db_storage`, answer
    PostgreSQL prompts (`pg_host=localhost`, `pg_port=5432`,
    `pg_dbname=plone_classicuidemo`, `pg_user=plone`, `pg_password=secret`).
12. Common outro.

## Prompt counts (for sizing Enter sequences)

Visible prompts per template (measured from the current copier-templates —
re-check with `awk` on `copier.yml` if templates change):

| Template              | Visible prompts |
|-----------------------|-----------------|
| backend_addon         | 8               |
| behavior              | 7               |
| content_type          | 14 (fewer shown at runtime because of conditional `when:` gates — Container run skips `parent_content_type*`, Item run skips `filter_content_types`) |
| controlpanel          | 6               |
| indexer               | 5               |
| site_initialization   | 5               |
| subscriber            | 7               |
| upgrade_step          | 7               |
| vocabulary            | 6               |
| restapi_service       | 11              |
| svelte_app            | 6               |
| form                  | 7               |
| mockup_pattern        | 5               |
| portlet               | 5               |
| theme                 | 5               |
| theme_barceloneta     | 5               |
| theme_basic           | 5               |
| view                  | 11              |
| viewlet               | 9               |
| zope-setup            | up to 18 (conditional on `db_storage`; FileStorage ≈ 10, ZEO ≈ 11, RelStorage ≈ 15) |

Use these as the baseline for how many answer keystrokes each command block
sends. Plus one or two buffer Enters — extra Enters at a shell prompt are
harmless newlines.

## Failure policy

If any step errors, **stop recording** and surface the error. Do not paper
over failures with retries — the viewer must see only successful output.
