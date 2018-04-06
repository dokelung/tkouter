from tkinter import *
from tkouter import *


class SimpleCalculator(TkOutWidget):
    labela = StringField(default='Number A:')
    labelb = StringField(default='Number B:')
    labelc = StringField(default='Result:')
    contenta = IntField(default=0)
    contentb = IntField(default=0)
    contentc = IntField(default=0)

    layout = 'cal.html'

    def __init__(self, tkroot):
        super().__init__(tkroot)

    def add(self):
        a = self.contenta
        b = self.contentb
        self.contentc = a + b

    def sub(self):
        a = self.contenta
        b = self.contentb
        self.contentc = a - b

    def mul(self):
        a = self.contenta
        b = self.contentb
        self.contentc = a * b

    def div(self):
        a = self.contenta
        b = self.contentb
        self.contentc = a / b

    def quit(self):
        self.parent.destroy()


if __name__ == '__main__':
    root = Tk()
    cal = SimpleCalculator(root)
    cal.pack()
    root.mainloop()