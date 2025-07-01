import time
import tkinter as tk
# from tkinter.ttk import Combobox
from tkinter import scrolledtext
# import sys
# from matplotlib.pyplot import close as matplotlibclose

from XHKO import calc
from writer import Writer


def calcGUI():  # todo needs to be a class.
    w = tk.Tk(className='Piezo actuation and microphone detection')
    w.geometry("600x400")  # this is the worst. i hate it.
    w.resizable(False, False)

    # set up variables that can be used in buttons
    # self.running = tk.BooleanVar(self.w, value=False)
    pause_text = tk.StringVar(w, value='Pause')
    repeats = tk.IntVar(w, value=1)
    fit = tk.BooleanVar(w, value=True)
    t = tk.DoubleVar(w, value=0.2)

    # widgets before mainloop
    entry_path = tk.Entry(w, textvariable=pause_text, width=68)
    tempbox = tk.Entry(w, textvariable=pause_text, width=5)
    widgets(w, pause_text)

    # print command redirect
    print_box = scrolledtext.ScrolledText(w, width=52, height=13)
    print_box.place(relx=0.01, rely=0.39)

    writer = Writer(print_box)

    time_start = time.time()
    # w.after(600, update, False)
    w.mainloop()


def widgets(w, var):
    tk.Label(w, text="Temperature").place(relx=0.625, rely=0.01)
    tk.Entry(w, textvariable=var, width=5).place(relx=0.625, rely=0.19)
    tk.Button(w, text='Play raw signal', command=buttonfunc).place(relx=0.85, rely=0.075)


def buttonfunc():
    print('buttonfunc')


# def update(self, stop=None, i=[0]):
#     # credit for this neat mutable argument call counter trick goes to https://stackoverflow.com/a/23160861
#     if stop is not None:
#         i[0] -= i[0]  # reset counter
#         if not stop:
#             i[0] = 1
#     self.counter.set(i[0])
#     if i[0] != 0:
#         i[0] += 1
#         # try: () except task already using daq card error: (don't continue self.after(update))
#         # if self.temptrack.get():
#         #     self.temp.set(round_sig_figs(grab_temp(self.dev_temp.get(), self.chan_temp.get(), num=250), sig_fig=4))
#         # self.w.after(600 - int((time.time() - self.time_start) % 600), self.update)  # update on a rate of 100/min
