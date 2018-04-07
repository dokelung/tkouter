from io import StringIO
from tkinter import *
from tkinter import ttk
import unittest

from lxml import etree
from lxml.cssselect import CSSSelector
from tkouter.core import TkGridMgr, TkOutWidget, TkOutElement, register
from tkouter.errors import *
from tkouter.fields import *
from tkouter import settings
from jinja2 import DictLoader


layout_html = """
        <html>
            <head>
                <title> test </title>
                <link rel="stylesheet" type="text/css" href="{{css_name}}" />
                <menu>
                    <command> menu command </command>
                    <menu>
                        <radiobutton />
                    </menu>
                </menu>
            </head>
            <body>
                <notebook name="nb">
                    <left type="labelframe" pack-fill="both">
                        <button command="{self.test}"> {self.data_dict.button_text} </button>
                        <entry id="0" textvariable="{self.strfield.var}" />
                        <entry id="1" textvariable="{self.boolfield.var}" />
                        <entry id="2" textvariable="{self.intfield.var}" />
                    </left>
                </notebook>
                {% if test_grid %}
                <grid>
                    <gr id="gr0">
                        <gd id="gd0"><button id="bt0" text="grid button 0" /></gd>
                        <gd id="gd1" rowspan="2" columnspan="2"><button id="bt1" text="grid button 1" /></gd>
                    </gr>
                    <gr id="gr1">
                        <gd id="gd2"><button id="bt2" text="grid button 2" /></gd>
                    </gr>
                </grid>
                {% endif %}
            </body>
        </html>
    """

layout_css = """
        left > button {
            width: 8;
            text: nouse;
        }
    """

@register('testwidget')
class TestWidget(TkOutWidget):
    strfield = StringField(default='str', max_length=5)
    boolfield = BoolField(default=True)
    intfield = IntField(default=10)

    layout = layout_html
    context = {'css_name': '', 'test_grid': True}
    data_dict = {'button_text': 'test button'}

    def test(self):
        pass

class TestWidgetWithCss(TkOutWidget):
    strfield = StringField(default='str', max_length=5)
    boolfield = BoolField(default=True)
    intfield = IntField(default=10)

    layout = "test.html"
    loader = DictLoader({'test.html': layout_html, 'test.css': layout_css})
    context = {'css_name': 'test.css', 'test_grid': False}
    data_dict = {'button_text': 'test button'}

    def test(self):
        for b in self.select('button'):
            b.config(text='change')

class TestWidgetWithoutLayout(TkOutWidget):
    pass

class TestTagUnRecognizedError(TkOutWidget):
    layout = """<html><hello> invalid </hello></html>"""

class TestDataNotExistError(TkOutWidget):
    layout = """<html><head></head><body><button command="{self.nofunc}" /></body></html>"""

class TestTagInWrongScopeOutSide(TkOutWidget):
    layout = """<html><radiobutton /><head></head><body></body></html>"""

class TestTagInWrongScopeHead(TkOutWidget):
    layout = """<html><head><button /></head><body></body></html>"""

class TestTagInWrongScopeMenu(TkOutWidget):
    layout = """<html><head><menu><title></title></menu></head><body></body></html>"""

class TestTagInWrongScopeBody(TkOutWidget):
    layout = """<html><head></head><body><command /></body></html>"""

class TestTagInWrongScopeGrid(TkOutWidget):
    layout = """<html><body><grid><gd></gd></grid></body></html>"""

class TestTagInWrongScopeGr(TkOutWidget):
    layout = """<html><body><grid><gr><button /></gr></grid></body></html>"""

class TestTagInWrongScopeGd(TkOutWidget):
    layout = """<html><body><grid><gr><gd><gr></gr></gd></gr></grid></body></html>"""


