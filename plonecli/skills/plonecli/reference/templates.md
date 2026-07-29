# Template questions — what `-d KEY=VALUE` answers each template accepts

This is the authoritative catalogue of every copier-template question, so you can build the
non-interactive `--defaults -d KEY=VALUE …` invocation **without** triggering a prompt and
**without** guessing. It is derived from the templates' `copier.yml`. The live source of truth is
still the templates clone (`~/.copier-templates/plone-copier-templates/<template>/copier.yml`); run
`plonecli -l` to see which templates/subtemplates apply where.

## How to read these tables

- **Required** (shown as `**required**` in the Default column) = the question has a validator and
  **no usable default** → you **must** pass it with `-d`, or copier still prompts (and hangs in
  Claude Code / CI). Only four keys are truly required: `behavior_name`, `content_type_name`,
  `service_name`, `upgrade_step_title`.
- **name†** = the subtemplate's primary identifier. It *has* the default shown (so `--defaults`
  won't prompt), but that default is a generic placeholder (`my-view`, `Weather`, …) — you'll almost
  always set it via `-d` to a real name. Its validator only rejects an empty value.
- **Default** = used when you omit the key under `--defaults`. Pass `-d KEY=VALUE` only to change it.
- **Choices** = the only accepted values (copier rejects others).
- **Conditional (`when`)** = the question only appears when another answer has a given value. To set
  it you must also set the controlling answer (e.g. `parent_content_type` needs `global_allow=false`).
- **Computed / hidden** keys (PascalCase→snake_case module names, interfaces, etc.) are derived
  automatically — **do not pass them**; they are listed only so you understand what gets generated.
- Booleans: pass `-d key=true` / `-d key=false`.

Golden rule: pass `--defaults` plus a `-d` for **every** answer the user actually specified, **plus**
every Required key. Don't invent values the user hasn't given — ask, then pass them via `-d`.

---

## Create templates (project-level — `plonecli create <template> <name>`)

### `backend_addon` — Plone backend add-on package

The `<name>` positional becomes the default `package_name`, so `package_name` is effectively
satisfied; everything else has a default.

| Key | Default | Choices / notes |
|---|---|---|
| `package_name` | the project dir name (or legacy package name) | Python package, e.g. `collective.todo`. |
| `package_title` | derived from `package_name` | Human-readable title. |
| `package_description` | "A Plone addon package" | |
| `plone_version` | newest supported minor | choices: the supported Plone minor versions (`PloneVersionsHook`). |
| `is_headless` | `false` | bool — headless/API-only addon. |
| `author_name` | "Plone Developer" | |
| `author_email` | "dev@plone.org" | |

Hidden/computed: `package_folder`, `namespace_parts`, `package_module`, `browser_layer_name`,
`current_year`, `current_date`.

### `zope-setup` (alias `project`) — runnable Plone/Zope project

When applied standalone, asks project identity; when applied **on top of an addon** (`addon`
composite or `plonecli setup`), identity + `base_path`/`db_storage` are read from the addon context
and those questions are skipped (`when: not addon_context`).

| Key | Default | Choices / notes |
|---|---|---|
| `project_name` | from addon context, else **required** | only asked when not run on an addon. |
| `project_title` | derived | only when not on an addon. |
| `project_description` | "A Plone project" | only when not on an addon. |
| `plone_version` | newest full version | choices: supported full Plone versions. |
| `distribution` | `plone.volto` | choices: `plone.volto`, `plone.classicui`. |
| `base_path` | `var` | runtime dir; only when not on an addon. |
| `db_storage` | `instance` | choices: `instance`, `relstorage`, `zeo`; only when not on an addon. |
| `zeo_address` | `localhost:8100` | only when `db_storage=zeo`. |
| `pg_host` | `localhost` | only when `db_storage=relstorage`. |
| `pg_port` | `5432` | only when `db_storage=relstorage`. |
| `pg_dbname` | `plone_<project_name>` | only when `db_storage=relstorage`. |
| `pg_user` | `plone` | only when `db_storage=relstorage`. |
| `pg_password` | "" (secret) | only when `db_storage=relstorage`. |
| `author_name` | "Plone Developer" | |
| `author_email` | "dev@plone.org" | |
| `initial_zope_username` | `admin` | |
| `initial_user_password` | `admin` (secret) | |

