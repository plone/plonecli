"""CLI-level tests for the ``plonecli completion`` command.

This command appends to the user's shell rc files, so shell detection, the
script output path and append idempotency are all covered against a temp home.
"""

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from plonecli.cli import cli


@pytest.fixture(autouse=True)
def isolated_cli(tmp_path, monkeypatch):
    """A temp home, no project, and no network-backed update check."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(
        "plonecli.cli.load_config",
        lambda: MagicMock(templates_dir=str(tmp_path / "templates")),
    )
    monkeypatch.setattr("plonecli.cli.find_project_root", lambda: None)
    monkeypatch.setattr("plonecli.updater.check_for_updates", lambda *a, **k: None)
    return home


def _completed(stdout=""):
    return subprocess.CompletedProcess(args=["plonecli"], returncode=0, stdout=stdout)


@pytest.mark.parametrize("shell", ["bash", "zsh", "fish"])
def test_prints_the_completion_script(runner, shell):
    with patch(
        "subprocess.run", return_value=_completed("# generated completion\n")
    ) as mock_run:
        result = runner.invoke(cli, ["completion", shell])

    assert result.exit_code == 0, result.output
    assert "# generated completion" in result.output
    env = mock_run.call_args.kwargs["env"]
    assert env["_PLONECLI_COMPLETE"] == f"{shell}_source"


def test_falls_back_to_the_eval_line(runner):
    """If the generator produces nothing, print the activation line instead."""
    with patch("subprocess.run", return_value=_completed("")):
        result = runner.invoke(cli, ["completion", "bash"])

    assert result.exit_code == 0, result.output
    assert "_PLONECLI_COMPLETE=bash_source plonecli" in result.output


@pytest.mark.parametrize("shell", ["bash", "zsh", "fish"])
def test_detects_the_login_shell(runner, monkeypatch, shell):
    monkeypatch.setenv("SHELL", f"/usr/bin/{shell}")

    with patch("subprocess.run", return_value=_completed("")) as mock_run:
        result = runner.invoke(cli, ["completion"])

    assert result.exit_code == 0, result.output
    assert mock_run.call_args.kwargs["env"]["_PLONECLI_COMPLETE"] == f"{shell}_source"


@pytest.mark.parametrize("shell_env", ["", "/bin/tcsh"])
def test_undetectable_shell_asks_for_one(runner, monkeypatch, shell_env):
    monkeypatch.setenv("SHELL", shell_env)

    result = runner.invoke(cli, ["completion"])

    assert result.exit_code != 0
    assert "bash|zsh|fish" in result.output


def test_rejects_an_unsupported_shell(runner):
    result = runner.invoke(cli, ["completion", "tcsh"])

    assert result.exit_code != 0


@pytest.mark.parametrize(
    ("shell", "rc_relpath"),
    [("bash", ".bashrc"), ("zsh", ".zshrc")],
)
def test_install_appends_the_eval_line(runner, isolated_cli, shell, rc_relpath):
    """Also a regression for the flag-after-argument form.

    The top-level group is chained, which disables interspersed args, so
    ``plonecli completion bash --install`` used to fail with "No such option:
    --install".
    """
    rc_file = isolated_cli / rc_relpath
    rc_file.write_text("# existing user config\n")

    result = runner.invoke(cli, ["completion", shell, "--install"])

    assert result.exit_code == 0, result.output
    content = rc_file.read_text()
    assert "# existing user config" in content
    assert f'eval "$(_PLONECLI_COMPLETE={shell}_source plonecli)"' in content
    assert str(rc_file) in result.output


def test_install_creates_the_fish_completions_file(runner, isolated_cli):
    result = runner.invoke(cli, ["completion", "fish", "--install"])

    assert result.exit_code == 0, result.output
    rc_file = isolated_cli / ".config/fish/completions/plonecli.fish"
    assert "env _PLONECLI_COMPLETE=fish_source plonecli | source" in rc_file.read_text()


def test_install_creates_a_missing_rc_file(runner, isolated_cli):
    result = runner.invoke(cli, ["completion", "bash", "--install"])

    assert result.exit_code == 0, result.output
    assert "_PLONECLI_COMPLETE" in (isolated_cli / ".bashrc").read_text()


@pytest.mark.parametrize("shell", ["bash", "zsh", "fish"])
def test_install_is_idempotent(runner, isolated_cli, shell):
    """A second --install must not append a duplicate line to the rc file."""
    first = runner.invoke(cli, ["completion", shell, "--install"])
    assert first.exit_code == 0, first.output
    rc_files = {
        "bash": isolated_cli / ".bashrc",
        "zsh": isolated_cli / ".zshrc",
        "fish": isolated_cli / ".config/fish/completions/plonecli.fish",
    }
    after_first = rc_files[shell].read_text()

    second = runner.invoke(cli, ["completion", shell, "--install"])

    assert second.exit_code == 0, second.output
    assert "already configured" in second.output
    assert rc_files[shell].read_text() == after_first
    assert after_first.count("_PLONECLI_COMPLETE") == 1
