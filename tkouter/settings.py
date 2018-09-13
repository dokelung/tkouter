__all__ = [
    'WIDGETS',
    'LOADER',
]


from tkinter import *
from tkinter import ttk

from jinja2 import FileSystemLoader


WIDGETS = {
    # widget tag type
    'label': Label,
    'entry': Entry,
    'button': Button,
    'spinbox': Spinbox,
    'combobox': ttk.Combobox,
    'listbox': Listbox,
    'treeview': ttk.Treeview,
    'notebook': ttk.Notebook,
    'radiobutton': ttk.Radiobutton,
    'checkbutton': ttk.Checkbutton,
    # frame tag type
    'frame': Frame,
    'labelframe': ttk.LabelFrame,
    # head tag type
    'menu': Menu,
}

LOADER = FileSystemLoader('./')