### `addon` (alias `add-on`) — composite

No own questions: it applies `backend_addon` then `zope-setup` in sequence. Pass the `-d` keys for
both layers in one `create addon` call. Do **not** also run `plonecli setup` afterward.

---

## `backend_addon` subtemplates (`plonecli add <sub>` inside an addon)

Every subtemplate also reads `package_name` / `package_folder` from the parent addon — you normally
don't pass those.

### `behavior` — Dexterity behavior

| Key | Default | Notes |
|---|---|---|
| `behavior_name` | **required** | interface name, e.g. `IFeatured`, `ITaggable`. A leading `I` is added if missing. |
| `behavior_description` | "A custom Dexterity behavior" | |

Hidden/computed: `behavior_interface`, `behavior_module`, `behavior_class`. `behavior_marker` /
`behavior_factory` exist but are `when: false` (both default `true`); override only via
`-d behavior_marker=false` etc. if you really need to.

Example: `plonecli add behavior --defaults -d behavior_name="IFeatured"`

### `content_type` — Dexterity content type

| Key | Default | Choices / notes |
|---|---|---|
| `content_type_name` | **required** | e.g. `Talk`, `News Item`. |
| `content_type_description` | "A custom content type" | |
| `content_type_base` | `Container` | choices: `Container`, `Item`. |
| `content_type_icon` | `puzzle` | Bootstrap icon name (e.g. `file-earmark`, `folder`, `newspaper`). |
| `global_allow` | `true` | bool — globally addable? |
| `parent_content_type` | `Folder` | choices come from the addon's known portal types plus `<enter manually>`; only when `global_allow=false`. |
| `parent_content_type_manual` | "" | only when `global_allow=false` **and** `parent_content_type=<enter manually>`. |
| `filter_content_types` | `true` | only when `content_type_base=Container`. |
| `activate_default_behaviors` | `true` | enable the full standard Plone behaviors bundle (see below). |
| `enable_dublin_core` | `true` | only asked when `activate_default_behaviors=false`; adds `plone.dublincore`. |
| `enable_navigation` | `true` | only asked when `activate_default_behaviors=false`; adds `plone.excludefromnavigation`. |

**Which behaviors get enabled.** The FTI's `behaviors` list depends on `activate_default_behaviors`:

- **`activate_default_behaviors=true` (default) — full bundle:** `plone.basic`, `plone.namefromtitle`, `plone.allowdiscussion`, `plone.excludefromnavigation`, `plone.shortname`, `plone.dublincore`, `plone.ownership`, `plone.publication`, `plone.categorization`, `plone.locking`, `plone.textindexer`, `plone.relateditems`, `plone.versioning`. When `content_type_base=Container`, also: `plone.constraintypes`, `plone.nextprevioustoggle`, `plone.nextpreviousenabled`, `plone.navigationroot`. (`enable_dublin_core`/`enable_navigation` are not asked in this case — those behaviors are already in the bundle.)
- **`activate_default_behaviors=false` — minimal set:** `plone.namefromtitle` is **always** enabled (no way to opt out — a content type needs it to derive its id/title). On top of that, `plone.dublincore` is added when `enable_dublin_core=true` (default) and `plone.excludefromnavigation` when `enable_navigation=true` (default). Set both to `false` to get the bare minimum of just `plone.namefromtitle`.

So even with all behavior toggles off, every content type ends up with at least `plone.namefromtitle`. That behavior provides the required `title` field **and** derives the object id from it (`plone.basic`/`plone.dublincore` also supply a title when enabled), so the bare-minimum type still has a working title.

Hidden/computed: `content_type_class`, `content_type_module`, `content_type_interface`,
`content_type_portal_type`, `parent_content_type_resolved`.

