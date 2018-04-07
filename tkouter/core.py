""" core module of tkouter
"""


__all__ =  [
    'register',
    'TkOutWidget',
]


from io import StringIO
from html.parser import HTMLParser
from tkinter import Frame, Menu
from tkinter import ttk

from jinja2 import Environment, Template
from lxml import etree
from lxml.cssselect import CSSSelector
import tinycss

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


class TkGridMgr:

    def __init__(self):
        self._segments = {}

    def get_column(self, row, rowspan=1, colspan=1):
        rsegments = self._segments.setdefault(row, [])
        if not rsegments:
            return 0
        lo = rsegments[0][0]
        hi = rsegments[-1][-1]
        for col in range(0, hi + 2):
            if self._has_space(row, col, rowspan, colspan):
                return col

    def add_column(self, row, col, rowspan=1, colspan=1):
        for r in range(row, row + rowspan):
            rsegments = self._segments.setdefault(r, [])
            rsegments.append((col, col + colspan - 1))
            self._segments[r] = self._merge_segments(rsegments)

    def _has_space(self, row, col, rowspan=1, colspan=1):
        LO, HI = 0, 1
        test = (col, col + colspan - 1)
        for r in range(row, row + rowspan):
            rsegments = self._segments.setdefault(r, [])
            for seg in rsegments:
                if seg[HI] < test[LO]:
                    continue
                elif seg[LO] > test[HI]:
                    break
                else:
                    return False
        return True

    @staticmethod
    def _merge_segments(segments):
        LO, HI = 0, 1
        segments = sorted(segments, key=lambda seg: seg[LO])
        merged = []
        for higher in segments:
            if not merged:
                merged.append(higher)
            else:
                lower = merged[-1]
                if higher[LO] <= lower[HI] or (higher[LO] - 1 == lower[HI]):
                    upper_bound = max(lower[HI], higher[HI])
                    merged[-1] = (lower[LO], upper_bound)
                else:
                    merged.append(higher)
        return merged


