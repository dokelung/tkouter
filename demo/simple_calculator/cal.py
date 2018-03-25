from tkinter import *
from tkouter import *
from cal_cls import MyClass


class MyModel(TkOutModel):
    labelvara = StringVar()
    labelvarb = StringVar()
    labelvarc = StringVar()
    contenta = IntVar()
    contentb = IntVar()
    contentc = IntVar()


class MyWindow(TkOutWidget):

    classes = MyClass
    layout = 'cal.html'

    def __init__(self, tkroot):
        self.labelvara = StringVar()
        self.labelvarb = StringVar()
        self.labelvarc = StringVar()
        self.contenta = IntVar()
        self.contentb = IntVar()
        self.contentc = IntVar()
        super().__init__(tkroot)
        self.labelvara.set('Number A:')
        self.labelvarb.set('Number B:')
        self.labelvarc.set('Result :')
        print(tkroot.title.__func__.__code__.co_varnames)

    def add(self):
        a = self.contenta.get()
        b = self.contentb.get()
        self.contentc.set(a+b)

    def sub(self):
        a = self.contenta.get()
        b = self.contentb.get()
        self.contentc.set(a-b)

    def mul(self):
        a = self.contenta.get()
        b = self.contentb.get()
        self.contentc.set(a*b)

    def div(self):
        a = self.contenta.get()
        b = self.contentb.get()
        self.contentc.set(a/b)


if __name__ == '__main__':

    root = Tk()
    window = MyWindow(root)
    window.pack()
    root.mainloop()
