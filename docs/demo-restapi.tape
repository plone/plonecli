# vhs tape: plonecli demo — REST API category
#
# Video 2 of 3. Creates `collective.restapidemo`, runs the two REST API
# subtemplates (restapi_service, svelte_app), then zope-setup with ZEO.
#
# This tape DRIVES every copier prompt — arrow keys for choices, y/n
# for booleans, text for inputs. Nothing waits on a human.
#
# Render: vhs docs/demo-restapi.tape  →  docs/demo-restapi.gif

Output docs/demo-restapi.gif

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
Type `mkdir -p /tmp/plonecli-demo && cd /tmp/plonecli-demo && rm -rf collective.restapidemo` Enter
Type "clear" Enter
Show
Sleep 1s

# ---- Intro banner ----
Type `echo -e "\n\033[1;45m ━━━ plonecli Demo 2 of 3 — REST API templates ━━━ \033[0m\n"` Enter
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
Type `echo -e "\n\033[1;46m ▶ STEP 6 — create collective.restapidemo addon \033[0m\n"` Enter
Sleep 2s
Type "plonecli create addon collective.restapidemo" Enter
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

Type "cd collective.restapidemo" Enter
Sleep 2s

# ---- restapi_service (8 prompts) ----
Type `echo -e "\n\033[1;46m ▶ STEP 7 — add restapi_service \033[0m\n"` Enter
Sleep 2s
Type "plonecli add re"
Tab
Sleep 600ms
Enter
Sleep 3s
# service_name (required)
Type "stats"
Sleep 500ms
Enter
Sleep 1500ms
# service_description
Enter
Sleep 1500ms
# expandable (bool, default no)
Enter
Sleep 1500ms
# http_get (bool, default yes)
Enter
Sleep 1500ms
# http_post (bool, default no)
Enter
Sleep 1500ms
# http_patch (bool, default no)
Enter
Sleep 1500ms
# http_delete (bool, default no)
Enter
Sleep 1500ms
# service_for (choice — demo arrow nav, accept default)
Down
Sleep 800ms
Up
Sleep 800ms
Enter
Sleep 10s
Sleep 5s

# ---- svelte_app (3 prompts) ----
Type `echo -e "\n\033[1;46m ▶ STEP 8 — add svelte_app (frontend that consumes the REST API) \033[0m\n"` Enter
Sleep 2s
Type "plonecli add sv"
Tab
Sleep 600ms
Enter
Sleep 3s
# svelte_app_name
Enter
Sleep 1500ms
# svelte_app_description
Enter
Sleep 1500ms
# svelte_app_custom_element (bool, default no)
Enter
Sleep 15s
Sleep 5s

# ---- zope-setup: ZEO ----
Type `echo -e "\n\033[1;46m ▶ STEP 9 — plonecli setup with ZEO \033[0m\n"` Enter
Sleep 2s
Type "plonecli setup" Enter
Sleep 3s
# plone_version
Enter
Sleep 1500ms
# distribution (default plone.volto — REST API / headless path)
Enter
Sleep 1500ms
# base_path
Enter
Sleep 1500ms
# db_storage — choices are [instance, relstorage, zeo]; pick 'zeo' (2 x Down)
Down
Sleep 800ms
Down
Sleep 800ms
Enter
Sleep 1500ms
# zeo_address (default localhost:8100)
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
Type `echo -e "\n\033[1;46m ▶ STEP 10 — resulting project layout \033[0m\n"` Enter
Sleep 2s
Type "ls -la" Enter
Sleep 4s
Type "ls .copier-answers*.yml" Enter
Sleep 4s
Type "ls src var" Enter
Sleep 4s

Type `echo -e "\n\033[1;42m ✔ REST API demo complete — restapi_service + svelte_app + ZEO instance \033[0m\n"` Enter
Sleep 5s
