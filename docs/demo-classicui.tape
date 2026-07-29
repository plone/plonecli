# vhs tape: plonecli demo — CLASSIC UI category
#
# Video 3 of 3. Creates `collective.classicuidemo`, runs all 8 classic-ui
# subtemplates, then zope-setup with RelStorage (PostgreSQL).
#
# This tape DRIVES every copier prompt — arrow keys for choices, y/n
# for booleans, text for inputs. Nothing waits on a human.
#
# Render: vhs docs/demo-classicui.tape  →  docs/demo-classicui.gif

Output docs/demo-classicui.gif

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
Type `mkdir -p /tmp/plonecli-demo && cd /tmp/plonecli-demo && rm -rf collective.classicuidemo` Enter
Type "clear" Enter
Show
Sleep 1s

# ---- Intro banner ----
Type `echo -e "\n\033[1;45m ━━━ plonecli Demo 3 of 3 — CLASSIC UI templates ━━━ \033[0m\n"` Enter
Sleep 3s

# ---- Common intro: version / list / help / completion ----
Type `echo -e "\n\033[1;46m ▶ STEP 1 — plonecli version \033[0m\n"` Enter
Sleep 2s
Type "plonecli -V" Enter
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
Type `echo -e "\n\033[1;46m ▶ STEP 6 — create collective.classicuidemo addon \033[0m\n"` Enter
Sleep 2s
Type "plonecli create addon collective.classicuidemo" Enter
Sleep 3s
# package_name
Enter
Sleep 1500ms
# package_title
Enter
Sleep 1500ms
# package_description
Enter
Sleep 1500ms
# plone_version (choice — demo arrow nav)
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

Type "cd collective.classicuidemo" Enter
Sleep 2s

# ---- form (4 prompts) ----
Type `echo -e "\n\033[1;46m ▶ STEP 7 — add form \033[0m\n"` Enter
Sleep 2s
Type "plonecli add fo"
Tab
Sleep 600ms
Enter
Sleep 3s
# form_name
Enter
Sleep 1500ms
# form_class_name
Enter
Sleep 1500ms
# form_for
Enter
Sleep 1500ms
# form_description
Enter
Sleep 8s
Sleep 5s

# ---- mockup_pattern (2 prompts) ----
Type `echo -e "\n\033[1;46m ▶ STEP 8 — add mockup_pattern \033[0m\n"` Enter
Sleep 2s
Type "plonecli add mo"
Tab
Sleep 600ms
Enter
Sleep 3s
# pattern_name
Enter
Sleep 1500ms
# pattern_description
Enter
Sleep 8s
Sleep 5s

# ---- portlet (2 prompts) ----
Type `echo -e "\n\033[1;46m ▶ STEP 9 — add portlet \033[0m\n"` Enter
Sleep 2s
Type "plonecli add po"
Tab
Sleep 600ms
Enter
Sleep 3s
# portlet_name
Enter
Sleep 1500ms
# portlet_description
Enter
Sleep 8s
Sleep 5s

# ---- theme (2 prompts) ----
# 'theme' alone is ambiguous with theme_barceloneta/theme_basic — Tab Tab
# lists all three, then we disambiguate by backspacing extras and pressing Enter.
Type `echo -e "\n\033[1;46m ▶ STEP 10 — add theme \033[0m\n"` Enter
Sleep 2s
Type "plonecli add theme"
Sleep 400ms
Tab Tab
Sleep 2s
Type " "
Sleep 400ms
Enter
Sleep 3s
# theme_name
Enter
Sleep 1500ms
# theme_description
Enter
Sleep 8s
Sleep 5s

# ---- theme_barceloneta (2 prompts) ----
Type `echo -e "\n\033[1;46m ▶ STEP 11 — add theme_barceloneta \033[0m\n"` Enter
Sleep 2s
Type "plonecli add theme_bar"
Tab
Sleep 600ms
Enter
Sleep 3s
# theme_name
Enter
Sleep 1500ms
# theme_description
Enter
Sleep 8s
Sleep 5s

# ---- theme_basic (2 prompts) ----
Type `echo -e "\n\033[1;46m ▶ STEP 12 — add theme_basic \033[0m\n"` Enter
Sleep 2s
Type "plonecli add theme_bas"
Tab
Sleep 600ms
Enter
Sleep 3s
# theme_name
Enter
Sleep 1500ms
# theme_description
Enter
Sleep 8s
Sleep 5s

# ---- view (6 prompts) ----
Type `echo -e "\n\033[1;46m ▶ STEP 13 — add view \033[0m\n"` Enter
Sleep 2s
Type "plonecli add vie"
Tab
Sleep 600ms
Enter
Sleep 3s
# view_name
Enter
Sleep 1500ms
# view_class_name
Enter
Sleep 1500ms
# view_base_class (choice)
Enter
Sleep 1500ms
# view_template (bool, default yes)
Enter
Sleep 1500ms
# view_for (choice)
Enter
Sleep 1500ms
# view_description
Enter
Sleep 8s
Sleep 5s

# ---- viewlet (6 prompts) ----
Type `echo -e "\n\033[1;46m ▶ STEP 14 — add viewlet \033[0m\n"` Enter
Sleep 2s
Type "plonecli add viewl"
Tab
Sleep 600ms
Enter
Sleep 3s
# viewlet_name
Enter
Sleep 1500ms
# viewlet_class_name
Enter
Sleep 1500ms
# viewlet_manager (choice — accept plone.portalheader default)
Enter
Sleep 1500ms
# viewlet_for
Enter
Sleep 1500ms
# viewlet_template (bool, default yes)
Enter
Sleep 1500ms
# viewlet_description
Enter
Sleep 8s
Sleep 5s

# ---- zope-setup: RelStorage (PostgreSQL) ----
Type `echo -e "\n\033[1;46m ▶ STEP 15 — plonecli setup with RelStorage (PostgreSQL) \033[0m\n"` Enter
Sleep 2s
Type "plonecli setup" Enter
Sleep 3s
# plone_version
Enter
Sleep 1500ms
# distribution — pick plone.classicui (Down)
Down
Sleep 800ms
Enter
Sleep 1500ms
# base_path
Enter
Sleep 1500ms
# db_storage — choices are [instance, relstorage, zeo]; pick 'relstorage' (1 x Down)
Down
Sleep 800ms
Enter
Sleep 1500ms
# pg_host
Enter
Sleep 1500ms
# pg_port
Enter
Sleep 1500ms
# pg_dbname (default plone_collective_classicuidemo)
Enter
Sleep 1500ms
# pg_user
Enter
Sleep 1500ms
# pg_password (secret)
Type "secret"
Sleep 500ms
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
# initial_user_password
Enter
Sleep 20s

# ---- Outro ----
Type `echo -e "\n\033[1;46m ▶ STEP 16 — resulting project layout \033[0m\n"` Enter
Sleep 2s
Type "ls -la" Enter
Sleep 4s
Type "ls .copier-answers*.yml" Enter
Sleep 4s
Type "ls src var" Enter
Sleep 4s

Type `echo -e "\n\033[1;42m ✔ Classic UI demo complete — 8 classic-ui subtemplates + RelStorage (PostgreSQL) \033[0m\n"` Enter
Sleep 5s
