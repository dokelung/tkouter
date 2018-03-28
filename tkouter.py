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

_gvars = [
    'WIDGETS',
    'LOADER',
    'DEBUG',
]

_apis = [
    'register',
]

_classes = [
    'TkOutWidget',
    'TkOutModel',
]

_errors = [
    'Error',
    'TagError',
    'TagUnRecognizedError',
    'DataNotExistError',
    'ClassNotExistError',
    'TagStartEndNotMatch',
    'TagInWrongScope',
    'TagStartEndTypeError',
]

__all__ = _gvars + _apis + _classes + _errors


import html.parser
from tkinter import *
from tkinter import ttk
import inspect

from jinja2 import Environment, FileSystemLoader


# ========================================================================
# global variables
# ========================================================================
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

DEBUG = True


# ========================================================================
# tkouter APIs
# ========================================================================
def register(name):
    """ function to add additional widget to BODY_WIDGETS
    usage: 
        register('my_widget_name')(MyWidgetClass) 
    """
    def _register(widget_cls):
        WIDGETS[name] = widget_cls
        return widget_cls
    return _register


# ========================================================================
# tkouter errors
# ========================================================================
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


# ========================================================================
# tkouter classes
# ========================================================================
class TkOutWidget(Frame):
    """ Design a user-defined widget with html-based layout

    User could define a html-based layout widget just by inheriting this class.
    Subclass may override some class attributes to make its own widget or layout.

    Public attributes:
    - widgets: available widgets (dictionary)
    - layout: layout html or layout-html file name (string)
    - classes: widget classes which provides several uniform interfaces to
               configure widgets. (class)
    - context: used to render the layout if it is a template (dictionary)
    - data_context: used to query the data when building a widget. (dictionary)
    """
    widgets = WIDGETS
    loader = LOADER
    layout = None
    classes = None
    context = {}
    data_context = None

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        if self.data_context is None:
            self.data_context = {'self': self}
        user_widgets = self.widgets
        self.widgets = {}
        self.widgets.update(WIDGETS)
        self.widgets.update(user_widgets)
        self._build()

    def _build(self):
        """ create layout and define widget attribute by tkouter html """
        self.env = Environment(loader=self.loader)
        if self.layout:
            template = self.env.get_template(self.layout)
            self._html = template.render(self.context)
        creator = TkOutWidgetCreator(self)
        creator.feed(self._html)

    def _destruct(self):
        """ clean the layout(unpack) and delete related widget attributes """
        raise NotImplementedError("TkOutWidget._destruct")


