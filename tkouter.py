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
    'BODY_WIDGETS',
    'LOADER',
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
    'TagLossAttributeError',
    'TagUnRecognizedError',
    'DataNotExistError',
    'ClassNotExistError',
    'TagStartEndNotMatch',
    'TagInWrongScope',
    'TagStartEndTypeError',
    'TagDisplayError',
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
_HEAD_WIDGETS = {
    'menu': Menu,
    'command': 'command',
    'separator': 'separator',
    'title': 'title',
}

_COMBO_WIDGETS = {
    'radiobutton': ttk.Radiobutton,
    'checkbutton': ttk.Checkbutton,
}

BODY_WIDGETS = {
    # widget tag type
    'label': Label,
    'entry': Entry,
    'button': Button,
    'spinbox': Spinbox,
    'combobox': ttk.Combobox,
    'listbox': Listbox,
    'treeview': ttk.Treeview,
    'notebook': ttk.Notebook,
    # frame tag type
    'frame': Frame,
    'labelframe': ttk.LabelFrame,
}

LOADER = FileSystemLoader('./')

# ========================================================================
# tkouter APIs
# ========================================================================
def register(name):
    """ function to add additional widget to BODY_WIDGETS
    usage: 
        register('my_widget_name')(MyWidgetClass) 
    """
    def _register(widget_cls):
        BODY_WIDGETS[name] = widget_cls
        return widget_cls
    return _register

# ========================================================================
# tkouter errors
# ========================================================================
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

class TagStartEndNotMatch(TagError):
    """ start tag does not match end tag"""

class TagInWrongScope(TagError):
    """ tag in wrong scope """

class TagStartEndTypeError(TagError):
    """ tag with wrong start end type """

class TagDisplayError(TagError):
    """ can not display tag """


# ========================================================================
# tkouter classes
# ========================================================================
class TkOutWidget(Frame):
    """ Design a user-defined widget with html-based layout

    User could define a html-based layout widget just by inheriting this class.
    Subclass may override some class attributes to make its own widget or layout.

    Public attributes:
    - body_widgets: available body widgets (dictionary)
    - layout: layout html or layout-html file name (string)
    - classes: widget classes which provides several uniform interfaces to
               configure widgets. (class)
    - context: used to render the layout if it is a template (dictionary)
    - data_context: used to query the data when building a widget. (dictionary)
    """
    body_widgets = None
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
        if self.body_widgets is None:
            self.body_widgets = BODY_WIDGETS
            self.body_widgets.update(_COMBO_WIDGETS)
        self._widget_type_counter = {}
        self._widgets = {}
        self._widgets.update(self.body_widgets)
        self._widgets.update(_HEAD_WIDGETS)
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
        raise NotImplementedError


class TkOutTag:
    """ Model a tkouter tag """

    _widget_type_counter = {}

    def __init__(self, creater, tag_name, attrs, se_type):
        self._tkoutw = creater._tkoutw
        self._tag_name = tag_name
        self._parent = self if self.is_html else creater._current_tag
        self._attrs = attrs
        self._attrs_dic = dict(attrs)
        self._se_type = se_type
        self._widget = None
        self._check_valid()
        self._check_se()
        self._check_scope()

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
        return self._tag_name in self._tkoutw._widgets or self.is_side

    @property
    def can_be_startend(self):
        return self._tag_name in self._tkoutw._widgets or self._tag_name in ['command', 'radiobutton', 'checkbutton']

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
        return self._tkoutw._widgets.get(self.widget_type, None)

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
        elif self.is_top_menu:
            self.parent_widget['menu'] = self.widget
        elif self.is_under_body:
            self.widget.pack(side=self.pack_side, **self.sp_options)


class TkOutWidgetCreator(html.parser.HTMLParser):
    """ Create tkouter widget layout by html

    It is the core engine of html-based layout.
    User should not use it directly.
    """

    def __init__(self, tkout_widget):
        super().__init__()
        self._tkoutw = tkout_widget
        self._scope = ''
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

    def handle_data(self, data):
        """ handle data """
        if self._current_tag._tag_name == 'title':
            self._tkoutw.parent.title(data)
        elif self._current_tag.is_under_body and self._current_tag.can_be_startend:
            self._current_tag.widget.config(text=data)

    def handle_startendtag(self, tag, attrs):
        """ handle start end tag """
        t = TkOutTag(self, tag, attrs, 'startend')
        t.display()

    def handle_starttag(self, tag, attrs):
        """ handle tag in the beginning of it """
        t = TkOutTag(self, tag, attrs, 'start')
        t.display()
        self._current_tag = t

    def handle_endtag(self, tag):
        """ handle tag in the end of it """
        if tag != self._current_tag._tag_name:
            msg = 'start tag <{}> does not match end tag <{}>'
            raise TagStartEndNotMatch(msg.format(self._current_tag._tag_name, tag))
        else:
            self._current_tag = None


