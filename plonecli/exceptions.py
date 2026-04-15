"""Custom exceptions."""

from __future__ import annotations

from click.exceptions import BadOptionUsage, NoSuchOption


class NotInPackageError(BadOptionUsage):
    """Raised if a command is used outside a Plone project."""

    message = 'The "{0}" command is only allowed within an existing package.'

    def __init__(self, option_name, ctx=None):
        message = self.message.format(option_name)
        super().__init__(option_name, message, ctx)
        self.option_name = option_name


class NoSuchValue(NoSuchOption):
    """Raised if an unknown template name is provided."""

    message = 'No such value: "{0}".'

    def __init__(self, option_name, value, possibilities=None, ctx=None):
        message = self.message.format(value)
        super().__init__(option_name, message, possibilities, ctx)
        self.option_name = option_name
        self.possibilities = possibilities