class TkOutElement(etree.ElementBase):

    def init(self, tkoutw):
        # common attributes
        self.tkoutw = tkoutw
        self.widgets = tkoutw.widgets
        self.widget_type_counter = tkoutw.widget_type_counter
        self.data_context = tkoutw.data_context

        self._widget = None
        self._name = None
        self._options = {}
        self._widget_method_options = {}

        if self.is_html:
            return

        # check
        self._check_valid()
        self._check_scope()

        # parse option
        self._gridmgr = TkGridMgr() if self.is_grid else None
        self._parse_options()
        self._init_pack_options()
        self._init_grid_options()

    # top checker
    def _check_valid(self):
        if not (self.is_html or self.is_scope or self.can_under_head or self.can_under_body):
            msg = 'unrecognized tag <{}>'
            raise TagUnRecognizedError(msg.format(self.tag))

    def _check_scope(self):
        if not (self.is_html or self.is_scope or self.is_under_head or self.is_under_body):
            msg = 'tag <{}> should be under tag <head> or <body>'
            raise TagInWrongScope(msg.format(self.tag))
        elif self.is_under_head and not self.can_under_head:
            msg = 'tag <{}> should not be under scope tag <head>'
            raise TagInWrongScope(msg.format(self.tag))
        elif self.is_under_menu and not self.can_under_menu:
            msg = 'tag <{}> should not be under tag <menu>'
            raise TagInWrongScope(msg.format(self.tag))
        elif self.is_under_body and not self.can_under_body:
            msg = 'tag <{}> should not be under scope tag <body>'
            raise TagInWrongScope(msg.format(self.tag))
        elif self.is_in_grid and not self.can_in_grid:
            msg = 'tag <{}> should not be in tag <grid>'
            raise TagInWrongScope(msg.format(self.tag))
        elif self.is_in_gr and not self.can_in_gr:
            msg = 'tag <{}> should not be in tag <gr>'
            raise TagInWrongScope(msg.format(self.tag))
        elif self.is_in_gd and not self.can_in_gd:
            msg = 'tag <{}> should not be in tag <gd>'
            raise TagInWrongScope(msg.format(self.tag))

    # option parsing
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
                    data = self.data_context[dkey]
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
        for attr, value in self.items():
            if attr in ['name', 'type', 'class', 'id']:
                continue
            elif '-' in attr:
                method, _, attr  = attr.partition('-')
                options = self._widget_method_options.setdefault(method, {})
                options[attr] = value
            else:
                self._options[attr] = value
        if self.text and self.text.strip():
            if self.is_under_head:
                if self.is_under_menu:
                    self._options['label'] = self.text.strip()
                elif self.is_root_attr:
                    self._options['root_attr'] = self.text.strip()
            elif self.is_under_body:
                self._options['text'] = self.text.strip()
        # handle options
        self._options = self._handle_options(self._options)
        for method, options in self._widget_method_options.items():
            self._widget_method_options[method] = self._handle_options(options)

    def _init_pack_options(self):
        if self.is_under_body:
            pack_options = self._widget_method_options.setdefault('pack', {})
            if 'side' not in pack_options:
                if self.getparent().is_body or self.getparent().is_notebook:
                    pack_options['side'] = 'top'
                elif self.getparent().is_side:
                    pack_options['side'] = self.getparent().tag

    def _init_grid_options(self):
        if self.is_gd:
            gr = self.getparent()
            grid = gr.getparent()
            if 'row' not in self.grid_options:
                self.grid_options['row'] = row = grid.index(gr)
            if 'column' not in self.grid_options:
                rowspan = int(self.grid_options.get('rowspan', 1))
                colspan = int(self.grid_options.get('columnspan', 1))
                col = self.gridmgr.get_column(row, rowspan, colspan)
                self.grid_options['column'] = col
                self.gridmgr.add_column(row, col, rowspan, colspan)

    # tag category
    @property
    def is_html(self):
        return self.tag == 'html' or self.tag =='xml'

    @property
    def is_head(self):
        return self.tag == 'head'

    @property
    def is_root_attr(self):
        return self.tag in ['title']

    @property
    def is_link(self):
        return self.tag == 'link'

    @property
    def is_css(self):
        return self.is_link and self.get('type') == 'text/css'

    @property
    def is_body(self):
        return self.tag == 'body'

    @property
    def is_scope(self):
        return self.is_head or self.is_body

    @property
    def is_side(self):
        return self.tag in ['top', 'bottom', 'left', 'right']

    @property
    def is_grid(self):
        return self.tag == 'grid'

    @property
    def is_gr(self):
        return self.tag == 'gr'

    @property
    def is_gd(self):
        return self.tag == 'gd'

    @property
    def is_grid_element(self):
        return self.is_gr or self.is_gd

    @property
    def is_menu(self):
        return self.has_widget_cls and issubclass(self.widget_cls, Menu)

    @property
    def is_top_menu(self):
        return self.is_menu and (not self.getparent().is_menu)

    @property
    def is_sub_menu(self):
        return self.is_menu and self.getparent().is_menu

    @property
    def is_notebook(self):
        return self.has_widget_cls and issubclass(self.widget_cls, ttk.Notebook)

    # scope checker
    @property
    def is_under_head(self):
        if self.getparent().is_html:
            return False
        return self.getparent().is_head or self.getparent().is_under_head

    @property
    def is_under_menu(self):
        return self.getparent().is_menu

    @property
    def is_under_body(self):
        if self.getparent().is_html:
            return False
        return self.getparent().is_body or self.getparent().is_under_body

    @property
    def is_in_grid(self):
        return self.getparent().is_grid

    @property
    def is_in_gr(self):
        return self.getparent().is_gr

    @property
    def is_in_gd(self):
        return self.getparent().is_gd

    @property
    def can_under_head(self):
        return self.is_root_attr or self.is_link or self.is_menu or self.can_under_menu

    @property
    def can_under_menu(self):
        return self.tag in ['separator', 'command', 'radiobutton', 'checkbutton'] or self.is_sub_menu

    @property
    def can_under_body(self):
        return (self.tag in self.widgets and not self.is_menu) or self.is_side or self.is_grid or self.is_grid_element

    @property
    def can_in_grid(self):
        return self.is_gr

    @property
    def can_in_gr(self):
        return self.is_gd

    @property
    def can_in_gd(self):
        return self.can_under_body and not self.is_grid_element

    # widget checker
    @property
    def has_no_widget_type(self):
        return self.is_html or self.is_scope or self.is_root_attr or self.is_grid_element

    @property
    def has_widget_type(self):
        return not self.has_no_widget_type

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
        return self.widget is not None

    @property
    def has_gridmgr(self):
        return self._gridmgr is not None

    # widget attr
    @property
    def widget_type(self):
        if self.has_no_widget_type:
            t = None
        elif self.is_side or self.is_grid:
            t = self.get('type') or'frame'
        else:
            t = self.get('type') or self.tag
        return t

    @property
    def widget_name(self):
        if self.has_widget_cls and self._name is None:
            self._name = self.get('name')
            if self._name is None:
                if self.widget_type in self.widget_type_counter:
                    self.widget_type_counter[self.widget_type] += 1
                else:
                    self.widget_type_counter[self.widget_type] = 0
                self._name = self.widget_type + '_' + str(self.widget_type_counter[self.widget_type])
        return self._name

    @property
    def widget_cls(self):
        return self.widgets.get(self.widget_type, None)

    @property
    def parent_widget(self):
        if self.getparent() is not None:
            if self.getparent().is_head:
                return self.tkoutw.parent
            elif self.getparent().is_body:
                return self.tkoutw
            elif self.getparent().is_gd:
                return self.getparent().getparent().getparent().widget
            else:
                return self.getparent().widget
        return None

    @property
    def gridmgr(self):
        if self.is_grid:
            return self._gridmgr
        elif self.is_gd:
            return self.getparent().getparent().gridmgr

    @property
    def pack_options(self):
        return self._widget_method_options['pack']

    @property
    def grid_options(self):
        return self._options

    @property
    def widget(self):
        if self._widget is None:
            assert(self.parent_widget)
            if self.is_under_body and not self.is_grid_element:
                self._widget = self.widget_cls(self.parent_widget, **self._options)
                setattr(self.tkoutw, self.widget_name, self._widget)
            elif self.is_menu:
                self._widget = self.widget_cls(self.parent_widget)
                setattr(self.tkoutw, self.widget_name, self._widget)
        return self._widget

    # core function
    def display(self):
        if self.is_html or self.is_scope or self.is_link or self.is_grid_element:
            pass
        elif self.is_under_head:
            if self.is_sub_menu:
                self.parent_widget.add_cascade(menu=self.widget, **self._options)
            elif self.is_under_menu:
                self.parent_widget.add(itemType=self.widget_type, **self._options)
            elif self.is_top_menu:
                self.parent_widget['menu'] = self.widget
            elif self.is_root_attr:
                func = getattr(self.parent_widget, self.tag)
                func(self._options['root_attr'])
        elif self.is_under_body:
            if self.is_in_gd:
                self.widget.grid(**self.getparent().grid_options)
            else:
                self.widget.pack(**self.pack_options)
            if self.getparent().is_notebook:
                self.parent_widget.add(child=self.widget, text=self.widget_name)


