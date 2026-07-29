# vhs tape: plonecli demo — BACKEND category
#
# Video 1 of 3. Creates `collective.backenddemo`, runs every backend
# subtemplate (content_type is demonstrated twice: Container then Item),
# then zope-setup with FileStorage (instance).
#
# This tape DRIVES every copier prompt — arrow keys for choices, y/n
# for booleans, text for inputs. Nothing waits on a human.
#
# Requires copier-templates >= the revision that adds `parent_content_type`
# (question fires when global_allow == false). Run `plonecli update` if
# the second content_type step skips that prompt.
#
# Render: vhs docs/demo-backend.tape  →  docs/demo-backend.webm

Output docs/demo-backend.webm

Set Shell "bash"
Set FontSize 16
Set FontFamily "JetBrains Mono"
Set Width 1440
Set Height 900
Set Theme "Dracula"
Set TypingSpeed 80ms
Set PlaybackSpeed 1.0

# ---- Pre-demo (hidden) ----
Hide
Type `eval "$(_PLONECLI_COMPLETE=bash_source plonecli)"` Enter
Type `mkdir -p /tmp/plonecli-demo && cd /tmp/plonecli-demo && rm -rf collective.backenddemo` Enter
Type "clear" Enter
Show
Sleep 1s

# ---- Intro banner ----
Type `echo -e "\n\033[1;45m ━━━ plonecli Demo 1 of 3 — BACKEND templates ━━━ \033[0m\n"` Enter
Sleep 3s

# ---- Common intro: version / list / help / completion ----
Type `echo -e "\n\033[1;46m ▶ STEP 1 — plonecli version \033[0m\n"` Enter
Sleep 2s
Type "plonecli -V" Enter
Sleep 3s
Sleep 5s

Type `echo -e "\n\033[1;46m ▶ STEP 2 — list available templates \033[0m\n"` Enter
Sleep 2s
Type "plonecli -l" Enter
Sleep 5s

Type `echo -e "\n\033[1;46m ▶ STEP 3 — top-level help \033[0m\n"` Enter
Sleep 2s
Type "plonecli --help" Enter
Sleep 5s

Type `echo -e "\n\033[1;46m ▶ STEP 4 — tab-complete top-level commands \033[0m\n"` Enter
Sleep 2s
Type "plonecli "
Sleep 400ms
Tab Tab
Sleep 3s
Ctrl+C
Sleep 1s

Type `echo -e "\n\033[1;46m ▶ STEP 5 — tab-complete main templates for 'create' \033[0m\n"` Enter
Sleep 2s
Type "plonecli create "
Sleep 400ms
Tab Tab
Sleep 3s
Type "add"
Tab
Sleep 1500ms
Ctrl+C
Sleep 1s

# ---- Create the addon (drive 7 backend_addon prompts) ----
Type `echo -e "\n\033[1;46m ▶ STEP 6 — create collective.backenddemo addon \033[0m\n"` Enter
Sleep 2s
Type "plonecli create addon collective.backenddemo" Enter
Sleep 3s
# package_name — default "collective.backenddemo"
Enter
Sleep 1500ms
# package_title
Enter
Sleep 1500ms
# package_description
Enter
Sleep 1500ms
# plone_version (choice — demonstrate arrow nav even for default)
Down
Sleep 800ms
Up
Sleep 800ms
Enter
Sleep 1500ms
# is_headless (bool, default no)
Enter
Sleep 1500ms
# author_name
Enter
Sleep 1500ms
# author_email
Enter
Sleep 20s

Type "cd collective.backenddemo" Enter
Sleep 2s

# ---- behavior (4 prompts) ----
Type `echo -e "\n\033[1;46m ▶ STEP 7 — add behavior \033[0m\n"` Enter
Sleep 2s
Type "plonecli add be"
Tab
Sleep 600ms
Enter
Sleep 3s
# behavior_name (required)
Type "IFeatured"
Sleep 500ms
Enter
Sleep 1500ms
# behavior_description
Enter
Sleep 1500ms
# behavior_marker
Enter
Sleep 1500ms
# behavior_factory
Enter
Sleep 8s
Sleep 5s

# ---- content_type #1 — Container, globally addable ----
Type `echo -e "\n\033[1;46m ▶ STEP 8 — add content_type (Container 'Project', globally addable) \033[0m\n"` Enter
Sleep 2s
Type "plonecli add conte"
Tab
Sleep 600ms
Enter
Sleep 3s
# content_type_name
Type "Project"
Sleep 500ms
Enter
Sleep 1500ms
# content_type_description
Type "A project folder"
Sleep 500ms
Enter
Sleep 1500ms
# content_type_base (choice — Container default, demo arrow navigation)
Down
Sleep 800ms
Up
Sleep 800ms
Enter
Sleep 1500ms
# content_type_icon
Type "folder"
Sleep 500ms
Enter
Sleep 1500ms
# global_allow (bool, default yes)
Enter
Sleep 1500ms
# filter_content_types (bool, default yes — only when Container)
Enter
Sleep 1500ms
# activate_default_behaviors (bool) — answer NO so we can demo dublin/nav prompts
Type "n"
Sleep 500ms
Enter
Sleep 1500ms
# enable_dublin_core (bool, default yes)
Enter
Sleep 1500ms
# enable_navigation (bool, default yes)
Enter
Sleep 10s
Sleep 5s

