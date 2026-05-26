# Declarative spec (`plonecli apply`)

`plonecli apply spec.yaml` scaffolds a complete addon — the main project plus an
ordered list of feature subtemplates — from **one** declarative YAML file, fully
non-interactively. Use it when you have a feature list up front (e.g. an agent
turning a requirements doc into an addon). For one-off steps, use `create`/`add`.

```shell
plonecli apply spec.yaml            # validate, then generate
plonecli apply --check spec.yaml    # validate + print the plan, generate nothing
plonecli apply --no-git spec.yaml   # skip git init / auto-commit
```

`apply` validates the **whole** spec up front (fail-fast) before writing any
files, so a typo in feature #5 is reported before feature #1 is generated.

## Format

```yaml
addon:
  template: backend_addon        # backend_addon | addon (composite) | zope-setup
  name: collective.todo          # target package/project name (also the directory)
  data:                          # answers for the main template (optional)
    plone_version: "6.1"
features:                        # ordered subtemplates (optional)
  - template: content_type
    data:
      content_type_name: Todos
      global_allow: true
  - template: content_type
    data:
      content_type_name: Todo
      global_allow: false
      parent_content_type: Todos
  - template: behavior
    data:
      behavior_name: IFeatured
  - template: restapi_service
    data:
      service_name: stats
  - template: language
    data:
      language_code: de
      language_name: German
```

* `addon.template` / `addon.name` are required.
* `data` keys are the template's `-d` answers — see [templates.md](templates.md)
  for every template's keys, defaults and choices.
* `features` run in order, each on top of the generated addon, exactly as
  repeated `plonecli add` calls would.
* `package_name`/`package_folder` for features are filled automatically from the
  generated addon — do not put them in feature `data`.

## What the spec does NOT cover: fields

Fields are **out of scope**. `content_type` and `behavior` emit an empty schema
(`pass`); the spec only chooses templates and their options. Add fields **after**
generation by editing the generated schema class (see [fields.md](fields.md)) or
with plone-snippets. Do not expect the spec to define fields.

## Validation rules

`apply` (and `--check`) report, before generating:

* unknown `addon.template` (not a project template);
* a feature `template` that is not a valid subtemplate for the project type;
* unknown answer keys for a template;
* missing required answers (e.g. `content_type_name`);
* values outside a template's fixed `choices` (dynamic choices like
  `plone_version` are not range-checked here — copier validates them at run time).
