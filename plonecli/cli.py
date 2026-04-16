"""Console script for plonecli."""

from __future__ import annotations

import importlib.metadata
import subprocess
import sys

import click
from click_aliases import ClickAliasedGroup

from plonecli.config import load_config, save_config
from plonecli.exceptions import NoSuchValue, NotInPackageError
from plonecli.project import find_project_root
from plonecli.registry import TemplateRegistry
from plonecli.templates import (
    ensure_templates_cloned,
    get_templates_info,
    run_add,
    run_create,
    update_templates_clone,
)


def echo(msg, fg="green", reverse=False):
    click.echo(click.style(msg, fg=fg, reverse=reverse))


def _get_registry():
    """Create a TemplateRegistry with current context."""
    config = load_config()
    project = find_project_root()
    return TemplateRegistry(config, project)


def get_templates(ctx, args, incomplete):
    """Shell completion for template names."""
    reg = _get_registry()
    templates = reg.get_available_templates()
    return [k for k in templates if incomplete in k]


class ClickFilteredAliasedGroup(ClickAliasedGroup):
    def list_commands(self, ctx):
        existing_cmds = super().list_commands(ctx)
        project = find_project_root()
        global_cmds = ["completion", "create", "config", "update"]
        global_only_cmds = ["create"]
        if not project:
            cmds = [cmd for cmd in existing_cmds if cmd in global_cmds]
        else:
            cmds = [cmd for cmd in existing_cmds if cmd not in global_only_cmds]
        return cmds


@click.group(
    cls=ClickFilteredAliasedGroup,
    chain=True,
    context_settings={"help_option_names": ["-h", "--help"]},
    invoke_without_command=True,
)
@click.option("-l", "--list-templates", "list_templates", is_flag=True)
@click.option("-V", "--versions", "versions", is_flag=True)
@click.pass_context
def cli(context, list_templates, versions):
    """Plone Command Line Interface (CLI)"""
    config = load_config()
    project = find_project_root()
    context.obj = {
        "config": config,
        "project": project,
        "target_dir": str(project.root_folder) if project else None,
    }

    if list_templates:
        reg = TemplateRegistry(config, project)
        click.echo(reg.list_templates())

    if versions:
        plonecli_version = importlib.metadata.version("plonecli")
        templates_info = get_templates_info(config)
        click.echo(f"plonecli: {plonecli_version}")
        click.echo(f"copier-templates: {templates_info}")

    # Check for updates (non-blocking, cached)
    if not list_templates and not versions:
        try:
            from plonecli.updater import check_for_updates

            new_version = check_for_updates()
            if new_version:
                echo(
                    f"\nA new version of plonecli is available: {new_version}",
                    fg="yellow",
                )
                echo(
                    "Update with: uv tool upgrade plonecli\n",
                    fg="yellow",
                )
        except Exception:  # noqa: BLE001
            pass


@cli.command()
@click.argument("template", type=click.STRING, shell_complete=get_templates)
@click.argument("name")
@click.pass_context
def create(context, template, name):
    """Create a new Plone package"""
    config = context.obj["config"]
    reg = TemplateRegistry(config)

    resolved = reg.resolve_template_name(template)
    if resolved is None or not reg.is_main_template(resolved):
        raise NoSuchValue(
            context.command.name,
            template,
            possibilities=reg.get_main_templates(),
        )

    steps = reg.get_composite_steps(resolved)
    if steps:
        echo(f"\nCreating {resolved} project: {name}", fg="green", reverse=True)
        for step in steps:
            echo(f"\n  Applying template: {step}", fg="green")
            run_create(step, name, config)
    else:
        echo(f"\nCreating {resolved} project: {name}", fg="green", reverse=True)
        run_create(resolved, name, config)
    context.obj["target_dir"] = name


@cli.command()
@click.argument("template", type=click.STRING, shell_complete=get_templates)
@click.pass_context
def add(context, template):
    """Add features to your existing Plone package"""
    project = context.obj.get("project")
    if project is None:
        raise NotInPackageError(context.command.name)

    config = context.obj["config"]
    reg = TemplateRegistry(config, project)

    resolved = reg.resolve_template_name(template)
    if resolved is None or not reg.is_subtemplate(resolved):
        raise NoSuchValue(
            context.command.name,
            template,
            possibilities=reg.get_subtemplates(),
        )

    echo(f"\nAdding {resolved} to {project.root_folder.name}", fg="green", reverse=True)
    run_add(resolved, project, config)


@cli.command()
@click.pass_context
def setup(context):
    """Run zope-setup inside an existing backend_addon"""
    project = context.obj.get("project")
    if project is None:
        raise NotInPackageError(context.command.name)
    if project.project_type != "backend_addon":
        raise click.UsageError(
            "The 'setup' command can only be run inside a backend_addon project."
        )

    config = context.obj["config"]
    echo("\nRunning zope-setup...", fg="green", reverse=True)
    run_create("zope-setup", str(project.root_folder), config)


@cli.command("serve")
@click.pass_context
def run_serve(context):
    """Start the Plone instance (delegates to invoke start)"""
    project = context.obj.get("project")
    if project is None:
        raise NotInPackageError(context.command.name)
    params = ["uv", "run", "invoke", "start"]
    echo(f"\nRUN: {' '.join(params)}", fg="green", reverse=True)
    echo("\nINFO: Open this in a Web Browser: http://localhost:8080")
    echo("INFO: You can stop it by pressing CTRL + c\n")
    subprocess.call(params, cwd=str(project.root_folder))


