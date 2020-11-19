# -*- coding: utf-8 -*-
"""Configure mrbob."""
from __future__ import absolute_import

from bobtemplates.plone.base import echo
from configparser import RawConfigParser
from functools import singledispatch
from mrbob.configurator import SkipQuestion

import codecs
import os
import sys


home_path = os.path.expanduser("~")


@singledispatch
def safe_string(data):
    return data


# the bytes param here is only needed for py3.6:
@safe_string.register(bytes)
def _(data: bytes):
    try:
        return data.decode("utf-8")
    except TypeError:
        return data


@singledispatch
def safe_bytes(data):
    return data


# the str param here is only needed for py3.6:
@safe_bytes.register(str)
def _(data: str):
    try:
        return data.encode("utf-8")
    except TypeError:
        return data


def configoverride_warning_post_question(configurator, question, answer):
    if answer.lower() != "y":
        print("Abort!")
        sys.exit(0)
    return answer


def mrbob_config_exists(configurator, answer):
    target_directory = home_path
    file_name = u".mrbob"
    file_list = os.listdir(target_directory)
    if file_name not in file_list:
        raise SkipQuestion(
            u"No existing mrbob config file found, so we skip this question."
        )


def check_git_disabled(configurator, answer):
    if configurator.variables["configure_mrbob.package.git.disabled"]:
        raise SkipQuestion(u"GIT is disabled, so we skip git related questions.")


def get_mrbob_config_variable(varname, dirname):
    """Checks mrbob config of given variable from ~/.mrbob file """
    config = RawConfigParser()
    file_name = ".mrbob"
    config_path = dirname + "/" + file_name
    file_list = os.listdir(dirname)
    if file_name not in file_list:
        return
    config.readfp(codecs.open(config_path, "r", "utf-8"))
    if not config.sections():
        return
    if config.has_option("variables", varname):
        return config.get("variables", varname)
    else:
        return


def pre_username(configurator, question):
    """Get username from mrbob config file."""
    default = get_mrbob_config_variable("author.name", home_path)
    if default and question:
        question.default = default


def pre_email(configurator, question):
    """Get author email from mrbob config file."""
    default = get_mrbob_config_variable("author.email", home_path)
    if default and question:
        question.default = default


def pre_github_username(configurator, question):
    """Get Github username from mrbob config file."""
    default = get_mrbob_config_variable("author.github.user", home_path)
    if default and question:
        question.default = default


def pre_plone_version(configurator, question):
    """Get plone version from mrbob config file."""
    default = get_mrbob_config_variable("plone.version", home_path)
    if default and question:
        question.default = default


def pre_package_git_init(configurator, question):
    """Get git init setting from mrbob config file."""
    default = get_mrbob_config_variable("package.git.init", home_path)
    if default and question:
        question.default = default


def pre_package_git_autocommit(configurator, question):
    """Get git autocommit setting from mrbob config file."""
    default = get_mrbob_config_variable("package.git.autocommit", home_path)
    if default and question:
        question.default = default


def pre_package_git_disable(configurator, question):
    """Get git disabled setting from mrbob config file."""
    default = get_mrbob_config_variable("package.git.disabled", home_path)
    if default and question:
        question.default = default


def pre_package_venv_disabled(configurator, question):
    """Get venv disabled setting from mrbob config file."""
    default = get_mrbob_config_variable("package.venv.disabled", home_path)
    if default and question:
        question.default = default


def is_venv_disabled():
    """Get venv disabled setting from mrbob config, for plonecli usage."""
    flag = get_mrbob_config_variable("package.venv.disabled", home_path) == "y"
    return flag


def generate_mrbob_ini(configurator, directory_path, answers):
    file_name = u".mrbob"
    file_path = directory_path + "/" + file_name
    template = """[mr.bob]
verbose = False

[variables]
# all variables answered here, will not being ask again:

author.name = {0}
author.email = {1}
author.github.user = {2}
package.venv.disabled = {3}
package.git.disabled = {4}
""".format(
        safe_string(answers["author.name"]),
        safe_string(answers["author.email"]),
        safe_string(answers["author.github.user"]),
        safe_string(answers["package.venv.disabled"]),
        safe_string(answers["package.git.disabled"]),
    )
    if not configurator.variables["configure_mrbob.package.git.disabled"]:
        template = (
            template
            + """package.git.init = {0}
package.git.autocommit = {1}
""".format(
                safe_string(answers["package.git.init"]),
                safe_string(answers["package.git.autocommit"]),
            )
        )
    template = (
        template
        + """
[defaults]
# set your default values for questions here, they questions are still being ask
# but with your defaults:

plone.version = {0}
#dexterity_type_global_allow = n
#dexterity_type_filter_content_types = y
#dexterity_type_activate_default_behaviors = n
#dexterity_type_supermodel = y
#python.version = python3.7
""".format(
            safe_string(answers["plone.version"])
        )
    )
    with open(file_path, "w") as f:
        f.write(template)


def post_render(configurator, target_directory=None):
    mrbob_config = {}
    mrbob_config["author.name"] = safe_string(
        configurator.variables["configure_mrbob.author.name"]
    )
    mrbob_config["author.email"] = safe_string(
        configurator.variables["configure_mrbob.author.email"]
    )
    mrbob_config["author.github.user"] = safe_string(
        configurator.variables["configure_mrbob.author.github.user"]
    )
    mrbob_config["package.venv.disabled"] = configurator.variables[
        "configure_mrbob.package.venv.disabled"
    ]
    if not configurator.variables["configure_mrbob.package.git.disabled"]:
        mrbob_config["package.git.disabled"] = "n"
        mrbob_config["package.git.init"] = configurator.variables[
            "configure_mrbob.package.git.init"
        ]
        mrbob_config["package.git.autocommit"] = configurator.variables[
            "configure_mrbob.package.git.autocommit"
        ]
    else:
        mrbob_config["package.git.disabled"] = "y"
    mrbob_config["plone.version"] = safe_string(
        configurator.variables["configure_mrbob.plone.version"]
    )
    if not target_directory:
        configurator.target_directory = home_path
        target_directory = configurator.target_directory
    generate_mrbob_ini(configurator, target_directory, mrbob_config)
    echo(
        u"\nMrbob's settings have been saved to {0}/.mrbob\n".format(target_directory),
        msg_type="info",
    )
