.. tkouter documentation master file, created by
   sphinx-quickstart on Mon Apr  9 03:15:41 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

tkouter
===================================

.. image:: https://img.shields.io/pypi/v/tkouter.svg
    :target: https://pypi.python.org/pypi/tkouter


.. image:: https://img.shields.io/pypi/pyversions/Django.svg
    :target: https://pypi.python.org/pypi/tkouter


.. image:: https://travis-ci.org/dokelung/tkouter.svg?branch=master
    :target: https://travis-ci.org/dokelung/tkouter


.. image:: https://img.shields.io/coveralls/github/dokelung/tkouter.svg
    :target: https://coveralls.io/github/dokelung/tkouter

**tkouter** is a python package for creating tkinter layout by html (xml).


Installation
------------

::

    $ pip install tkouter


Taste it
--------

::

    from tkinter import Tk, messagebox
    from tkouter import *


    class HelloWorld(TkOutWidget):
        layout = """
            <html>
                <head>
                    <title> hello world </title>
                </head>
                <body>
                    <button width="20" command="{self.hello}">
                        Click
                    </button>
                </body>
            </html>"""

        def hello(self):
            messagebox.showinfo('welcome to tkouter', 'hello world')


    if __name__ == '__main__':
        root = Tk()
        hl = HelloWorld(root)
        hl.pack()
        root.mainloop()


Contents
--------

.. toctree::
   :maxdepth: 3

   tutorial
   core