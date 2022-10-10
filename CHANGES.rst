History
=======

2.5 (unreleased)
----------------

- Nothing changed yet.


2.4 (2022-10-10)
----------------

- Depend on bobtemplates.plone >=6.0b15 ;)


2.3 (2022-10-08)
----------------

- Depend on bobtemplates.plone >=6.0b16


2.2 (2022-05-04)
----------------

- Remove dependency on ``virtualenv``.
  [wesleybl]

- Rename deprecated ``autocompletion`` parameter to ``shell_complete``
  [zshashz]


2.1.2 (2021-05-06)
------------------

- Fix broken releases 2.1/2.1.1
  [MrTango]


2.1.1 (2021-05-05)
------------------

- Fix setup.cfg - v2.1 is a brown bag release.
  [jensens]

- Improve README
  [svx]


2.1 (2021-05-05)
----------------

- Call mr.bob using its API, no longer as subprocess.
  This ease the usage in a virtualenv.
  [jensens]

- Do not install zest.releaser with plonecli (keep for dev/tox).
  [jensens]

- Do not install virtualenv if not Python 2.7
  [jensens]


2.0 (2020-12-10)
----------------

- Release


2.0b1 (2020-11-20)
------------------

- Add alias upport and an alias for "virtualenv" for the venv command
  [MrTango]

- Improve handling of global/local commands, we use ClickFilteredAliasedGroup to filter the command rather than using an if condition in code.
  [MrTango]


2.0a2 (2020-11-19)
------------------

- Fix #63 generate_mrbob_ini and the acconding tests
  [MrTango]

- Drop Python2.7 support and remove it from tox and travis setup. Also improve linting with new isort and black.
  [MrTango]

- Add config command to disable the venv creation/update on plonecli build command
  [MrTango]

- Allow auto completion of template names
  [MrTango]

- Improve mrbob config generation and now override an existing config file after a warning
  [MrTango]

- Fix typos, ReST formatting and update content of README.rst.
  [staeff]


1.1 (2019-04-14)
----------------

- Add new build option -p to define the python binary to use for the virtualenv
  [MrTango]


1.0 (2019-03-08)
----------------

- add note for including install directory to $PATH
  [fgrcon]

- Document the new `deprecated` and `info` options
  [erral]

- modernize code for Python 3 support
  [MrTango]


0.3.0 (2018-10-17)
------------------

- Sort templates on --list-templates/-l command output
  [MrTango]

- Show deprecate flag and info for templates in template list
  [MrTango]

- Use the now released click library in version >= 7.0, you have to uninstall plonecli-click before upgrading!
  [MrTango]

0.2.2 (2018-08-13)
------------------

- Add -t and -s options to the test command
  [kakshay21]

- Fix #33 ConfigParser.NoOptionError
  [kakshay21]


0.2.1 (2018-07-09)
------------------

- Add plonecli config command to configure mrbob's global user settings
  [kakshay21]

- Add versions -V/--versions command
  [kakshay21]

- Add document commends -h, -V, test and config in README
  [kakshay21]


0.2.0 (2018-04-03)
------------------

- Add test command to allow running test from plonecli
  [MrTango]


0.1.1 (2018-03-28)
------------------

- Improve command line output with colors and remove verbose option
  [MrTango]

- Add virtualenv as requirement and improve README
  [MrTango]


0.1.1b6 (2018-03-28)
--------------------

- fix autocomletion for top level commands
  [MrTango]


0.1.1b5 (2018-03-27)
--------------------

- use bobtemplates.plone>=3.0.0b5
  [MrTango]


0.1.1b4 (2018-03-26)
--------------------

- Use a forked version of click library (plonecli-click) as dependency for now
  [MrTango]


0.1.1b3 (2018-03-23)
--------------------

- Fix broken release


0.1.1b2 (2018-03-22)
--------------------

- Fix dist on pypi


0.1.1b1 (2018-03-22)
--------------------

- Add requirements.txt referencing the special Click version.
  This makes a ``pip`` installation possible.
  [jensens]
- Refactored registry to use the new bobtemplate.cfg
  [MrTango]


0.1.0a4 (2017-10-30)
--------------------

- provide plonecli_autocomplete.sh for bash autocompletion
  [MrTango]
- fix depency to bobtemplates.plone, we need >=3.0.0a3
  [MrTango]


0.1.0a3 (2017-10-24)
--------------------

- Update README to use easy_install instead of pip for now
  [MrTango]


0.1.0a2 (2017-10-24)
--------------------

- fix setup.py to use the github version of click, until click >6.7 is released
  [MrTango]


0.1.0a1 (2017-10-24)
--------------------

- initital version with list templates support and bobtemplates.plone integration
  [MrTango, tmassman, Gomez]
