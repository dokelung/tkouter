import operator

from tkinter import *
from tkouter import TkOutWidget, register
from cal_cls import MyClass


class MyWindow(TkOutWidget):

    classes = MyClass
    layout = 'cal.html'

    def __init__(self, tkroot):
        self.contenta = StringVar()
        super().__init__(tkroot)
        self.operator = None
        self.cache = None
        self.contenta.set(0)
        self.should_clear = True

    def clear(self):
        self.operator = None
        self.cache = None
        self.contenta.set(0)
        self.should_clear = True

    def add(self):
        if self.operator:
            self._equal()
        number = self.contenta.get()
        self.cache = number
        self.operator = operator.add
        self.should_clear = True

    def sub(self):
        if self.operator:
            self._equal()
        number = self.contenta.get()
        self.cache = number
        self.operator = operator.sub
        self.should_clear = True

    def mul(self):
        if self.operator:
            self._equal()
        number = self.contenta.get()
        self.cache = number
        self.operator = operator.mul
        self.should_clear = True

    def div(self):
        if self.operator:
            self._equal()
        number = self.contenta.get()
        self.cache = number
        self.operator = operator.truediv
        self.should_clear = True

    def _trim_redundant_digit(self, nbstr):
        if '.' in nbstr:
            intpart, _, pointpart = nbstr.partition('.')
            if not pointpart or all(d=='0' for d in pointpart):
                return intpart
        return nbstr

    def _equal(self):
        number = self.contenta.get()
        if self.operator:
            number = str(self.operator(float(self.cache), float(number)))
            number = self._trim_redundant_digit(number)
        self.contenta.set(number)

    def equal(self):
        self._equal()
        self.operator = None
        self.should_clear = True

    def percent(self):
        number = self.contenta.get()
        number = str(float(number)/100)
        self.contenta.set(number)
        self.should_clear = True

    def neg(self):
        number = self.contenta.get()
        if number[0] == '-':
            number = number[1:]
        else:
            number = '-' + number
        self.contenta.set(number)

    # number
    def dot(self):
        if self.should_clear:
            self.contenta.set('')
            self.should_clear = False
        number = self.contenta.get()
        if len(number) >= 20:
            return
        self.contenta.set(number+'.')

    def zero(self):
        if self.should_clear:
            self.contenta.set('')
            self.should_clear = False
        number = self.contenta.get()
        if len(number) >= 20:
            return
        self.contenta.set(number+'0')

    def one(self):
        if self.should_clear:
            self.contenta.set('')
            self.should_clear = False
        number = self.contenta.get()
        if len(number) >= 20:
            return
        self.contenta.set(number+'1')

    def two(self):
        if self.should_clear:
            self.contenta.set('')
            self.should_clear = False
        number = self.contenta.get()
        if len(number) >= 20:
            return
        self.contenta.set(number+'2')

    def three(self):
        if self.should_clear:
            self.contenta.set('')
            self.should_clear = False
        number = self.contenta.get()
        if len(number) >= 20:
            return
        self.contenta.set(number+'3')

    def four(self):
        if self.should_clear:
            self.contenta.set('')
            self.should_clear = False
        number = self.contenta.get()
        if len(number) >= 20:
            return
        self.contenta.set(number+'4')

    def five(self):
        if self.should_clear:
            self.contenta.set('')
            self.should_clear = False
        number = self.contenta.get()
        if len(number) >= 20:
            return
        self.contenta.set(number+'5')

    def six(self):
        if self.should_clear:
            self.contenta.set('')
            self.should_clear = False
        number = self.contenta.get()
        if len(number) >= 20:
            return
        self.contenta.set(number+'6')

    def seven(self):
        if self.should_clear:
            self.contenta.set('')
            self.should_clear = False
        number = self.contenta.get()
        if len(number) >= 20:
            return
        self.contenta.set(number+'7')

    def eight(self):
        if self.should_clear:
            self.contenta.set('')
            self.should_clear = False
        number = self.contenta.get()
        if len(number) >= 20:
            return
        self.contenta.set(number+'8')

    def nine(self):
        if self.should_clear:
            self.contenta.set('')
            self.should_clear = False
        number = self.contenta.get()
        if len(number) >= 20:
            return
        self.contenta.set(number+'9')

    def bye(self):
        print('bye')


if __name__ == '__main__':

    root = Tk()
    window = MyWindow(root)
    window.pack()
    root.mainloop()
