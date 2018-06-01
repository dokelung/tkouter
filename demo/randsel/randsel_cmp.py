import random

from tkinter import Tk, Frame, Entry, StringVar, BooleanVar, Button, Listbox, Menu
from tkinter.ttk import LabelFrame


class RandomSelector(Frame):

    def __init__(self, master):
        super().__init__(master)
        self.set_vars()
        self.set_frames()
        self.set_widgets()
        self.set_menu()
        self._items = []

    def set_vars(self):
        # tkinter variable
        self.item = StringVar()
        self.item.set('Item Name')
        self.hide = BooleanVar()
        self.hide.set(False)

    def set_frames(self):
        self.seladd_frame = Frame(self)
        self.itemframe = LabelFrame(self, text='Items')
        self.seladd_frame.pack()
        self.itemframe.pack(fill='both', expand=1)

    def set_widgets(self):
        self.entry = Entry(self.seladd_frame, width=30, textvariable=self.item)
        self.entry.pack(side='left')
        self.sel_button = Button(self.seladd_frame, text="Select", command=self.sel, width=8)
        self.add_button = Button(self.seladd_frame, text="Add", command=self.add, width=8)
        self.sel_button.pack(side='left')
        self.add_button.pack(side='left')
        self.listbox = Listbox(self.itemframe)
        self.listbox.pack(fill='both', expand=1)

    def set_menu(self):
        self.top_menu = Menu(self)
        self.cmd_menu = Menu(self.top_menu)
        self.cmd_menu.add(itemType='command', command=self.sel, label='Select')
        self.cmd_menu.add(itemType='command', command=self.add, label='Add')
        self.cmd_menu.add(itemType='separator')
        self.cmd_menu.add(itemType='command', command=self.quit, label='Quit')
        self.view_menu = Menu(self.top_menu)
        self.view_menu.add(itemType='checkbutton', label='Hide items', onvalue=1, offvalue=0, variable=self.hide, command=self.show)
        self.top_menu.add_cascade(menu=self.cmd_menu, label='Command', underline=0)
        self.top_menu.add_cascade(menu=self.view_menu, label='View', underline=0)
        self.master['menu'] = self.top_menu

    def sel(self):
        if self._items:
            self.item.set(random.choice(self._items))

    def add(self):
        self._items.append(self.item.get())
        self.listbox.insert('end', self.item.get())

    def show(self):
        if self.hide.get():
            self.itemframe.pack_forget()
        else:
            self.itemframe.pack(fill="both", expand="1")

    def quit(self):
        self.master.destroy()


if __name__ == '__main__':
    root = Tk()
    root.title('Random Selector')
    rs = RandomSelector(root)
    rs.pack()
    root.mainloop()