class TkOutWidgetCreator2(html.parser.HTMLParser):
    """ Create tkouter widget layout by html

    It is the core engine of html-based layout.
    User should not use it directly.
    """

    def __init__(self, tkout_widget):
        super().__init__()
        self._tkoutw = tkout_widget
        self._scope = ''
        self._tag_stack = []
        # define tags
        self.skip_tags = ['html']
        self.area_tags = ['head', 'body']
        self.side_tags = ['top', 'bottom', 'left', 'right']
        self.menu_tags = ['menu', 'separator', 'command', 'radiobutton', 'checkbutton']
        self.comb_tags = list(_COMBO_WIDGETS.keys())
        self.head_tags = list(_HEAD_WIDGETS.keys()) + list(_COMBO_WIDGETS.keys())
        self.body_tags = list(self._tkoutw.body_widgets.keys()) + self.side_tags + ['widget']

    @property
    def _current_tag(self):
        return self._tag_stack[-1]

    @_current_tag.setter
    def _current_tag(self, next_tag):
        self._tag_stack.append(next_tag)

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

    def _is_widget_tag(self, tag):
        return tag in self._tkoutw._widgets

    def _init_head(self):
        """ settings for handling elements between <head> tag """
        self._scope = 'head'
        self._parents = [self._tkoutw.parent]

    def _init_body(self):
        """ settings for handling elements between <body> tag """
        self._scope = 'body'
        self._parents = [self._tkoutw]
        self._packtypes = ['top']

    def _backtrack(self):
        """ backtrack to the upper level """
        if self._scope == 'head':
            self._parents.pop(-1)
        elif self._scope == 'body':
            self._parents.pop(-1)
            self._packtypes.pop(-1)

    def _parseattrs(self, attrs, tag, check_widget=True):
        """ parse tag's attributes

        given:
            tag: tag name
            attrs: tuple list, each tuple is a 2-elements pair (attr, value)
        return:
            tuple: (name, typ, widget, options, sp_options)
            - name: variable name (string)
            - typ: widget type
            - widget: widget class name (class, type)
            - options: widget options (dictionary)
            - sp_options: special options (dictionary)
        """
        # use tag as type if tag is an available widget name
        typ = tag if tag in self._tkoutw._widgets else None
        # init return values
        name, widget, options, sp_options = (None, None, {}, {})
        # parse attributes
        for attr, value in attrs:
            if attr == 'name':
                name = value,
                m
            elif attr == 'type':
                typ = value
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
        # post process
        widget = self._tkoutw._widgets.get(typ, None)
        if widget:
            name = self._handle_name(name, typ)
        options = self._handle_options(options)
        # check widget
        if check_widget and widget is None:
            msg = 'loss "type" attribute in tag <{}>'
            raise TagLossAttributeError(msg.format(tag))
        return name, typ, widget, options, sp_options

    def _handle_name(self, name, typ):
        """ handle widget name

        User can omit "name" attribute for their widgets, this function use
        given "typ" and current widgets number to produce an unique name
        for widget using.

        given:
            name: original name attribute fetched from tag || None
            typ: type attribute fetched from tag (should not be None)
        return:
            a string which 
        """
        assert(typ is not None)
        if name is not None:
            return name
        if typ in self._tkoutw._widget_type_counter:
            self._tkoutw._widget_type_counter[typ] += 1
        else:
            self._tkoutw._widget_type_counter[typ] = 0
        return typ + '_' + str(self._tkoutw._widget_type_counter[typ])

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

    def _get_packside(self, sp_options):
        if 'side' in sp_options:
            side = sp_options['side']
            del sp_options['side']
        else:
            side = self._packtype
        return side

    def _create_widget(self, name, widget_cls, options):
        """ create widget with widget_cls and options, also assign to name """
        if not isinstance(self._parent, Menu): # general widget
            widget = widget_cls(self._parent, **options)
            setattr(self._tkoutw, name, widget)
        elif widget_cls == Menu: # top menu and sub menu
            widget = widget_cls(self._parent)
            setattr(self._tkoutw, name, widget)
        else: # separator, command, checkbutton, radiobutton under menu
            widget = None
        return widget

    def _show_widget(self, typ, widget, options, sp_options):
        """ to display widget
        - top menu: set to windows's menu attribute
        - sub menu: add_cascade to parent menu
        - menu widget: add to parent menu
        - general widget: pack
        """
        if isinstance(self._parent, Menu):
            if isinstance(widget, Menu): # sub menu
                self._parent.add_cascade(menu=widget, **options)
            else: # separator, command, checkbutton, radiobutton under menu
                self._parent.add(itemType=typ, **options)
        elif isinstance(widget, Menu): # top level menu
            self._parent['menu'] = widget
        else: # general widget
            side = self._get_packside(sp_options)
            widget.pack(side=side, **sp_options)

    def _handle_widget(self, tag, attrs):
        """ create widget and show it """
        name, typ, Widget, options, sp_options = self._parseattrs(attrs, tag)
        widget = self._create_widget(name, Widget, options)
        self._show_widget(typ, widget, options, sp_options)
        return widget

    def _check_scope(self, tag):
        if tag in self.comb_tags:
            return
        if tag in self.head_tags and self._scope != 'head':
            msg = 'tag <{}> should be under scope tag <head>'
            raise TagInWrongScope(msg.format(tag))
        if tag in self.body_tags and self._scope != 'body':
            msg = 'tag <{}> should be under scope tag <body>'
            raise TagInWrongScope(msg.format(tag))

    def handle_data(self, data):
        """ handle data """
        if self._current_tag == 'title':
            self._tkoutw.parent.title(data)
        elif self._current_tag in self.body_tags and self._is_widget_tag(self._current_tag):
            print(self._current_tag, self._parent)
            self._parent.config(text=data)

    def handle_startendtag(self, tag, attrs):
        """ handle start end tag """
        self._check_scope(tag)

        if tag in self.menu_tags and tag != 'menu':
            widget = self._handle_widget(tag, attrs)
        elif tag in self.body_tags:
            widget = self._handle_widget(tag, attrs)
        elif self._is_widget_tag(tag):
            pass
        else:
            msg = 'unrecognized tag <{}>'
            raise TagUnRecognizedError(msg.format(tag))

    def handle_starttag(self, tag, attrs):
        """ handle tag in the beginning of it """
        self._current_tag = tag
        self._check_scope(tag)

        if tag in self.skip_tags:
            pass
        elif tag in self.area_tags:
            if tag == 'head':
                self._init_head()
            elif tag == 'body':
                self._init_body()
        elif tag in self.side_tags:
            container = self._handle_widget(tag, attrs)
            self._parent = container
            self._packtype = tag
        elif tag in self.menu_tags:
            if tag == 'menu':
                menu = self._handle_widget(tag, attrs)
                self._parent = menu
            else:
                widget = self._handle_widget(tag, attrs)
                self._parent = widget
        elif tag in self.body_tags:
            widget = self._handle_widget(tag, attrs)
            self._parent = widget
            self._packtype = 'top'
        elif self._is_widget_tag(tag):
            pass
        else:
            msg = 'unrecognized tag <{}>'
            raise TagUnRecognizedError(msg.format(tag))

    def handle_endtag(self, tag):
        """ handle tag in the end of it """
        if tag != self._current_tag:
            msg = 'start tag <{}> does not match end tag <{}>'
            raise TagStartEndNotMatch(msg.format(self._current_tag, tag))
        else:
            self._tag_stack.pop(-1)
        self._check_scope(tag)

        if tag in self.skip_tags:
            pass
        elif tag in self.area_tags:
            self._backtrack()
            assert(not self._parents)
        elif tag in self.side_tags:
            self._backtrack()
        elif tag in self.menu_tags:
            if tag == 'menu':
                self._backtrack()
            else:
                self._backtrack()
        elif tag in self.body_tags:
            self._backtrack()
        elif self._is_widget_tag(tag):
            pass
        else:
            msg = 'unrecognized tag <{}>'
            raise TagUnRecognizedError(msg.format(tag))


class TkOutModel:

    def __init__(self):
        attrs = inspect.getmembers(self, lambda a: not(inspect.isroution(a)))
        attrs = [a for a in attrs if not(a[0].startswith('__') and a[0].endswith('__'))]
        for a in attrs:
            attr = getattr(self, a)
            setattr(self, a, property(lambda attr: attr.get()))
