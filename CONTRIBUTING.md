# Contributing

Contributions are welcome, and they are greatly appreciated! Every
little bit helps, and credit will always be given.

You can contribute in many ways:

## Types of Contributions

### Report Bugs

Report bugs at https://github.com/plone/plonecli/issues.

If you are reporting a bug, please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

### Fix Bugs

Look through the GitHub issues for bugs. Anything tagged with "bug"
and "help wanted" is open to whoever wants to implement it.

### Implement Features

Look through the GitHub issues for features. Anything tagged with "enhancement"
and "help wanted" is open to whoever wants to implement it.

### Write Documentation

Plone CLI could always use more documentation, whether as part of the
official Plone CLI docs, in docstrings, or even on the web in blog posts,
articles, and such.

### Submit Feedback

The best way to send feedback is to file an issue at https://github.com/plone/plonecli/issues.

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that contributions
  are welcome :)

## Get Started!

Ready to contribute? Here's how to set up `plonecli` for local development.

1. Clone the repo locally:

   ```shell
   git clone git@github.com:plone/plonecli.git
   ```

2. Create a branch of the `plonecli` repo:

   ```shell
   git checkout -b yourgithubuser_topic
   ```

3. Create a virtualenv and install your local copy:

   ```shell
   python3 -m venv venv
   ./venv/bin/pip install -e .[dev]
   ```

   Now you can make your changes locally.

4. When you're done making changes, run test and linters with tox:

   ```shell
   tox
   ```

   To get flake8 and tox, just pip install them into your virtualenv.

5. Commit your changes and push your branch to GitHub:

   ```shell
   git add .
   git commit -m "Your detailed description of your changes."
   git push
   ```

6. Submit a pull request through the GitHub website.

## Pull Request Guidelines

Before you submit a pull request, check that it meets these guidelines:

1. Update CHANGES.md file


## Tips

To run a subset of tests:

```shell
tox -l
py27
py37
py38
py39
flake8
tox -e flake8
```
