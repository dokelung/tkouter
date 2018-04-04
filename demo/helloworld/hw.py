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