# ---- content_type #2 — Item, not globally addable ----
Type `echo -e "\n\033[1;46m ▶ STEP 9 — add content_type (Item 'Task', not globally addable) \033[0m\n"` Enter
Sleep 2s
Type "plonecli add conte"
Tab
Sleep 600ms
Enter
Sleep 3s
# content_type_name
Type "Task"
Sleep 500ms
Enter
Sleep 1500ms
# content_type_description
Type "A task inside a Project"
Sleep 500ms
Enter
Sleep 1500ms
# content_type_base (choice — navigate Down to pick Item)
Down
Sleep 800ms
Enter
Sleep 1500ms
# content_type_icon
Type "check2-square"
Sleep 500ms
Enter
Sleep 1500ms
# global_allow — answer NO (opposite of first run)
Type "n"
Sleep 500ms
Enter
Sleep 1500ms
# parent_content_type (choice — default Folder). Choice order:
# Document, File, Image, News Item, Event, Link, Folder, Collection,
# Project, <enter manually>. Navigate 2 x Down from Folder → Project.
Down
Sleep 800ms
Down
Sleep 800ms
Enter
Sleep 1500ms
# (filter_content_types is skipped — content_type_base != Container)
# activate_default_behaviors (bool, default yes)
Enter
Sleep 1500ms
Sleep 10s
Sleep 5s

# ---- controlpanel (3 prompts) ----
Type `echo -e "\n\033[1;46m ▶ STEP 10 — add controlpanel \033[0m\n"` Enter
Sleep 2s
Type "plonecli add contr"
Tab
Sleep 600ms
Enter
Sleep 3s
# controlpanel_name
Enter
Sleep 1500ms
# controlpanel_title
Enter
Sleep 1500ms
# controlpanel_description
Enter
Sleep 8s
Sleep 5s

# ---- indexer (2 prompts) ----
Type `echo -e "\n\033[1;46m ▶ STEP 11 — add indexer \033[0m\n"` Enter
Sleep 2s
Type "plonecli add in"
Tab
Sleep 600ms
Enter
Sleep 3s
# indexer_name
Enter
Sleep 1500ms
# indexer_description
Enter
Sleep 8s
Sleep 5s

# ---- site_initialization (2 prompts) ----
Type `echo -e "\n\033[1;46m ▶ STEP 12 — add site_initialization \033[0m\n"` Enter
Sleep 2s
Type "plonecli add si"
Tab
Sleep 600ms
Enter
Sleep 3s
# site_name
Enter
Sleep 1500ms
# language
Enter
Sleep 8s
Sleep 5s

# ---- subscriber (4 prompts) ----
Type `echo -e "\n\033[1;46m ▶ STEP 13 — add subscriber \033[0m\n"` Enter
Sleep 2s
Type "plonecli add su"
Tab
Sleep 600ms
Enter
Sleep 3s
# subscriber_handler_name
Enter
Sleep 1500ms
# subscriber_event
Enter
Sleep 1500ms
# subscriber_for
Enter
Sleep 1500ms
# subscriber_description
Enter
Sleep 8s
Sleep 5s

# ---- upgrade_step (4 prompts) ----
Type `echo -e "\n\033[1;46m ▶ STEP 14 — add upgrade_step \033[0m\n"` Enter
Sleep 2s
Type "plonecli add up"
Tab
Sleep 600ms
Enter
Sleep 3s
# upgrade_step_title (required)
Type "Add catalog index"
Sleep 500ms
Enter
Sleep 1500ms
# upgrade_step_description
Enter
Sleep 1500ms
# source_version
Enter
Sleep 1500ms
# destination_version
Enter
Sleep 8s
Sleep 5s

# ---- vocabulary (3 prompts) ----
Type `echo -e "\n\033[1;46m ▶ STEP 15 — add vocabulary \033[0m\n"` Enter
Sleep 2s
Type "plonecli add vo"
Tab
Sleep 600ms
Enter
Sleep 3s
# vocabulary_name
Enter
Sleep 1500ms
# vocabulary_description
Enter
Sleep 1500ms
# vocabulary_type (choice simple/catalog — accept simple default)
Enter
Sleep 8s
Sleep 5s

# ---- zope-setup: FileStorage (instance) ----
Type `echo -e "\n\033[1;46m ▶ STEP 16 — plonecli setup with FileStorage (instance) \033[0m\n"` Enter
Sleep 2s
Type "plonecli setup" Enter
Sleep 3s
# plone_version (choice)
Enter
Sleep 1500ms
# distribution (choice, default plone.volto)
Enter
Sleep 1500ms
# base_path
Enter
Sleep 1500ms
# db_storage (choice — 'instance' is default; demo arrow-nav and pick instance)
Down
Sleep 800ms
Down
Sleep 800ms
Up
Sleep 800ms
Up
Sleep 800ms
Enter
Sleep 1500ms
# author_name
Enter
Sleep 1500ms
# author_email
Enter
Sleep 1500ms
# initial_zope_username
Enter
Sleep 1500ms
# initial_user_password (secret)
Enter
Sleep 20s

# ---- Outro ----
Type `echo -e "\n\033[1;46m ▶ STEP 17 — resulting project layout \033[0m\n"` Enter
Sleep 2s
Type "ls -la" Enter
Sleep 4s
Type "ls .copier-answers*.yml" Enter
Sleep 4s
Type "ls src var" Enter
Sleep 4s

Type `echo -e "\n\033[1;42m ✔ Backend demo complete — 7 backend subtemplates + content_type (x2) + FileStorage instance \033[0m\n"` Enter
Sleep 5s