@cli.command("test")
@click.option("-v", "--verbose", is_flag=True, help="Verbose test output")
@click.pass_context
def run_test(context, verbose):
    """Run the tests in your package (delegates to invoke test)"""
    project = context.obj.get("project")
    if project is None:
        raise NotInPackageError(context.command.name)
    params = ["uv", "run", "invoke", "test"]
    if verbose:
        params.append("--verbose")
    echo(f"\nRUN: {' '.join(params)}", fg="green", reverse=True)
    subprocess.call(params, cwd=str(project.root_folder))


@cli.command("debug")
@click.pass_context
def run_debug(context):
    """Start the Plone instance in debug mode (delegates to invoke debug)"""
    project = context.obj.get("project")
    if project is None:
        raise NotInPackageError(context.command.name)
    params = ["uv", "run", "invoke", "debug"]
    echo(f"\nRUN: {' '.join(params)}", fg="green", reverse=True)
    echo("INFO: You can stop it by pressing CTRL + c\n")
    subprocess.call(params, cwd=str(project.root_folder))


@cli.command()
@click.pass_context
def config(context):
    """Configure plonecli global settings"""
    cfg = context.obj["config"]

    # Check for migration from .mrbob on first run
    from plonecli.config import CONFIG_FILE, migrate_from_mrbob

    if not CONFIG_FILE.exists():
        migrated = migrate_from_mrbob()
        if migrated:
            echo("Found existing ~/.mrbob configuration.", fg="yellow")
            if click.confirm("Import settings from ~/.mrbob?", default=True):
                cfg = migrated

    # Interactive prompts with current values as defaults
    cfg.author_name = click.prompt("Author name", default=cfg.author_name)
    cfg.author_email = click.prompt("Author email", default=cfg.author_email)
    cfg.github_user = click.prompt("GitHub username", default=cfg.github_user)

    # Suggest latest Plone version
    from plonecli.plone_versions import get_latest_stable_version

    default_version = cfg.plone_version or get_latest_stable_version()
    cfg.plone_version = click.prompt(
        "Default Plone version", default=default_version
    )

    cfg.repo_url = click.prompt("Templates repo URL", default=cfg.repo_url)
    cfg.repo_branch = click.prompt("Templates branch", default=cfg.repo_branch)

    save_config(cfg)
    echo(f"\nConfiguration saved to {CONFIG_FILE}", fg="green")


@cli.command()
@click.pass_context
def update(context):
    """Update copier-templates and check for plonecli updates"""
    config = context.obj["config"]

    # Update templates clone
    echo("\nUpdating copier-templates...", fg="green")
    try:
        ensure_templates_cloned(config)
        msg = update_templates_clone(config)
        echo(f"  {msg}", fg="green")
    except Exception as e:  # noqa: BLE001
        echo(f"  Failed to update templates: {e}", fg="red")

    # Check PyPI for plonecli updates
    echo("\nChecking for plonecli updates...", fg="green")
    try:
        from plonecli.updater import check_for_updates

        new_version = check_for_updates(force=True)
        if new_version:
            current = importlib.metadata.version("plonecli")
            echo(
                f"  New version available: {new_version} (current: {current})",
                fg="yellow",
            )
            echo("  Update with: uv tool upgrade plonecli", fg="yellow")
        else:
            echo("  plonecli is up to date.", fg="green")
    except Exception as e:  # noqa: BLE001
        echo(f"  Could not check for updates: {e}", fg="red")

    # Show templates info
    echo(f"\nTemplates: {get_templates_info(config)}", fg="green")


@cli.command()
@click.argument(
    "shell",
    required=False,
    type=click.Choice(["bash", "zsh", "fish"]),
)
@click.option("--install", is_flag=True, help="Install completion into your shell config")
def completion(shell, install):
    """Show or install shell completion.

    Without arguments, auto-detects your shell and prints the completion script.
    Use --install to append the activation line to your shell config file.
    """
    import os

    if shell is None:
        login_shell = os.path.basename(os.environ.get("SHELL", ""))
        if login_shell in ("bash", "zsh", "fish"):
            shell = login_shell
        else:
            raise click.UsageError(
                f"Could not detect shell (SHELL={os.environ.get('SHELL', '')!r}).\n"
                "Please specify one: plonecli completion bash|zsh|fish"
            )

    env_var = "_PLONECLI_COMPLETE"
    source_cmd = f"{env_var}={shell}_source plonecli"

    if not install:
        # Print the completion script to stdout
        import subprocess as _sp

        env = {**os.environ, env_var: f"{shell}_source"}
        result = _sp.run(["plonecli"], capture_output=True, text=True, env=env)
        if result.stdout:
            click.echo(result.stdout)
        else:
            # Fallback: print eval instruction
            click.echo(f'eval "$({source_cmd})"')
        return

    # --install: append eval line to the appropriate rc file
    rc_files = {
        "bash": os.path.expanduser("~/.bashrc"),
        "zsh": os.path.expanduser("~/.zshrc"),
        "fish": os.path.expanduser("~/.config/fish/completions/plonecli.fish"),
    }
    rc_file = rc_files[shell]

    if shell == "fish":
        # Fish uses a completions directory with the script itself
        os.makedirs(os.path.dirname(rc_file), exist_ok=True)
        eval_line = f"env {source_cmd} | source"
    else:
        eval_line = f'eval "$({source_cmd})"'

    # Check if already installed
    if os.path.exists(rc_file):
        with open(rc_file) as f:
            content = f.read()
        if "_PLONECLI_COMPLETE" in content:
            echo(f"Shell completion already configured in {rc_file}", fg="yellow")
            return

    with open(rc_file, "a") as f:
        f.write(f"\n# plonecli shell completion\n{eval_line}\n")

    echo(f"Shell completion installed in {rc_file}", fg="green")
    echo(f"Restart your shell or run: source {rc_file}", fg="green")


if __name__ == "__main__":
    cli()
