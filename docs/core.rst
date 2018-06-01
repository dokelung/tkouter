核心
====

要使用 tkouter，我們通常都會從 tkouter 中匯入所有的元件：

::

    from tkouter import *

當然我們也可以只匯入需要用的部分，例如：

::

    from tkouter import TkOutWidget

繼承 TkOutWidget 來實作自訂元件
-------------------------------

``tkouter.core.TkOutWidget`` 是 tkouter 最核心的 class，我們實作的元件都必需繼承自該類別。

一個最基本的 ``TkOutWidget`` 可能長成下面這個樣子:

::

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

我們透過設定類別變數 ``layout``，來給予該元件一個 html 佈局，tkouter 會自動根據該 html 來生成相應的佈局。

我們也可以將這段 html 放到一個單獨的文件 ``hw.html`` 裡面，然後改成指定文件名的方式來讓 tkouter 找到 html 佈局：

::

    class HelloWorld(TkOutWidget):
        layout = "hw.html"

        def hello(self):
            messagebox.showinfo('welcome to tkouter', 'hello world')

寫完了 ``TkOutWidget`` 類別之後，我們只要將之實例化，便能將該元件生出來並且做好佈局，最後呼叫 tkinter root 的 mainloop 來啟動 GUI 應用。

    >>> from tkinter import Tk
    >>> root = Tk()
    >>> hw = HelloWorld(root)
    >>> hw.pack()
    >>> root.mainloop()

下面簡列該類別中，五個可設定的 class variable，我們將在各個章節介紹他們：

============= =========
name          說明
============= =========
widgets       這是一個 dictionay，key 是可使用的標籤名，value 是該標籤對應生成的 tk 元件。
loader        html 佈局和 css 等靜態文件的載入器，使用者可以將之設定為任何一個可用的 Jinja2 載入器。
layout        描述佈局的 **html 字串** 或是 **html 文件名稱**，目前僅支援 ``.html`` 和 ``.xml`` 兩種文件類型。
context       這是一個 dictionay，用來進行 html 佈局的 **渲染 (render)**。
data_context  這是一個 dictionay，用來進行 html 佈局的 **綁定 (bind)**。
============= =========

接下來，我們會陸續介紹 tkouter 如何實現佈局的，同時也會指出一些設定上要注意的事項。

原理
----

整個佈局的原理是這樣子的：

1. ``TkOutWidget`` 本身是 ``Frame`` 元件的子類別，當我們實體化一個 ``TkOutWidget`` 物件的時候，我們會生成一個 ``Frame`` 元件。而在 ``<body>`` 標籤其下的元件會 pack 或 grid 到這個 ``Frame`` 底下。
2. ``<html>``、``<head>`` 和 ``<body>`` 標籤不會做任何事情，他們只是用來界定範圍用的。
3. ``<html>`` 標籤底下的內容都是用來設置頂層資訊或菜單的，詳見之後的介紹。
4. ``<body>`` 標籤底下只允許元件標籤和佈局標籤的存在，tkouter 首先根據元件標籤產生對應的 tk 元件並將之賦值給對應的變數，再根據佈局標籤，呼叫對應的 ``pack`` 和 ``grid`` 方法來做佈局。

.. note::
    元件在生成的時候會以其上層標籤對應的元件為 parent (master)，而 TkOutWidget 元件本身的 parent 在其被實例化時指定。

標籤
----

接著我們來談佈局上的標籤。

標籤的結構與屬性
~~~~~~~~~~~~~~~~

由於 tkouter 的核心引擎是一個 XML parser，所以能夠使用的標籤只有：

1. 成對出現的 start tag 和 end tag，前者如 ``<html>``，後者如 ``</html>``。
2. 單獨出現的 startend tag，也就是所謂的封閉標籤，如  ``<button />``。

而有些標籤只能以成對的方式出現，例如 ``<head>`` 或 ``<body>``，而大部分的元件標籤都可以自由選擇使用成對標籤或封閉標籤。

一個 **完整的** 標籤，可能長這樣：

::

    <button class="but" id="b0" pack-side="right">
        My Button
    </button>

如同標準的 html，一個 tkouter 標籤具有下列成分：

**標籤名稱**
  在標籤最一開頭的單一字串，標籤名稱必須是 tkouter 預設支援的標籤或是使用者自行註冊的元件標籤。

**標籤屬性**
  以 ``屬性名="屬性值"`` 的形式出現，各屬性間由 *空白* 隔開。
  其中 ``class`` 和 ``id`` 屬性是所有標籤皆可設定的屬性，其作用是能讓我們使用 CSS selector 去選取元件。
  而名稱中有 ``-`` 字元的屬性我們稱為 **特殊屬性** 或 **元件方法屬性**，我們會在 `元件標籤 <元件標籤_>`_ 中介紹到。

**標籤內文**
  夾在成對標籤中的純文字。
  對於元件標籤而言，標籤內文會成為其 ``text`` 屬性的值，而對於菜單標籤而言，該文字會成為 ``label`` 屬性的值。
  也就是說 ``<button>My Button</button>`` 基本上等價於 ``<button text="My Button" />``。