**Containment is fully wired by the template — do not edit the parent FTI yourself.** When you
pass `global_allow=false` + `parent_content_type`, the post-copy hook adds the new type to that
parent's `allowed_content_types`: it edits the parent FTI's `types/*.xml` if the parent lives in
this package, or creates a minimal `purge="False"` FTI override (e.g. for stock Plone `Folder`) that
only appends the new type. So just answer `parent_content_type` (and `parent_content_type_manual`
for a type not in the choices) — never hand-edit allowed types in any `types/*.xml` before or after.

Example (containment): `plonecli add content_type --defaults -d content_type_name="Talk" -d global_allow=false -d parent_content_type="Folder"`

### `restapi_service` — `plone.restapi` endpoint

| Key | Default | Choices / notes |
|---|---|---|
| `service_name` | **required** | endpoint name, e.g. `stats`, `my-endpoint`. |
| `service_description` | "A custom REST API endpoint" | |
| `expandable` | `false` | add `IExpandableElement` adapter (extends `@search` etc.). |
| `http_get` | `true` | |
| `http_post` | `false` | |
| `http_patch` | `false` | |
| `http_delete` | `false` | |
| `service_for` | `plone.dexterity.interfaces.IDexterityContainer` | choices: `…IDexterityContainer`, `…IDexterityContent`, `Products.CMFPlone.interfaces.IPloneSiteRoot`, `zope.interface.Interface`. |

Hidden/computed: `service_module`, `service_class`, `service_endpoint`.

### `view` — BrowserView (optional page template)

| Key | Default | Choices / notes |
|---|---|---|
| `view_name` | `my-view` (name†) | URL id, used as `@@my-view`. |
| `view_class_name` | `MyView` | PascalCase Python class. |
| `view_base_class` | `BrowserView` | choices: `BrowserView`, `DefaultView`, `CollectionView`. |
| `view_template` | `true` | also generate a `.pt`? |
| `view_for` | `*` | choices: addon content-type interfaces + `*` + `<enter manually>`. |
| `view_for_manual` | `*` | only asked when `view_for=<enter manually>`; must be non-empty. |
| `view_marker` | `false` | generate a marker interface? |
| `view_description` | "A custom browser view" | |

Hidden/computed: `view_for_interface`, `view_module`.

### `viewlet` — `browser:viewlet`

| Key | Default | Choices / notes |
|---|---|---|
| `viewlet_name` | `myviewlet` (name†) | lowercase identifier. |
| `viewlet_class_name` | `MyViewlet` | PascalCase. |
| `viewlet_manager` | `plone.portalheader` | choices: the standard Plone viewlet managers (`plone.htmlhead`, `plone.portaltop`, `plone.portalheader`, `plone.portalfooter`, `plone.abovecontent`, `plone.belowcontent`, `plone.portalleftcolumn`, `plone.portalrightcolumn`, … — see `copier.yml` for the full list). |
| `viewlet_for` | `*` | interface or `*`. |
| `viewlet_template` | `true` | also generate a `.pt`? |
| `viewlet_description` | "A custom viewlet" | |

Hidden/computed: `viewlet_module`.

### `portlet` — classic Plone portlet

| Key | Default | Notes |
|---|---|---|
| `portlet_name` | `Weather` (name†) | PascalCase display name. |
| `portlet_description` | "A custom portlet" | |

Hidden/computed: `portlet_module`.

### `vocabulary` — named vocabulary (`IVocabularyFactory`)

| Key | Default | Choices / notes |
|---|---|---|
| `vocabulary_name` | `AvailableThings` (name†) | PascalCase class name. |
| `vocabulary_description` | "A custom named vocabulary" | |
| `vocabulary_type` | `simple` | choices: `simple` (SimpleTerm list), `catalog` (StaticCatalogVocabulary). |

Hidden/computed: `vocabulary_class`, `vocabulary_module`.

### `indexer` — catalog indexer (`@indexer`)

| Key | Default | Notes |
|---|---|---|
| `indexer_name` | `my_custom_index` (name†) | snake_case Python identifier. |
| `indexer_description` | "A custom catalog indexer" | |

### `subscriber` — zope event subscriber

