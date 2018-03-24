# tkouter.py
""" Module for creating tkinter layout by html.

Creating GUI layout can be troublesome sometimes.
This module provides a easy way that you can use familar html to create layout.
Also, it can help you save lots of time on the settings of widgets, variable
management and more.

This module helps user to use MVC pattern to do GUI design.

Available Classes:
- TkOutWidget: Main class of tkouter module, you can inherit it to make your
               own widget by using html-based layout
"""

_util = [
    'WIDGETS',
    'LOADER',
]

_classes = [
    'TkOutWidget',
    'TkOutModel',
]

_errors = [
    'Error',
    'TagError',
    'TagLossAttributeError',
    'TagUnRecognizedError',
    'DataNotExistError',
    'ClassNotExistError',
    'HeadLossReferWindowError',
    'CallBackLossFunctionError',
]

__all__ = _util + _classes + _errors


import html.parser
from tkinter import *
from tkinter import ttk
from jinja2 import Environment, FileSystemLoader
import inspect

# util
WIDGETS = {
    # widget tag type
    'label': Label,
    'entry': Entry,
    'button': Button,
    'radiobutton': ttk.Radiobutton,
    'checkbutton': ttk.Checkbutton,
    'spinbox': Spinbox,
    'combobox': ttk.Combobox,
    'listbox': Listbox,
    'treeview': ttk.Treeview,
    'notebook': ttk.Notebook,
    # frame tag type
    'frame': Frame,
    'labelframe': ttk.LabelFrame,
    # head tag type
    'menu': Menu,
}

LOADER = FileSystemLoader('./')

# tkouter errors
class Error(Exception):
    """ Base-class for all exceptions raised by this module. """

class TagError(Error):
    """ There is a problem in the tag of layout html. """

class TagLossAttributeError(TagError):
    """ Standard tkouter tag losses 'name'/'type' attribute. """

class TagUnRecognizedError(TagError):
    """ There is unknown tag in tkouter layout html. """

class DataNotExistError(TagError):
    """ can not find the data specified in tag from data_context. """

class ClassNotExistError(TagError):
    """ can not find the class specified in tag from classes. """

class HeadLossReferWindowError(TagError):
    """ head tag losses reference window. """

class CallBackLossFunctionError(TagError):
    """ callback tag losses function attribute. """


# tkouter main classes
class TkOutWidget(Frame):
    """ Design a user-defined widget with html-based layout

    User could define a html-based layout widget just by inheriting this class.
    Subclass may override some class attributes to make its own widget or layout.

    Public attributes:
    - widgets: available tkinter(tkouter) widgets.
               (dictionary: widget_tagname/widget_class)
    - classes: widget classes which provides several uniform interfaces to
               configure widgets. (class)
    - html: layout html (string)
    - htmlfile: file of layout html, if htmlfile is given then attribute html
                will be ignored by tkouter (html file)
    - str_context: used to render the htmlfile if it is a template (dictionary)
    - data_context: used to query the data when building a widget. (dictionary)
    """

    widgets = WIDGETS
    classes = None
    loader = LOADER
    html = ""
    htmlfile = None
    str_context = {}
    data_context = None

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        if self.data_context is None:
            self.data_context = {'self': self}
        self.build()

    def build(self):
        """ create layout and define widget attribute by tkouter html """
        self.env = Environment(loader=self.loader)
        if self.htmlfile:
            template = self.env.get_template(self.htmlfile)
            self.html = template.render(self.str_context)
        creator = TkOutWidgetCreator(self)
        creator.feed(self.html)

    def destruct(self):
        """ clean the layout(unpack) and delete related widget attributes """
        raise NotImplementedError


