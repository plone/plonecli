# -*- coding: utf-8 -*-
"""Configure mrbob."""
from __future__ import absolute_import

from bobtemplates.plone.base import echo
from configparser import RawConfigParser
from functools import singledispatch
from mrbob.configurator import SkipQuestion

import codecs
import os


home_path = os.path.expanduser("~")


@singledispatch
def safe_string(data):
    return data


@safe_string.register
def _(data: bytes):
    try:
        return data.decode("utf-8")
    except TypeError:
        return data


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
    file_list = os.listdir(directory_path)
    if file_name not in file_list:
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
    else:
        # get config file contents
        lines = [
            line.rstrip("\n") for line in codecs.open(file_path, "r", "utf-8")
        ]  # NOQA: E501
        commented_settings = [
            line for line in lines if line and line[0] == "#"
        ]  # NOQA: E501
        config = RawConfigParser()
        # to explicitly convert `key` to str so that we don't get error in
        # .join() of `value`(of type str) and `key`(of type unicode)
        # in RawConfigParser.write() method
        config.optionxform = str
        config.readfp(codecs.open(file_path, "r", "utf-8"))
        if not config.has_section("variables"):
            config.add_section("variables")
        for key, value in answers.items():
            config.set("variables", key, value)
        with open(file_path, "w") as mrbob_config_file:
            config.write(mrbob_config_file)
        # append commented settings at the end
        with codecs.open(file_path, "a", "utf-8") as mrbob_config_file:
            mrbob_config_file.writelines(commented_settings)


def post_render(configurator, target_directory=None):
    mrbob_config = {}
    mrbob_config["author.name"] = configurator.variables[
        "configure_mrbob.author.name"
    ].encode("utf-8")
    mrbob_config["author.email"] = configurator.variables[
        "configure_mrbob.author.email"
    ].encode("utf-8")
    mrbob_config["author.github.user"] = configurator.variables[
        "configure_mrbob.author.github.user"
    ].encode("utf-8")
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
    mrbob_config["plone.version"] = configurator.variables[
        "configure_mrbob.plone.version"
    ].encode("utf-8")
    if not target_directory:
        configurator.target_directory = home_path
        target_directory = configurator.target_directory
    generate_mrbob_ini(configurator, target_directory, mrbob_config)
    echo(
        u"\nMrbob's settings have been saved to {0}/.mrbob\n".format(target_directory),
        msg_type="info",
    )
