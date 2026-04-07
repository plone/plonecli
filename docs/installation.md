# Installation


## UV Tool (Recommended)

The recommended way to install plonecli is as a UV tool, which makes it available globally:

```shell
uv tool install plonecli
```

To upgrade:

```shell
uv tool upgrade plonecli
```


## Run Without Installing (uvx)

You can run plonecli without installing it using `uvx`:

```shell
uvx plonecli create addon my.addon
```

Note: shell completion does not work with `uvx`.


## With pipx

```shell
pipx install plonecli
```


## From Sources

The sources for Plone CLI can be downloaded from the [GitHub repo](https://github.com/plone/plonecli/).

```shell
git clone git@github.com:plone/plonecli.git
cd plonecli
uv sync --extra dev --extra test
```


## Shell Completion

plonecli supports tab-completion for commands and template names in bash, zsh, and fish.

To install completion automatically:

```shell
plonecli completion --install
```

Or set it up manually by adding to your shell config:

**Bash** (`~/.bashrc`):
```shell
eval "$(_PLONECLI_COMPLETE=bash_source plonecli)"
```

**Zsh** (`~/.zshrc`):
```shell
eval "$(_PLONECLI_COMPLETE=zsh_source plonecli)"
```

**Fish** (`~/.config/fish/completions/plonecli.fish`):
```shell
env _PLONECLI_COMPLETE=fish_source plonecli | source
```

For faster shell startup, save the completion script to a file instead of using `eval`:

```shell
_PLONECLI_COMPLETE=bash_source plonecli > ~/.plonecli-complete.bash
# Then in ~/.bashrc:
source ~/.plonecli-complete.bash
```