| Key | Default | Notes |
|---|---|---|
| `subscriber_handler_name` | `obj_modified_do_something` (name†) | snake_case handler/module name. |
| `subscriber_event` | `zope.lifecycleevent.interfaces.IObjectModifiedEvent` | dotted event interface. |
| `subscriber_for` | `plone.dexterity.interfaces.IDexterityContent` | dotted context interface. |
| `subscriber_description` | "A custom event subscriber" | |

### `controlpanel` — registry-backed settings form

| Key | Default | Notes |
|---|---|---|
| `controlpanel_name` | `MyFeatured` (name†) | PascalCase base name. |
| `controlpanel_title` | = `controlpanel_name` | shown in Plone's control-panel list. |
| `controlpanel_description` | "A custom control panel" | |

Hidden/computed: `controlpanel_module`, `controlpanel_url_id`.

### `form` — `z3c.form`-based form

| Key | Default | Notes |
|---|---|---|
| `form_name` | `my-form` (name†) | URL id, invoked as `@@my-form`. |
| `form_class_name` | `MyForm` | PascalCase. |
| `form_for` | `*` | interface or `*`. |
| `form_description` | "A custom form" | |

Hidden/computed: `form_module`.

### `upgrade_step` — GenericSetup upgrade step

| Key | Default | Notes |
|---|---|---|
| `upgrade_step_title` | **required** | e.g. "Add catalog index". |
| `upgrade_step_description` | "A custom upgrade step" | |
| `source_version` | current `metadata.xml` version (injected) | upgrade **from**. |
| `destination_version` | `source + 1` | upgrade **to**. |

See [add.md](add.md) for the full upgrade-step workflow (fill the handler, add a test).

### `site_initialization` — site init registry records

| Key | Default | Notes |
|---|---|---|
| `site_name` | `New Plone Site` (name†) | site title in header/tab. |
| `language` | `en` | ISO 639-1 two-letter code. |

### `mockup_pattern` — Mockup JS pattern scaffold

| Key | Default | Notes |
|---|---|---|
| `pattern_name` | `my-pattern` (name†) | without the `pat-` prefix. |
| `pattern_description` | "A custom Mockup JS pattern" | |

### `theme` — full Diazo theme (scss partials + webpack)

| Key | Default | Notes |
|---|---|---|
| `theme_name` | `My Theme` (name†) | shown in the theming control panel. |
| `theme_description` | "A custom Plone theme" | |

Hidden/computed: `theme_id`.

### `theme_barceloneta` — Barceloneta-based theme variant

Same keys as `theme` (`theme_name` is the name† key, `theme_description` defaults to "A Barceloneta-based
Plone theme"); hidden `theme_id`.

### `theme_basic` — minimal basic theme

Same keys as `theme` (`theme_name` is the name† key, `theme_description` defaults to "A basic Plone theme");
hidden `theme_id`.

### `svelte_app` — Svelte app scaffold (vite + Python mount view)

| Key | Default | Notes |
|---|---|---|
| `svelte_app_name` | `my-svelte-app` (name†) | kebab-case. |
| `svelte_app_description` | "A custom Svelte application" | |
| `svelte_app_custom_element` | `false` | compile as a Web Component? |

Hidden/computed: `svelte_app_module`, `svelte_app_class`.

---

## `zope-setup` subtemplates (`plonecli add <sub>` inside a project)

### `zope_instance` — additional named Zope instance

| Key | Default | Choices / notes |
|---|---|---|
| `instance_name` | `instance` (name†) | dir name, e.g. `instance1`, `zeo-client1`. |
| `port` | `8080` | HTTP port. |
| `base_path` | from project context, else `var` | runtime dir. |
| `db_storage` | from project context, else `instance` | choices: `instance`, `relstorage`, `zeo`. |
| `zeo_address` | `localhost:8100` | only when `db_storage=zeo`. |
| `pg_host` / `pg_port` / `pg_dbname` / `pg_user` / `pg_password` | as in zope-setup | only when `db_storage=relstorage`. |
| `initial_zope_username` | `admin` | |
| `initial_user_password` | `admin` (secret) | |

Hidden/computed: `project_name`, `instance_home`.
