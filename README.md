# tkouter

![](https://img.shields.io/pypi/v/tkouter.svg)
![](https://img.shields.io/pypi/pyversions/tkouter.svg)
[![Build Status](https://travis-ci.org/dokelung/tkouter.svg?branch=master)](https://travis-ci.org/dokelung/tkouter)
![Coveralls github](https://img.shields.io/coveralls/github/dokelung/tkouter.svg)

* [README 中文版](讀我.md)
* [PyConTw 2018 Slides 中文版](http://dokelung.github.io/tkouter)
* [Documents 中文版](https://tkouter.readthedocs.io/zh_TW/latest/)

## Taste it

```python
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
```

## Introduction

Creating GUI layout can be troublesome sometimes.
This package provides an easy way that you can use familar html to create layout.
Also, it can help you save lots of time on the settings of widgets, variable
management and more.
This package helps user to use MVC pattern to do GUI design.

## Installation

Use pip:

```sh
$ pip install tkouter
```

or you can clone this repo directly.

```sh
$ git clone https://github.com/dokelung/tkouter.git
```

## Requirements

* Python3.5 or later
* [Jinja2](http://jinja.pocoo.org/docs/2.10/)
* [lxml](http://lxml.de/)
* [tinycss](https://tinycss.readthedocs.io/en/latest/index.html)
* [cssslect](https://cssselect.readthedocs.io/en/latest/)

## Features

* Use html (xml) to layout
* Support css to config widgets
