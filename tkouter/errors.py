""" Module contains all errors
"""

__all__ = [
    'Error',
    'TagError',
    'TagUnRecognizedError',
    'DataNotExistError',
    'ClassNotExistError',
    'TagStartEndNotMatch',
    'TagInWrongScope',
    'TagStartEndTypeError',
]


class Error(Exception):
    """ Base-class for all exceptions raised by this module. """

class TagError(Error):
    """ There is a problem in the tag of layout html. """

class TagUnRecognizedError(TagError):
    """ There is unknown tag in tkouter layout html. """

class DataNotExistError(TagError):
    """ can not find the data specified in tag from data_context. """

class ClassNotExistError(TagError):
    """ can not find the class specified in tag from classes. """

class TagStartEndNotMatch(TagError):
    """ start tag does not match end tag"""

class TagInWrongScope(TagError):
    """ tag in wrong scope """

class TagStartEndTypeError(TagError):
    """ tag with wrong start end type """