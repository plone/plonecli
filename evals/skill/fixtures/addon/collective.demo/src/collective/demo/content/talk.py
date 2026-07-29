from plone.dexterity.content import Container
from plone.supermodel import model
from zope.interface import implementer


class ITalk(model.Schema):
    """Schema for Talk."""

    # schema fields go here


@implementer(ITalk)
class Talk(Container):
    """Talk content type."""
