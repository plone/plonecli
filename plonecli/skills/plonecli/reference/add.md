# Adding features — `plonecli add <subtemplate>`

Run from **inside** a plonecli-generated project. If you are not in one, the command fails with `NotInPackageError` — `cd` into the project root first.

```shell
cd collective.todo
plonecli add content_type
plonecli add behavior
plonecli add restapi_service
```

## Subtemplates are gated by project type

plonecli detects the project type from `pyproject.toml` (e.g. `backend_addon`, `project`). Only subtemplates whose `parent` matches that type are offered. So:

- Inside a **`backend_addon`**: `content_type`, `behavior`, `restapi_service`.
- Inside a **`zope-setup`** project: `zope_instance`.

Always confirm what is actually available here with `plonecli -l` (run inside the project) — it lists only the applicable subtemplates and reflects the configured template repo/branch.

## The three common backend_addon subtemplates

| Subtemplate | Adds | Typical follow-up |
|---|---|---|
| `content_type` | A Dexterity content type (schema, FTI, registration). | Restart/reinstall the addon so the new type is registered; add tests for the type. |
| `behavior` | A behavior (reusable schema/marker applied to content types). | Wire the behavior onto a content type; add tests. |
| `restapi_service` | A `plone.restapi` service (endpoint, adapter, registration). | Add tests exercising the endpoint. |

copier will prompt interactively for the specifics (names, fields, options) — answer per the user's requirements. Do not invent answers; if the user hasn't specified e.g. field names, ask.

## After adding

1. Review `git status`/diff — `add` writes new files and may touch existing ones (e.g. `configure.zcml`, `profiles`). Preserve intentional local edits.
2. Run `plonecli test` and report real results. Never skip tests.
3. If a running instance is needed to see the change, ask the user to (re)start it — do not start the server yourself.

## zope_instance

Inside a `zope-setup` project, `plonecli add zope_instance` adds an additional named Zope instance. Each instance has its own `.copier-answers.zope-instance-<name>.yml` and can later be reconfigured by name ([maintain.md](maintain.md)).
