# Adding fields to a content type or behavior

plonecli has **no field-adding subtemplate**. `plonecli add content_type` (and
`plonecli add behavior`) scaffold a `model.Schema` class with only commented
examples; fields are added by **hand-editing that `.py` schema file**. Both a
content type and a behavior use the **same field syntax** — everything here
applies to both.

Where the schema class lives:

- **content type:** `src/<package>/content/<module>.py`
- **behavior:** `src/<package>/behaviors/<module>.py`

Replace the `pass` / commented examples in the schema class with real field
definitions. Do **not** re-run a copier subtemplate to "add a field" and do not
hand-write FTI/profile XML for it — Dexterity reads the fields from the Python
schema.

## Per-field question flow

Fields are application-specific and are **not** copier `-d` answers, so don't
guess them. For **each** field the user wants, gather these four answers, then
write the field. Ask the user with whatever question mechanism the host agent
provides (Claude Code: `AskUserQuestion`; other agents: their own UI).

1. **Field name** — Python identifier in `snake_case`, e.g. `start_date`.
2. **Field type** — pick from the catalogue below (TextLine, Text, RichText,
   Bool, Int, Float, Choice, Multi-Choice, Date, Datetime, Email, URI,
   NamedBlobImage, NamedBlobFile, RelationChoice, RelationList, …).
3. **Required** — yes/no. **Default: no** (`required=False`).
4. **Default value** — optional. Map to `default=…`; omit the line if none.

Conditional follow-ups — ask only when the chosen type needs it:

- **Choice / Multi-Choice** → a named `vocabulary=` *or* an inline `values=`
  (`SimpleVocabulary`).
- **List / Tuple / Set / FrozenSet** → a `value_type=` (e.g.
  `schema.TextLine(...)`).
- **RelationChoice / RelationList** → target portal type(s) /
  `plone.app.vocabularies.Catalog` or a `CatalogSource`.
- **DataGrid** → the row schema interface and the `collective.z3cform.datagridfield`
  dependency.

## Field catalogue

`schema` is `zope.schema`. The scaffolded module imports only `schema` (`from
zope import schema`) and `model` (`from plone.supermodel import model`). Add any
other import below as needed — and `from plone.supermodel import directives`
before using `directives.*`.

| Type | Field class | Import | Needs |
|---|---|---|---|
| Single-line text | `schema.TextLine` | `from zope import schema` | — |
| Multi-line text | `schema.Text` | `from zope import schema` | — |
| Rich text (HTML) | `RichText` | `from plone.app.textfield import RichText` | — |
| Boolean | `schema.Bool` | `from zope import schema` | — |
| Integer | `schema.Int` | `from zope import schema` | — |
| Float | `schema.Float` | `from zope import schema` | — |
| Decimal | `schema.Decimal` | `from zope import schema` | — |
| Single choice | `schema.Choice` | `from zope import schema` | `vocabulary=` or `values=` |
| Multi choice | `schema.List` / `schema.Set` | `from zope import schema` | `value_type=schema.Choice(...)` |
| List | `schema.List` | `from zope import schema` | `value_type=` |
| Tuple | `schema.Tuple` | `from zope import schema` | `value_type=` |
| Set / FrozenSet | `schema.Set` / `schema.FrozenSet` | `from zope import schema` | `value_type=` |
| Date | `schema.Date` | `from zope import schema` | — |
| Datetime | `schema.Datetime` | `from zope import schema` | — |
| Email | `schema.Email` | `from plone.schema import Email` | from `plone.schema`, not `zope.schema` |
| URI / URL | `schema.URI` | `from zope import schema` | — |
| JSON | `JSONField` | `from plone.schema import JSONField` | `schema=json.dumps({})` |
| Password | `schema.Password` | `from zope import schema` | — |
| Id | `schema.Id` | `from zope import schema` | — |
| DottedName | `schema.DottedName` | `from zope import schema` | optional `min_dots`/`max_dots` |
| Interface | `schema.InterfaceField` | `from zope import schema` | — |
| Source text | `schema.SourceText` | `from zope import schema` | — |
| ASCII / ASCIILine | `schema.ASCII` / `schema.ASCIILine` | `from zope import schema` | — |
| Bytes / BytesLine | `schema.Bytes` / `schema.BytesLine` | `from zope import schema` | — |
| File upload | `NamedBlobFile` | `from plone.namedfile.field import NamedBlobFile` | — |
| Image upload | `NamedBlobImage` | `from plone.namedfile.field import NamedBlobImage` | — |
| Relation (single) | `RelationChoice` | `from z3c.relationfield.schema import RelationChoice` | `vocabulary="plone.app.vocabularies.Catalog"` |
| Relation (multi) | `RelationList` | `from z3c.relationfield.schema import RelationList` | `value_type=RelationChoice(...)` |
| Tabular grid | `schema.List` of `DictRow` | `from collective.z3cform.datagridfield import DataGridFieldFactory, DictRow` | row schema + extra dependency |