class TkOutWidget(Frame):
    """ Design a user-defined widget with html-based layout

    User could define a html-based layout widget just by inheriting this class.
    Subclass may override some class attributes to make its own widget or layout.

    Public attributes:
    - widgets: available widgets (dictionary)
    - layout: layout html(xml) or layout-html(xml) file name (string)
    - context: used to render the layout if it is a template (dictionary)
    - data_context: used to query the data when building a widget. (dictionary)
    """
    widgets = settings.WIDGETS
    loader = settings.LOADER
    layout = None
    context = {}
    data_context = None

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        if self.data_context is None:
            self.data_context = {'self': self}
        self.widget_type_counter = {}
        self._build()

    def _build(self):
        """ create layout and define widget attribute by tkouter html """
        if not self.layout:
            return

        env = Environment(loader=self.loader)
        if '.html' in self.layout or 'xml' in self.layout:
            template = env.get_template(self.layout)
            self._html = template.render(self.context)
        else:
            self._html = Template(self.layout).render(self.context)

        # lxml parser
        parser_lookup = etree.ElementDefaultClassLookup(element=TkOutElement)
        self._parser = etree.XMLParser()
        self._parser.set_element_class_lookup(parser_lookup)
        self._tree = etree.parse(StringIO(self._html), self._parser)

        # we should cache the elements for storing data to it
        self._proxy_cache = list(self._tree.getroot().iter())

        # css
        css = None
        for e in self._tree.getroot().iter():
            if e.is_css and e.get('href'):
                self._css = env.get_template(e.get('href')).render()
                self._css_parser = tinycss.make_parser()
                self._stylesheet = self._css_parser.parse_stylesheet(self._css)
                for rule in self._stylesheet.rules:
                    for e in self._select(rule.selector.as_css()):
                        for d in rule.declarations:
                            if e.get(d.name) is None:
                                e.set(d.name, d.value.as_css())

        # post init etree elements and display their widgets
        for e in self._tree.getroot().iter():
            try:
                e.init(self)
                e.display()
            except TagError as err:
                print('Error when parsing tag: ')
                print(etree.tostring(e, pretty_print=True, encoding=str, method='html'))
                raise err

    def _select(self, selector_str):
        """ use css selector string to query corresponding etree elements """
        sel = CSSSelector(selector_str)
        return (e for e in sel(self._tree.getroot()))

    def select(self, selector_str):
        """ use css selector string to query corresponding widgets """
        return (e.widget for e in self._select(selector_str) if e.widget is not None)