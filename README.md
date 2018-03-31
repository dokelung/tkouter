# tkouter

Creating GUI layout can be troublesome sometimes.
This package provides an easy way that you can use familar html to create layout.
Also, it can help you save lots of time on the settings of widgets, variable
management and more.
This package helps user to use MVC pattern to do GUI design.

在過往的 GUI 程式設計中，製作 layout 往往是一件麻煩事。

1. 散落各處的元件及其擺放方式，難以讓設計師一目了然地想像和理解排版，我們只能透過實際運行 GUI 應用才能觀察到整體的佈局設計。
2. 其次，在代碼中，關於佈局的 **視圖邏輯**、處理使用者輸入與渲染的 **控制邏輯** 與 GUI 應用主要的 **計算邏輯**，完全混雜在一起，既不利於開發，也不利於維護修改。
3. 其三，缺乏統一性的方式可以對相關 GUI 元件進行屬性上的修改。

以上這些不足，在 Web 開發中，基於歷史發展的硬限制和逐步的改良加強，早就有了更方便的工具和解決方法: html、css 和模板語言的使用，能夠完全地切割視圖邏輯，能使設計單純化，也能使佈局一目了然；使用 MVC 設計架構的框架，能夠切割各種邏輯業務，使得設計更有彈性、更易維護。

基於以上需求和 Web 解決方案的啟發，tkinter 的擴充函式庫 - tkouter 誕生了，它支援使用者以 html 進行 layout 的設計。自此將視圖切割，並大幅度地簡化了設計的難度，更能以此為基礎，讓整體的設計趨近於 MVC 的原則。

## Contents

* [Installation](#installation)
* [Requirements](#requirements)

## Installation

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
