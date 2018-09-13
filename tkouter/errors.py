""" Module contains all errors
"""

__all__ = [
    'Error',
    'TagError',
    'TagUnRecognizedError',
    'DataNotExistError',
    'TagInWrongScope',
]


class Error(Exception):
    """ Base-class for all exceptions raised by this module. """


class TagError(Error):
    """ There is a problem in the tag of layout html. """


class TagUnRecognizedError(TagError):
    """ There is unknown tag in tkouter layout html. """


class DataNotExistError(TagError):
    """ can not find the data specified in tag from data_context. """


class TagInWrongScope(TagError):
    """ tag in wrong scope """