class TkOutTag:
    """ Model a tkouter tag """

    _widget_type_counter = {}

    def __init__(self, creater, tag_name, attrs, se_type):
        # common attributes
        self._tkoutw = creater._tkoutw
        self._tag_name = tag_name
        self._parent = self if self.is_html else creater._current_tag
        self._attrs = attrs
        self._attrs_dic = dict(attrs)
        self._se_type = se_type
        self._widget = None

        # special attributes
        self._menu_entry_count = 0

        # check
        self._check_valid()
        self._check_se()
        self._check_scope()

    def __str__(self):
        return '<{}>'.format(self._tag_name)

    def __repr__(self):
        return 'TkOutTag({}, {}, {}, {})'.format('<TkOutWidgetCreator>', self._tag_name, self._attrs, self._se_type)

    def _check_valid(self):
        if not (self.is_html or self.is_scope or self.can_under_head or self.can_under_body):
            msg = 'unrecognized tag <{}>'
            raise TagUnRecognizedError(msg.format(self._tag_name))

    def _check_se(self):
        if self.is_startend and not self.can_be_startend:
            msg = 'tag <{}/> can not be a startend tag'
            raise TagStartEndTypeError(msg.format(self._tag_name))

    def _check_scope(self):
        if self.is_html:
            assert(self._parent.is_html)
        elif self.is_under_head and not self.can_under_head:
            msg = 'tag <{}> should be under scope tag <head>'
            raise TagInWrongScope(msg.format(self._tag_name))
        elif self.is_under_menu and not self.can_under_menu:
            msg = 'tag <{}> should be under scope tag <menu>'
            raise TagInWrongScope(msg.format(self._tag_name))
        elif self.is_under_body and not self.can_under_body:
            msg = 'tag <{}> should be under scope tag <body>'
            raise TagInWrongScope(msg.format(self._tag_name))

    def _handle_options(self, options):
        """ handle tag options
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

    @property
    def is_start(self):
        return self._se_type == 'start'

    @property
    def is_end(self):
        return self._se_type == 'end'

    @property
    def is_startend(self):
        return self._se_type == 'startend'

    @property
    def is_html(self):
        return self._tag_name == 'html'

    @property
    def is_head(self):
        return self._tag_name == 'head'

    @property
    def is_body(self):
        return self._tag_name == 'body'

    @property
    def is_scope(self):
        return self.is_head or self.is_body

    @property
    def is_side(self):
        return self._tag_name in ['top', 'bottom', 'left', 'right']

    @property
    def is_menu(self):
        return self._tag_name == 'menu'

    @property
    def is_top_menu(self):
        return self.is_menu and (not self._parent.is_menu)

    @property
    def is_sub_menu(self):
        return self.is_menu and self._parent.is_menu

    @property
    def is_under_head(self):
        if self._parent.is_html:
            return False
        return self._parent.is_head or self._parent.is_under_head

    @property
    def is_under_menu(self):
        return self._parent.is_menu

    @property
    def is_under_body(self):
        if self._parent.is_html:
            return False
        return self._parent.is_body or self._parent.is_under_body

    @property
    def can_under_head(self):
        return self._tag_name in ['title'] or self.is_menu or self.can_under_menu

    @property
    def can_under_menu(self):
        return self._tag_name in ['separator', 'command', 'radiobutton', 'checkbutton'] or self.is_sub_menu

    @property
    def can_under_body(self):
        return self._tag_name in self._tkoutw.widgets or self.is_side

    @property
    def can_be_startend(self):
        if self.is_menu:
            return False
        return self._tag_name in self._tkoutw.widgets or self._tag_name in ['separator', 'command', 'radiobutton', 'checkbutton']

    @property
    def has_no_widget_type(self):
        return self.is_html or self.is_scope or self._tag_name in ['title']

    @property
    def has_widget_type(self):
        return self.widget_type is not None

    @property
    def has_widget_name(self):
        return self.widget_name is not None

    @property
    def has_widget_cls(self):
        return self.widget_cls is not None

    @property
    def has_class_options(self):
        return bool(self.class_options)

    @property
    def has_options(self):
        return bool(self.options)

    @property
    def has_sp_options(self):
        return bool(self.sp_options)

    @property
    def has_pack_side(self):
        return self.pack_side is not None

    @property
    def has_widget(self):
        return self.is_under_body or self.is_menu

    @property
    def widget_type(self):
        if self.has_no_widget_type:
            t = None
        elif self.is_side:
            t = self._attrs_dic.get('type', 'frame')
        else:
            t = self._attrs_dic.get('type', self._tag_name)
        return t

    @property
    def widget_name(self):
        if self.has_widget_cls:
            name = self._attrs_dic.get('name', None)
            if name is None:
                if self.widget_type in self._widget_type_counter:
                    self._widget_type_counter[self.widget_type] += 1
                else:
                    self._widget_type_counter[self.widget_type] = 0
                name = self.widget_type + '_' + str(self._widget_type_counter[self.widget_type])
        else:
            name = None
        return name

    @property
    def widget_cls(self):
        return self._tkoutw.widgets.get(self.widget_type, None)

    @property
    def class_options(self):
        options = {}
        clss = self._attrs_dic.get('class', None)
        if clss:
            cls_lst = clss.split()
            for cname in cls_lst:
                if not hasattr(self._tkoutw.classes, cname):
                    msg = 'class "{}" does not exists'
                    raise ClassNotExist(msg.format(cname))
                c = getattr(self._tkoutw.classes, cname)
                for cls_attr, cls_value in c.__dict__.items():
                    if cls_attr.startswith('_'):
                        continue
                    options[cls_attr] = str(cls_value)
        return options

    @property
    def options(self):
        options = self.class_options
        for attr, value in self._attrs:
            if attr in ['name', 'type', 'class'] or attr.startswith('sp-'):
                continue
            else:
                options[attr] = value
        return self._handle_options(options)

    @property
    def sp_options(self):
        options = {}
        for attr, value in self._attrs:
            if attr.startswith('sp-'):
                attr = attr[3:]
                options[attr] = value
        return options

    @property
    def pack_side(self):
        side = None
        if self.is_under_body:
            side = self.sp_options.get('side', None)
            if side is None:
                if self._parent.is_body:
                    side = 'top'
                else:
                    side = self._parent._tag_name
                    assert(side in ['top', 'bottom', 'left', 'right'])
        return side

    @property
    def parent_widget(self):
        if self._parent.has_widget:
            return self._parent.widget
        else:
            if self._parent.is_head:
                return self._tkoutw.parent
            elif self._parent.is_body:
                return self._tkoutw
        return None

    @property
    def widget(self):
        if self._widget is None:
            if self.is_under_body:
                self._widget = self.widget_cls(self.parent_widget, **self.options)
                setattr(self._tkoutw, self.widget_name, self._widget)
            elif self.is_menu:
                self._widget = self.widget_cls(self.parent_widget)
                setattr(self._tkoutw, self.widget_name, self._widget)
        return self._widget

    def display(self):
        if self.is_sub_menu:
            self.parent_widget.add_cascade(menu=self.widget, **self.options)
        elif self.is_under_menu:
            self.parent_widget.add(itemType=self.widget_type, **self.options)
            self._parent._menu_entry_count += 1
        elif self.is_top_menu:
            self.parent_widget['menu'] = self.widget
        elif self.is_under_body:
            self.widget.pack(side=self.pack_side, **self.sp_options)

    def re_display(self, **update_options):
        options = self.options
        options.update(update_options)
        if self.is_sub_menu:
            raise NotImplementedError("TkOutTag.re_display::is_sub_menu")
        elif self.is_under_menu:
            self.parent_widget.delete(self._parent._menu_entry_count-1)
            self.parent_widget.add(itemType=self.widget_type, **options)
        elif self.is_top_menu:
            raise NotImplementedError("TkOutTag.re_display::is_top_menu")
        elif self.is_under_body:
            raise NotImplementedError("TkOutTag.re_display::is_under_body")


class TkOutWidgetCreator(html.parser.HTMLParser):
    """ Create tkouter widget layout by html

    It is the core engine of html-based layout.
    User should not use it directly.
    """

    def __init__(self, tkout_widget):
        super().__init__()
        self._tkoutw = tkout_widget
        self._tag_stack = []

    @property
    def _current_tag(self):
        if self._tag_stack:
            return self._tag_stack[-1]
        else:
            return None

    @_current_tag.setter
    def _current_tag(self, tag):
        if tag is None:
            self._tag_stack.pop(-1)
        else:
            self._tag_stack.append(tag)

    def _show_current_tag(self, se_type, tag_or_data, attrs=None):
        """ debug function """
        if not DEBUG:
            return
        indent = len(self._tag_stack) * 4 * ' ' if se_type in ['start', 'startend', 'data'] else (len(self._tag_stack)-1) * 4 * ' '
        if se_type in ['start', 'end', 'startend']:
            tag = tag_or_data
            bslash = '/' if se_type=='end' else ''
            eslash = ' /' if se_type=='startend' else ''
            if attrs:
                attrs = ' ' + ', '.join(['{}="{}"'.format(attr, value) for attr, value in attrs])
            else:
                attrs = ''
            temp = '<{bslash}{tag}{attrs}{eslash}>'
            print(indent + temp.format(bslash=bslash, tag=tag, attrs=attrs, eslash=eslash))
        else:
            data = tag_or_data
            data = data.strip()
            if data:
                print(indent + data)

    def handle_data(self, data):
        """ handle data """
        self._show_current_tag('data', data)
        if self._current_tag._tag_name == 'title':
            self._tkoutw.parent.title(data)
        elif self._current_tag.is_under_menu and self._current_tag.can_be_startend:
            self._current_tag.re_display(label=data)
        elif self._current_tag.is_under_body and self._current_tag.can_be_startend:
            self._current_tag.widget.config(text=data)

    def handle_startendtag(self, tag, attrs):
        """ handle start end tag """
        self._show_current_tag('startend', tag, attrs)
        t = TkOutTag(self, tag, attrs, 'startend')
        t.display()

    def handle_starttag(self, tag, attrs):
        """ handle tag in the beginning of it """
        self._show_current_tag('start', tag, attrs)
        t = TkOutTag(self, tag, attrs, 'start')
        t.display()
        self._current_tag = t

    def handle_endtag(self, tag):
        """ handle tag in the end of it """
        self._show_current_tag('end', tag)
        if tag != self._current_tag._tag_name:
            msg = 'start tag <{}> does not match end tag </{}>'
            raise TagStartEndNotMatch(msg.format(self._current_tag._tag_name, tag))
        else:
            self._current_tag = None


class TkOutModel:

    def __init__(self):
        attrs = inspect.getmembers(self, lambda a: not(inspect.isroution(a)))
        attrs = [a for a in attrs if not(a[0].startswith('__') and a[0].endswith('__'))]
        for a in attrs:
            attr = getattr(self, a)
            setattr(self, a, property(lambda attr: attr.get()))
