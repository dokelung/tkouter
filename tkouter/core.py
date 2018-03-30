""" core module of tkouter
"""


__all__ =  [
    'register',
    'TkOutWidget',
]


from html.parser import HTMLParser
from tkinter import Frame, Menu
from tkinter import ttk

from jinja2 import Environment

from . import settings
from .errors import *


def register(name):
    """ function to add additional widget to BODY_WIDGETS
    usage: 
        register('my_widget_name')(MyWidgetClass) 
    """
    def _register(widget_cls):
        settings.WIDGETS[name] = widget_cls
        return widget_cls
    return _register


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
    widgets = settings.WIDGETS
    loader = settings.LOADER
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
        self.widgets.update(settings.WIDGETS)
        self.widgets.update(user_widgets)
        self._build(settings.DEBUG)

    def _build(self, debug=False):
        """ create layout and define widget attribute by tkouter html """
        self.env = Environment(loader=self.loader)
        if self.layout:
            template = self.env.get_template(self.layout)
            self._html = template.render(self.context)
        creator = TkOutWidgetCreator(self, debug)
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

        self._options = {}
        self._widget_method_options = {}
        self._parse_options()
        self._init_pack_options()

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
                        elif attr in data.__class__.__dict__:
                            data = data.__class__.__dict__[attr]
                        elif attr in data:
                            data = data[attr]
                    modified_options[name] = data
                except:
                    msg = 'data "{}" does not exist'
                    raise DataNotExistError(msg.format(value))
            else:
                modified_options[name] = value
        return modified_options

    def _parse_options(self):
        clss = self._attrs_dic.get('class', None)
        if clss:
            cls_lst = clss.split()
            for cname in cls_lst:
                if not hasattr(self._tkoutw.classes, cname):
                    msg = 'class "{}" does not exists'
                    raise ClassNotExist(msg.format(cname))
                c = getattr(self._tkoutw.classes, cname)
                for attr, value in c.__dict__.items():
                    if attr.startswith('_'):
                        continue
                    elif '__' in attr:
                        method, _, attr  = attr.partition('__')
                        options = self._widget_method_options.setdefault(method, {})
                        options[attr] = value
                    else:
                        self._options[attr] = str(value)
        for attr, value in self._attrs:
            if attr in ['name', 'type', 'class']:
                continue
            elif '-' in attr:
                method, _, attr  = attr.partition('-')
                options = self._widget_method_options.setdefault(method, {})
                options[attr] = value
            else:
                self._options[attr] = value
        # handle options
        self._options = self._handle_options(self._options)
        for method, options in self._widget_method_options.items():
            self._widget_method_options[method] = self._handle_options(options)

    def _init_pack_options(self):
        if self.is_under_body:
            pack_options = self._widget_method_options.setdefault('pack', {})
            if 'side' not in pack_options:
                if self._parent.is_body or self._parent.is_notebook:
                    pack_options['side'] = 'top'
                else:
                    pack_options['side'] = self._parent._tag_name
                    assert(pack_options['side'] in ['top', 'bottom', 'left', 'right'])

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
        return self.has_widget_cls and issubclass(self.widget_cls, Menu)

    @property
    def is_top_menu(self):
        return self.is_menu and (not self._parent.is_menu)

    @property
    def is_sub_menu(self):
        return self.is_menu and self._parent.is_menu

    @property
    def is_notebook(self):
        return self.has_widget_cls and issubclass(self.widget_cls, ttk.Notebook)

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
        if self.is_menu or self.is_notebook:
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
    def has_options(self):
        return bool(self._options)

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
    def pack_options(self):
        return self._widget_method_options['pack']

    @property
    def widget(self):
        if self._widget is None:
            if self.is_under_body:
                self._widget = self.widget_cls(self.parent_widget, **self._options)
                setattr(self._tkoutw, self.widget_name, self._widget)
            elif self.is_menu:
                self._widget = self.widget_cls(self.parent_widget)
                setattr(self._tkoutw, self.widget_name, self._widget)
        return self._widget

    def display(self):
        if self.is_sub_menu:
            self.parent_widget.add_cascade(menu=self.widget, **self._options)
        elif self.is_under_menu:
            self.parent_widget.add(itemType=self.widget_type, **self._options)
            self._parent._menu_entry_count += 1
        elif self.is_top_menu:
            self.parent_widget['menu'] = self.widget
        elif self.is_under_body:
            self.widget.pack(**self.pack_options)

    def re_display(self, **update_options):
        options = self._options
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

    def post_process(self):
        if self._parent.is_notebook:
            self.parent_widget.add(child=self.widget, text=self.widget_name)


class TkOutWidgetCreator(HTMLParser):
    """ Create tkouter widget layout by html

    It is the core engine of html-based layout.
    User should not use it directly.
    """

    def __init__(self, tkout_widget, debug=False):
        super().__init__()
        self._tkoutw = tkout_widget
        self._tag_stack = []
        self._debug = debug

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
        if not self._debug:
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
        self._current_tag.post_process()
        if tag != self._current_tag._tag_name:
            msg = 'start tag <{}> does not match end tag </{}>'
            raise TagStartEndNotMatch(msg.format(self._current_tag._tag_name, tag))
        else:
            self._current_tag = None