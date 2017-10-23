# -*- coding: utf-8 -*-
"""Custom exceptions."""

from click.exceptions import BadOptionUsage


class NotInPackageError(BadOptionUsage):
    """Raised if an option is not available outside a package."""

    message = 'The "{0}" command is only allowed within an existing package.'

    def __init__(self, option_name, ctx=None):
        message = self.message.format(option_name)
        BadOptionUsage.__init__(self, option_name, message, ctx)
        self.option_name = option_name