.. note::
    除了標籤名稱之外，其他的屬性幾乎都是可選的。如果使用預設值就能滿足我們需求的話，我們應當盡可能減少不必要的屬性設定。

標籤的種類
~~~~~~~~~~

在 tkouter 的 html 佈局中，標籤分為下面幾類：

============= =========
種類           說明
============= =========
文件標籤       就是 ``<html>`` 標籤，用以定義整個佈局的範圍。
範圍標籤       分別是 ``<head>`` 和 ``<body>`` 標籤，前者用來作一些 top level 的設定，後者用來佈局實體元件。
頂層資訊標籤    用來設定頂層視窗的標籤，如設定視窗標題的 ``<title>`` 標籤和設定視窗大小的 ``<geometry>`` 標籤。
佈局標籤       用來配合 ``pack`` 和 ``grid`` 方法的佈局標籤。
菜單標籤       用來進行菜單的設置的標籤，例如：``<menu>``。
元件標籤       最基本的標籤，例如：``<button>``。每個元件標籤都對應到一個 tk 元件。這也是唯一允許使用者進行擴充的標籤。
============= =========

頂層資訊標籤
~~~~~~~~~~~~

以下是 tkouter 目前支援的頂層資訊標籤：

``<title>``
  用來設定頂層視窗的標題。例如：``<title> Hello World </title>``。對應的 tkinter 語法為：``top_level_widget.title("Hello World")``
``<geometry>``
  用來設定視窗大小和位置。例如：``<geometry> 300x200+50+100 </geometry>`` 會設定視窗寬為 300，長為200，起始 x 座標為 50，起始 y 座標為 100。
  對應的 tkinter 語法是：``top_level_widget.geometry("300x200+50+100")``

佈局標籤
~~~~~~~~

tkouter 支援了 tkinter 中的 pack 佈局方法和 grid 佈局方法。

以下是可使用的 pack 佈局標籤：

``<top>``
  其下的標籤元件會由上至下排列
``<bottom>``
  其下的標籤元件會由下至上排列
``<left>``
  其下的標籤元件會由左至右排列
``<right>``
  其下的標籤元件會由右至左排列

以上四種標籤預設會生成 ``Frame`` 元件，其下的標籤元件會依照指定的 ``side`` pack 到該 ``Frame`` 上。

我們也可以使用標籤屬性 ``type`` 來改成其他可用的 ``Frame`` 元件，例如 ``LabelFrame``。

以下是個 pack 佈局的簡單範例：

::

    <top type="labelframe">
        <button />
    </top>

以下是可用的 grid 佈局標籤：

``<grid>``
  代表其下的區塊要以 grid 進行佈局，他的直接子標籤只能是 ``<gr>`` 標籤，一個 grid 系統就是由若干 *列* 組成的。
``<gr>``
  grid row 的意思。grid 標籤系統中的一列。他的直接子標籤只能是 ``<gd>`` 標籤。
``<gd>``
  一個 grid 系統中的一個網格，其直接子標籤可以是 **單一的元件標籤**、**pack 佈局標籤** 或 **另一組 grid 佈局標籤**。

``<grid>`` 標籤會預設生成 ``Frame`` 元件，其下的標籤元件會依據指定的 ``row`` 和 ``column`` grid 到該 ``Frame`` 上。

以下是個 grid 佈局的簡單範例，效果是 2x2 的網格佈局：

::

    <body>
        <grid>
            <gr>
                <gd><button>button top-left </button></gd>
                <gd><button>button top-right </button></gd>
            </gr>
            <gr>
                <gd><button>button bottom-left </button></gd>
                <gd><button>button bottom-right </button></gd>
            </gr>
        </grid>
    </body>

.. note::
    更多的佈局概念請參見 `佈局 <佈局_>`_

菜單標籤
~~~~~~~~

若想要為 tk 元件設定菜單，可使用以下相關的菜單標籤：

``<menu>``
  用以產生一層的菜單，其下可以有巢狀的菜單結構，tkouter 會自動將之轉為多級菜單。
  此標籤必須成對出現，並放置於 ``<head>`` 標籤之內。
  最外層的 ``<menu>`` 我們稱為 **頂層菜單**，其下的菜單我們稱為 **子菜單**，一個 tkouter 元件中只允許出現一個頂層菜單。
  此標籤下只允許出現 ``<menu>``、``<command>``、``<separator>``、``<radiobutton>`` 和 ``<checkbutton>`` 五種標籤。
``<command>``
  菜單命令標籤，通常會綁定一個元件方法，當其被選取的時候，呼叫對應的方法。
``<separator>``
  會產生一條分隔線。
``<radiobutton>``
  會產生菜單單選按鈕。
``<checkbutton>``：
  會產生核取方塊按鈕。