class TkOutWidgetCreator(html.parser.HTMLParser):
    """ Create tkouter widget layout by html

    It is the core engine of html-based layout.
    User should not use it directly.
    """

    skip_tags = ['html']
    pack_tags = ['top', 'bottom', 'left', 'right']

    def __init__(self, tkout_widget):
        super().__init__()
        self._tkoutw = tkout_widget
        self._scope = ''

    @property
    def _parent(self):
        return self._parents[-1]

    @_parent.setter
    def _parent(self, next_parent):
        self._parents.append(next_parent)

    @property
    def _packtype(self):
        return self._packtypes[-1]

    @_packtype.setter
    def _packtype(self, packtype):
        self._packtypes.append(packtype)

    def _init_head(self):
        """ settings for handling elements between <head> tag """
        self._parents = []

    def _init_body(self):
        """ settings for handling elements between <body> tag """
        self._parents = [self._tkoutw]
        self._packtypes = ['top']

    def _backtrack(self):
        """ backtrack to the upper level """
        if self._scope == 'head':
            self._parents.pop(-1)
        elif self._scope == 'body':
            self._parents.pop(-1)
            self._packtypes.pop(-1)

    def _parseattrs(self, attrs):
        """ parse tag's attributes

        given:
            attrs: tuple list, each tuple is a 2-elements pair (attr, value)
        return:
            tuple: (name, widget, options, sp_options)
            - name: variable name (string)
            - widget: widget class name (class, type)
            - options: widget options (dictionary)
            - sp_options: special options (dictionary)
        """
        name, widget, options, sp_options = (None, None, {}, {})
        for attr, value in attrs:
            if attr == 'name':
                name = value
            elif attr == 'type':
                widget = self._tkoutw.widgets.get(value, None)
            elif attr == 'class':
                if not hasattr(self._tkoutw.classes, value):
                    msg = 'class "{}" does not exist'
                    raise ClassNotExist(msg.format(value))
                cls = getattr(self._tkoutw.classes, value) 
                for cls_attr, cls_value in cls.__dict__.items():
                    if cls_attr.startswith('_'):
                        continue
                    options[cls_attr] = str(cls_value)
            elif attr.startswith('sp-'):
                attr = attr[3:]
                sp_options[attr] = value
            else:
                options[attr] = value
        options = self._handle_options(options)
        return name, widget, options, sp_options

    def _handle_options(self, options):
        """ handle tag(widet) options

        For the simple type of options, user just give its value(string) in the
        layout html tags. Note that, string here is okay for interger, float,
        ...etc because tkinter will transform all types to string in tcl level
        execution.

        Some options are special or complicated, we should pre-set their values
        and assign to some variables then specify the variable in symbol "{" and
        "}" as option value.
        """
        modified_options = {}
        for name, value in options.items():
            if value.startswith('{') and value.endswith('}'):
                value = value[1:-1].strip()
                attrs = value.split('.')
                dkey, *attrs = attrs
                try:
                    data = self._tkoutw.data_context[dkey]
                    for attr in attrs:
                        if hasattr(data, attr):
                            data = getattr(data, attr)
                        elif attr in data:
                            data = data[attr]
                    modified_options[name] = data
                except:
                    msg = 'data "{}" does not exist'
                    raise DataNotExistError(msg.format(value))
            else:
                modified_options[name] = value
        return modified_options

    def handle_starttag(self, tag, attrs):
        """ handle tag in the beginning of it """
        if tag in self.skip_tags:
            return
        elif tag == 'callback':
            self._handle_callback(tag, attrs)
            return
        elif tag == 'head':
            self._scope = 'head'
            self._init_head()
        elif tag == 'body':
            self._scope = 'body'
            self._init_body()
            return
        if self._scope == 'head':
            self._handle_head_starttag(tag, attrs)
        elif self._scope == 'body':
            self._handle_body_starttag(tag, attrs)

    def _handle_callback(self, tag, attrs):
        """ handle callback tag """
        name, Widget, options, sp_options = self._parseattrs(attrs)
        if 'function' not in options:
            msg = 'loss "function" attribute in tag <{}>'
            raise CallBackLossFunctionError(msg.format(tag))
        cb = options['function']
        del options['function']
        cb(**options)

    def _handle_head_starttag(self, tag, attrs):
        """ handle head tag in the beginning of it """
        # parse attrs
        name, Widget, options, sp_options = self._parseattrs(attrs)
        if tag == 'head':
            if 'window' not in options:
                msg = 'loss "window" attribute in tag <{}>'
                raise HeadLossReferWindowError(msg.format(tag))
            self._window = options['window']
            self._parent = options['window']
        elif tag == 'menu':
            if name is None or Widget is None:
                msg = 'loss "name" or "type" attribute in tag <{}>'
                raise TagLossAttributeError(msg.format(tag))
            # menu
            if self._parent is self._window: #toplevel menu
                if not self._window['menu']:
                    menu = Widget(self._parent, **options)
                    setattr(self._tkoutw, name, menu)
                    self._window['menu'] = menu
                # propogate
                self._parent = menu
            else: # cascade menu
                menu = Widget(self._parent, **options)
                setattr(self._tkoutw, name, menu)
                self._parent.add_cascade(menu=menu, **sp_options)
                # propogate
                self._parent = menu
        else:
            msg = 'unrecognized tag <{}>'
            raise TagUnRecognizedError(msg.format(tag))

    def _handle_body_starttag(self, tag, attrs):
        """ handle body tag in the beginning of it """
        # parse attrs
        name, Widget, options, sp_options = self._parseattrs(attrs)
        if name is None or Widget is None:
            msg = 'loss "name" or "type" attribute in tag <{}>'
            raise TagLossAttributeError(msg.format(tag))
        # pack side
        if 'side' in sp_options:
            side = sp_options['side']
            del sp_options['side']
        else:
            side = self._packtype
        # create frame or widget
        if tag in self.pack_tags:
            container = Widget(self._parent, **options)
            setattr(self._tkoutw, name, container)
            container.pack(side=side, **sp_options)
            # propogate
            self._parent = container
            self._packtype = tag
        elif tag == 'widget':
            widget = Widget(self._parent, **options)
            setattr(self._tkoutw, name, widget)
            widget.pack(side=side, **sp_options)
        else:
            msg = 'unrecognized tag <{}>'
            raise TagUnRecognizedError(msg.format(tag))

    def handle_endtag(self, tag):
        """ handle tag in the end of it """
        if tag in self.skip_tags + ['head', 'body']:
            return
        if self._scope == 'head':
            self._handle_head_endtag(tag)
        elif self._scope == 'body':
            self._handle_body_endtag(tag)

    def _handle_head_endtag(self, tag):
        """ handle head tag in the end of it """
        if tag == 'menu':
            self._backtrack()
        else:
            msg = 'unrecognized tag </{}>'
            raise TagUnRecognizedError(msg.format(tag))

    def _handle_body_endtag(self, tag):
        """ handle body tag in the end of it """
        if tag in self.pack_tags:
            self._backtrack()
        else:
            msg = 'unrecognized tag </{}>'
            raise TagUnRecognizedError(msg.format(tag))


class TkOutModel:

    def __init__(self):
        attrs = inspect.getmembers(self, lambda a: not(inspect.isroution(a)))
        attrs = [a for a in attrs if not(a[0].startswith('__') and a[0].endswith('__'))]
        for a in attrs:
            attr = getattr(self, a)
            setattr(self, a, property(lambda attr: attr.get()))
