# plone todos

Note: use plonecli>=7.0.b10, not the current stable version!

Create a new plone addon "derico.todos", with the following features:

## content types (CT's)

### Todos

- type: container
- global addable: yes
- no default behaviors activated
- fields: []


### Todo

- type: item
- global addable: no
- parent: Todos
- no default behaviors activated
- fields:
    - name: priority, type: choice field with vocabulary (hight, normal, low), default: normal
    - name: done, type: boolean, default: False
    - name: description, type: RichText, required: False

## views

### Todos view

name: view
registration for CT: Todos
purpose: lists todos and there status (done yes/no), allows filtering by status, show only open by default.

### Todo

name: view
registration for CT: Todo
purpose: shows Todo details

The addon has to be translated into german.

## Restapi

create a restapi service to show all todo infos on the todos list without calling single todos.
