History
=======

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