.. note::
    1. 當 tkouter 元件的 parent 是 top-level 元件的時候，才能為其設置菜單。
    2. ``<radiobutton>`` 和 ``<checkbutton>`` 是唯二可以同時用在 ``<menu>`` 和 ``<body>`` 之下的標籤。
       被使用在菜單時，不會真的產生 tk 元件，但是出現在 ``<body>`` 標籤之下，則會產生真正的元件。
    3. ``<command>``、``<radiobutton>`` 和 ``<checkbutton>`` 標籤中的 **標籤內文** 會成為菜單的 ``label`` 屬性。

元件標籤
~~~~~~~~

元件標籤具有下列標籤屬性：

**name**
  生成元件會被指派的變數名字，基本上要符合 python 的變數命名法則。
  當此項屬性未設定時，tkouter 預設會以 ``<type>_<idx>`` 作為該元件標籤的 ``name`` 屬性。
  比如說，第一個未給定 ``name`` 屬性的 ``<button>`` 標籤將會自動取得名稱：``"button_0"``。
**type**
  元件標籤對應的元件類別名，這應該是 tkouter 預設支援的元件名稱或是使用者自行註冊上去的合法元件類別。
  當此項屬性未設定時，tkouter 會以該標籤的標籤名當做 ``type``。
  比如說，``<button />`` 標籤的 ``type`` 選項將會自動判定為 ``button``，如同 ``<button type="button" />`` 一樣。

.. note::
    1. 當元件標籤的 ``type`` 屬性與標籤名不符時，以 ``type`` 屬性為主。
    2. 我們通常習慣直接以標籤名代替 ``type`` 屬性，這樣可使佈局更簡單乾淨一些。

元件標籤會根據 ``type`` 生成對應的 tkinter 元件，並且將之賦值給 ``name`` 指定的變數。

例如：

::

    <button name="button_1">
        My Button
    </button>

這個元件的 ``name = "button_1"``、``type = "button"`` 且 ``text = "My Button"``，以下是等價的 tkinter 代碼：

::

    # self is tkouter widget, instance of class "TkOutWidget"
    self.button_1 = Button(text="My Button")

.. note::
    1. 元件標籤中的 **標籤內文** 會成為元件的 ``text`` 屬性。
    2. tkouter 不單單只能進行一次性的轉換佈局，其自動生成的元件也會賦值到指定的 ``name`` 屬性，
       使用者可以在 python 代碼中用一般的方式來調整和操作元件。

佈局
----

tkouter 目前支援兩種佈局方法，分別是 **pack 佈局** 和 **grid 佈局**。

pack 佈局
~~~~~~~~~~

pack 佈局能做出相對複雜的佈局，且在佈局的語法上相對簡潔，是比較推薦的佈局方法。

我們用下面這個例子來說明：

::

    <body>
        <left>
            <top>
                <button> button 1 </button>
                <button> button 2 </button>
            </top>
            <button> button 3 </button>
            <button> button 4 </button>
        </left>
    </body>

他對應


tkouter 一律對沒有使用 grid 佈局的元件進行 pack 的動作，而且會根據元件的 parent 決定好 pack side。

**pack**
  生成元件會被指派的變數名字，基本上要符合 python 的變數命名法則。

.. note::
    就如同一般的 web design 會使用 ``<div>`` 來組織垂直的排列佈局、使用 `<span>` 來組織水平的排列佈局一樣，
    tkouter 使用 ``<top>`` 和 ``<bottom>`` 實作垂直的排列佈局、使用 ``<left>`` 和 ``<right>`` 來實現水平的排列佈局。

grid 佈局
~~~~~~~~~~

渲染
----

綁定
----

透過 `渲染 <渲染_>`_ 可以讓我們在佈局模板載入的當下進行靜態的作圖具象，而綁定可以讓我們進行動態的連結，
這對於有綁定 GUI 事件的元件尤其重要。

因為渲染是一次性的，且所有的物件只能被轉為文字輸出，這對於需要綁定非字串物件的 GUI 程式而言，顯然不敷使用。

在 tkouter 的佈局中，我們可以利用單層的大括號 ``{}`` 並使用類別變數 ``data_context`` 所提供的實例來與元件進行綁定。

.. note::
    ``data_context`` 是一個 dictionary，其 key 為能在大括號 ``{}`` 中使用的變數，其值為該變數對應的物件。
    若 ``data_context`` 未被設定，預設值為 ``{'self': self}``，也就是我們能在佈局中使用 ``self`` 來代稱 tkouter widget。
    同時也能夠透過 ``.`` 來存取其屬性和成員。

舉例來說，如果 tkouter widget 有一個方法成員 ``hello`` 而我們想要將其綁定到一個按鈕元件上，可以這樣做：

::

    class MyWidget(TkOutWidget):

        layout = """
            <button command="{self.hello}">
                Print Hello
            </button>"""

        def hello(self):
            print("Hello")

這個佈局可能的 tkinter 等價代碼是：

::

    self.button_0 = Button(text="Print Hello", command=self.hello)

又或者 ``hello`` 是一個獨立的全域函數，則我們可以自行調整 ``data_context`` 來綁定該函數：

::

    def hello():
        print("Hello")

    class MyWidget(TkOutWidget):

        data_context = {'hello': hello}

        layout = """
            <button command="{hello}">
                Print Hello
            </button>"""