`plone.namedfile`, `z3c.relationfield` and `collective.z3cform.datagridfield`
fields need their package listed in `install_requires`/`dependencies` in
`pyproject.toml` (namedfile and relationfield are pulled in by Plone core;
datagridfield is an extra add-on).

## Field definition templates

Common types, ready to adapt. `title`/`description` use plain strings, matching
the scaffolded examples. Set `required=True` only when the user said yes
(default is `False`); drop `default=` when there is no default.

```python
# TextLine — single line
speaker = schema.TextLine(
    title="Speaker",
    description="Name of the speaker",
    required=False,
    default="",
)

# Text — multi-line plain text
abstract = schema.Text(
    title="Abstract",
    required=False,
)

# RichText — WYSIWYG HTML
body = RichText(
    title="Body text",
    required=False,
)

# Bool
featured = schema.Bool(
    title="Featured",
    required=False,
    default=False,
)

# Int
seats = schema.Int(
    title="Seats",
    required=False,
)

# Choice — named vocabulary
audience = schema.Choice(
    title="Audience",
    vocabulary="plone.app.vocabularies.PortalTypes",
    required=False,
)

# Choice — inline values
level = schema.Choice(
    title="Level",
    values=["beginner", "intermediate", "advanced"],
    required=False,
)

# Multi choice
tags = schema.List(
    title="Tags",
    value_type=schema.TextLine(title="Tag"),
    required=False,
    default=[],
)

# Date / Datetime
start = schema.Datetime(
    title="Start",
    required=False,
)

# Image upload
image = NamedBlobImage(
    title="Lead image",
    required=False,
)

# Relation (single)
related = RelationChoice(
    title="Related item",
    vocabulary="plone.app.vocabularies.Catalog",
    required=False,
)
```

For inline `values=` on a Choice you may also build a vocabulary explicitly:

```python
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary

LEVELS = SimpleVocabulary([
    SimpleTerm(value="beginner", title="Beginner"),
    SimpleTerm(value="advanced", title="Advanced"),
])
```

**i18n:** to make titles translatable, define a message factory once in the
package `__init__.py` (`from zope.i18nmessageid import MessageFactory` then
`_ = MessageFactory("<package>")`), import it in the schema module
(`from <package> import _`), and wrap strings as `title=_("Speaker")`.

## Widgets & autoform directives

Use `plone.autoform`/`plone.supermodel` directives inside the schema class to
control widgets, ordering, fieldsets, visibility and permissions. `model` is
imported in the scaffolded module; add `from plone.supermodel import directives`
before using `directives.*`.

```python
# Pick a widget (the widget must be imported)
directives.widget(level=RadioFieldWidget)

# Group fields into a fieldset / tab
model.fieldset(
    "details",
    label=_("Details"),
    fields=["speaker", "level"],
)

# Order, visibility, mode
directives.order_before(level="speaker")
directives.omitted("internal_note")
directives.no_omit("internal_note")
directives.mode(edit="hidden")

# Field-level permissions
directives.read_permission(secret="cmf.ManagePortal")
directives.write_permission(secret="cmf.ManagePortal")
```

Common widgets (import from `plone.app.z3cform.widgets`; see
<https://github.com/plone/plone.app.z3cform/tree/master/plone/app/z3cform/widgets>):
`TextWidget`, `RadioFieldWidget`, `CheckBoxFieldWidget`,
`SingleCheckBoxBoolFieldWidget`, `SelectFieldWidget`, `AjaxSelectFieldWidget`,
`RelatedItemsFieldWidget`, `WysiwygFieldWidget`, `QueryStringFieldWidget`,
`TextLinesFieldWidget`, `OptgroupFieldWidget`, `LinkFieldWidget`.

> Source for the field/widget catalogue: the
> [plone/plone-vs-snippets](https://github.com/plone/plone-vs-snippets) VS Code
> extension (`Plone Snippets`), which documents the full set of Plone Python and
> XML schema fields, widgets and autoform directives.

## After editing

- The schema is **Python**, not GenericSetup profile XML, so adding fields needs
  **no upgrade step** by itself — there is no `profiles/default/*` change.
- Restart/reinstall the addon to see the new fields. Run `plonecli test` and
  report real results.
- An upgrade step **is** needed only if the same change also edits profile XML —
  e.g. you add a catalog index/metadata for the field (`catalog.xml`) or change
  `types/*.xml`. Then follow the upgrade-step rule in
  [add.md](add.md#upgrade_step--required-after-profile-xml-changes).
- Review `git status`/diff and preserve intentional local edits.
