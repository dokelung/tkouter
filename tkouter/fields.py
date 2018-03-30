""" Module contains all available fields in tkout
"""

__all__ = [
    'StringField',
]


from tkinter import StringVar


class StringField:
    """ basic field which is implemented by StringVar
    """

    def __init__(self, *, default='', max_length=100):
        self._var = None
        self._default = default
        self._max_length = max_length

    @property
    def var(self):
        if self._var is None:
            self._var = StringVar()
            self._var.set(self._default)
        else:
            return self._var

    def __get__(self, instance, owner):
        return self.var.get()

    def __set__(self, instance, value):
        if len(self.var.get()) >= self._max_length:
            return
        self.var.set(value)