class TestTkOutWidget(unittest.TestCase):

    def select_one_element(self, selector_str):
        elements = list(self.tkoutw._select(selector_str))
        assert len(elements) == 1
        return elements[0]

    def test_widget(self):
        root = Tk()
        self.tkoutw = TestWidget(root)
        html = self.select_one_element('html')
        head = self.select_one_element('head')
        body = self.select_one_element('body')
        title = self.select_one_element('title')
        css = self.select_one_element('link')
        top_menu = self.select_one_element('head > menu')
        sub_menu = self.select_one_element('menu > menu')
        left = self.select_one_element('body left')
        notebook = self.select_one_element('body > notebook')
        button = self.select_one_element('left > button')
        command = self.select_one_element('menu > command')
        radiobutton = self.select_one_element('menu > radiobutton')
        entry_0 = self.select_one_element('left > entry#0')
        grid = self.select_one_element('body > grid')
        gr_0 = self.select_one_element('#gr0')
        gd_0 = self.select_one_element('#gd0')
        gd_1 = self.select_one_element('#gd1')
        gd_2 = self.select_one_element('#gd2')
        button_g0 = self.select_one_element('#bt0')
        # tag category
        self.assertTrue(html.is_html)
        self.assertTrue(head.is_head)
        self.assertTrue(title.is_root_attr)
        self.assertTrue(css.is_link)
        self.assertTrue(css.is_css)
        self.assertTrue(body.is_body)
        self.assertTrue(head.is_scope and not title.is_scope)
        self.assertTrue(left.is_side and not body.is_side)
        self.assertTrue(grid.is_grid and gr_0.is_gr and gd_0.is_gd)
        self.assertTrue(not grid.is_grid_element and gr_0.is_grid_element and gd_0.is_grid_element)
        self.assertTrue(top_menu.is_menu and sub_menu.is_menu)
        self.assertTrue(top_menu.is_top_menu)
        self.assertTrue(sub_menu.is_sub_menu)
        self.assertTrue(notebook.is_notebook)
        # scope
        self.assertTrue(title.is_under_head and not head.is_under_head)
        self.assertTrue(sub_menu.is_under_menu and not top_menu.is_under_menu)
        self.assertTrue(button.is_under_body and not body.is_under_body)
        self.assertTrue(gr_0.is_in_grid and not grid.is_in_grid)
        self.assertTrue(gd_0.is_in_gr and not gr_0.is_in_gr)
        self.assertTrue(button_g0.is_in_gd and not gd_0.is_in_gd)
        self.assertTrue(css.can_under_head and not left.can_under_head)
        self.assertTrue(radiobutton.can_under_menu and not button.can_under_menu)
        self.assertTrue(notebook.can_under_body and not title.can_under_body)
        self.assertFalse(top_menu.can_under_body or sub_menu.can_under_body)
        self.assertTrue(gr_0.can_in_grid and not grid.can_in_grid)
        self.assertTrue(gd_0.can_in_gr and not gr_0.can_in_gr)
        self.assertTrue(button_g0.can_in_gd and not gd_0.can_in_gd and not top_menu.can_in_gd)
        # widget checker
        self.assertTrue(title.has_no_widget_type and html.has_no_widget_type)
        self.assertTrue(button.has_widget_type and radiobutton.has_widget_type)
        self.assertTrue(button.has_widget_name and not title.has_widget_name)
        self.assertTrue(left.has_widget_cls and not title.has_widget_cls)
        self.assertTrue(button.has_options and not notebook.has_options)
        self.assertTrue(button.has_widget and top_menu.has_widget and not css.has_widget)
        self.assertTrue(grid.has_gridmgr and not gr_0.has_gridmgr and not gd_0.has_gridmgr)
        # widget attr
        self.assertIsNone(title.widget_type)
        self.assertEqual(left.widget_type, 'labelframe')
        self.assertEqual(button.widget_type, 'button')
        self.assertIsNone(title.widget_name)
        self.assertEqual(notebook.widget_name, 'nb')
        self.assertEqual(top_menu.widget_name, 'menu_0')
        self.assertEqual(sub_menu.widget_name, 'menu_1')
        self.assertIsNone(title.widget_cls)
        self.assertEqual(top_menu.widget_cls, Menu)
        self.assertIsNone(html.parent_widget)
        self.assertEqual(top_menu.parent_widget, self.tkoutw.parent)
        self.assertEqual(notebook.parent_widget, self.tkoutw)
        self.assertEqual(button.parent_widget, left.widget)
        self.assertEqual(grid.gridmgr, gd_0.gridmgr)
        self.assertEqual(button._options['command'], self.tkoutw.test)
        self.assertEqual(button._options['text'], 'test button')
        self.assertEqual(entry_0._options['textvariable'], self.tkoutw.__class__.__dict__['strfield'].var)
        self.assertEqual(left.pack_options['fill'], 'both')
        self.assertEqual(gd_0.grid_options, {'row': 0, 'column': 0})
        self.assertEqual(gd_1.grid_options, {'row': 0, 'column': 1, 'rowspan': '2', 'columnspan': '2'})
        self.assertEqual(gd_2.grid_options, {'row': 1, 'column': 0})
        self.assertIsNone(title.widget)
        self.assertIsInstance(button.widget, Button)
        self.assertIsInstance(top_menu.widget, Menu)
        self.assertEqual(notebook.widget, self.tkoutw.nb)
        self.assertEqual(button.widget, self.tkoutw.button_0)
        # field
        self.assertEqual(self.tkoutw.strfield, 'str')
        self.assertEqual(self.tkoutw.boolfield, True)
        self.assertEqual(self.tkoutw.intfield, 10)
        self.tkoutw.strfield = 'tttttttttt'
        self.tkoutw.boolfield = False
        self.tkoutw.intfield = 20
        self.assertEqual(self.tkoutw.strfield, 'ttttt')
        self.assertEqual(self.tkoutw.boolfield, False)
        self.assertEqual(self.tkoutw.intfield, 20)

    def test_css(self):
        root = Tk()
        self.tkoutw = TestWidgetWithCss(root)
        button = self.select_one_element('left > button')
        self.assertEqual(button._options['text'], 'test button')
        self.assertEqual(button._options['width'], '8')
        self.assertEqual(button.widget['text'], 'test button')
        self.assertEqual(button.widget['width'], 8)
        # select funcion
        self.tkoutw.test()
        self.assertEqual(button.widget['text'], 'change')

    def test_no_layout(self):
        root = Tk()
        self.tkoutw = TestWidgetWithoutLayout(root)

    def test_api(self):
        self.assertIn('testwidget', settings.WIDGETS)

    def test_error(self):
        root = Tk()
        self.assertRaises(TagUnRecognizedError, TestTagUnRecognizedError, root)
        self.assertRaises(DataNotExistError, TestDataNotExistError, root)
        self.assertRaises(TagInWrongScope, TestTagInWrongScopeOutSide, root)
        self.assertRaises(TagInWrongScope, TestTagInWrongScopeHead, root)
        self.assertRaises(TagInWrongScope, TestTagInWrongScopeMenu, root)
        self.assertRaises(TagInWrongScope, TestTagInWrongScopeBody, root)
        self.assertRaises(TagInWrongScope, TestTagInWrongScopeGrid, root)
        self.assertRaises(TagInWrongScope, TestTagInWrongScopeGr, root)
        self.assertRaises(TagInWrongScope, TestTagInWrongScopeGd, root)


class TestTkGridMgr(unittest.TestCase):

    def test_grid_mgr(self):
        gridmgr = TkGridMgr()
        self.assertEqual(gridmgr.get_column(0), 0)
        gridmgr.add_column(0, 1, 2, 2)
        self.assertEqual(gridmgr._segments[0], [(1, 2)])
        self.assertEqual(gridmgr._segments[1], [(1, 2)])
        gridmgr.add_column(0, 4, 1, 1)
        self.assertEqual(gridmgr.get_column(0), 0)
        gridmgr.add_column(0, 0, 1, 1)
        self.assertEqual(gridmgr.get_column(0), 3)
        self.assertEqual(gridmgr.get_column(1), 0)
        gridmgr.add_column(1, 0, 1, 1)
        self.assertEqual(gridmgr.get_column(1), 3)


if __name__ == '__main__':
    unittest.main()