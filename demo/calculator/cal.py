import operator

from tkinter import Tk

from tkouter import *
from tkouter import settings



class Calculator(TkOutWidget):

    # layout
    layout = 'cal.html'

    # model
    content = StringField(default='0', max_length=20)

    def __init__(self, tkroot):
        super().__init__(tkroot)
        self.operator = None
        self.cache = None
        self.should_clear = True

    def clear(self):
        self.operator = None
        self.cache = None
        self.content = 0
        self.should_clear = True

    def add(self):
        if self.operator:
            self._equal()
        number = self.content
        self.cache = number
        self.operator = operator.add
        self.should_clear = True

    def sub(self):
        if self.operator:
            self._equal()
        number = self.content
        self.cache = number
        self.operator = operator.sub
        self.should_clear = True

    def mul(self):
        if self.operator:
            self._equal()
        number = self.content
        self.cache = number
        self.operator = operator.mul
        self.should_clear = True

    def div(self):
        if self.operator:
            self._equal()
        number = self.content
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
        number = self.content
        if self.operator:
            number = str(self.operator(float(self.cache), float(number)))
            number = self._trim_redundant_digit(number)
        self.content = number

    def equal(self):
        self._equal()
        self.operator = None
        self.should_clear = True

    def percent(self):
        number = self.content
        number = str(float(number)/100)
        self.content = number
        self.should_clear = True

    def neg(self):
        number = self.content
        if number[0] == '-':
            number = number[1:]
        else:
            number = '-' + number
        self.content = number

    # number
    def dot(self):
        if self.should_clear:
            self.content = ''
            self.should_clear = False
        self.content += '.'

    def zero(self):
        if self.should_clear:
            self.content = ''
            self.should_clear = False
        self.content += '0'

    def one(self):
        if self.should_clear:
            self.content = ''
            self.should_clear = False
        self.content += '1'

    def two(self):
        if self.should_clear:
            self.content = ''
            self.should_clear = False
        self.content += '2'

    def three(self):
        if self.should_clear:
            self.content = ''
            self.should_clear = False
        self.content += '3'

    def four(self):
        if self.should_clear:
            self.content = ''
            self.should_clear = False
        self.content += '4'

    def five(self):
        if self.should_clear:
            self.content = ''
            self.should_clear = False
        self.content += '5'

    def six(self):
        if self.should_clear:
            self.content = ''
            self.should_clear = False
        self.content += '6'

    def seven(self):
        if self.should_clear:
            self.content = ''
            self.should_clear = False
        self.content += '7'

    def eight(self):
        if self.should_clear:
            self.content = ''
            self.should_clear = False
        self.content += '8'

    def nine(self):
        if self.should_clear:
            self.content = ''
            self.should_clear = False
        self.content += '9'

    def bye(self):
        print('bye')


if __name__ == '__main__':
    root = Tk()
    calculator = Calculator(root)
    calculator.pack(fill='both', expand='1')
    DEBUG = False
    root.mainloop()