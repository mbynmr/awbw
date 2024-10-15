import time
import tkinter as tk
from tkinter.ttk import Notebook as notebook
from tkinter import filedialog, scrolledtext, CENTER
import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
# from tkinter.ttk import Combobox
# from tkinter import filedialog, scrolledtext
# from matplotlib.pyplot import close as matplotlibclose

from co import co_maker
from unit import unit_maker
from map import load_map


# todo sturm & lash movement
# todo snow & rain
# todo missiles (CO and player)
# todo captures
# todo damage:
#  check for ['apc', 'bboat', 'bbomb', 'lander', 'tcopter'] in attacks bcus 0 luck
#  check a 0 base damage isn't gaining luck as well if they can't physically fire. out of ammo 'aa' vs tank.
#  javier indirect defence needs to be BEFORE fire is called.
#  sonja attack order
#  kanbei & sonja counterattack damage


class Engine:
    """
    big main class for GUI (which deals with everything else)
    """

    def __init__(self):
        self.w = tk.Tk(className='awbw')
        # self.w.geometry("100x400")  # this is the worst. i hate it.
        self.w.state('zoomed')
        # self.w.resizable(False, False)

        # co & stats
        self.p1 = co_maker('jake')
        self.p1['army'] = 'yellowcomet'
        self.p2 = co_maker('jess')
        self.p2['army'] = 'purplelightning'
        # # units (no, these go in self.p1['units'])
        # self.p1u = []
        # self.p2u = []
        self.turns = 0
        self.days = 1
        self.map_info = ([], [], [], [], [], [])  # ownedby, stars, repair, production, access, special

        # tabs
        details_nb = notebook(self.w, width=370, height=900)
        details_nb.place(relx=0.8, rely=0.01)
        game_tab = tk.Frame(details_nb)
        details_nb.add(game_tab, text='Game')
        self.game_widgets(game_tab)
        co_tab = tk.Frame(details_nb)
        details_nb.add(co_tab, text='CO & unit')
        self.co_widgets(co_tab)
        page3 = tk.Frame(details_nb)
        details_nb.add(page3, text='debug')

        # figure display
        my_dpi = 102
        # fig_bg, self.ax_bg = plt.subplots(figsize=(1500 / my_dpi, 1000 / my_dpi), dpi=my_dpi)
        fig_bg, self.ax_bg = plt.subplots(figsize=(1077 / my_dpi, 839 / my_dpi), dpi=my_dpi)
        self.ax_bg.set_xticklabels([])
        self.ax_bg.set_yticklabels([])
        self.fig, self.axs = plt.subplots(figsize=(1077 / my_dpi, 839 / my_dpi), dpi=my_dpi)  # coordinate space axes

        self.canvas_bg = FigureCanvasTkAgg(fig_bg, master=self.w)
        self.canvas_bg.get_tk_widget().place(relx=0.4, rely=0.5, anchor=CENTER)
        # self.canvas = FigureCanvasTkAgg(self.fig, master=self.w)
        # self.canvas.get_tk_widget().place(relx=0.4, rely=0.5, anchor=CENTER)
        # # fig.canvas.callbacks.connect('pick_event', on_pick)
        # self.canvas.callbacks.connect('pick_event', on_pick)
        # self.fig.set_facecolor('none')
        # self.axs.set_facecolor('none')

        # other widgets
        mp = r"maps\Last Vigil.txt"
        self.map_path = tk.StringVar(self.w, value=mp)
        # map_nb = notebook(self.w)
        self.entry_path = tk.Entry(game_tab, textvariable=self.map_path, width=68)
        self.widgets()
        # print command redirect
        self.print_box = scrolledtext.ScrolledText(page3, width=43, height=50)
        self.print_box.place(relx=0.01, rely=0.02)
        self.Writer = Writer(self.print_box)

        self.w.after(60, self.update)
        self.w.mainloop()

    def widgets(self):
        parent = self.w
        tk.Button(parent, text='Close', command=self.close).place(relx=0.925, rely=0.925)
        self.entry_path.place(relx=0.25, rely=0.325)
        self.entry_path.xview_moveto(1)

    def game_widgets(self, parent):
        tk.Label(parent, text=f'Day: {self.days}').place(relx=0.25, rely=0.075)
        tk.Label(parent, text="Map path").place(relx=0.25, rely=0.275)
        tk.Button(parent, text='Path', command=self.select_path).place(relx=0.01, rely=0.315)
        tk.Button(parent, text='Load map', command=self.load_map).place(relx=0.01, rely=0.335)

    def co_widgets(self, parent):
        tk.Label(parent, text="CO stuff and unit details").place(relx=0.25, rely=0.275)
        # tk.Button(parent, text='COP', command=self.COP).place(relx=0.01, rely=0.335)
        # tk.Button(parent, text='SCOP', command=self.SCOP).place(relx=0.11, rely=0.335)

    def buttonfunc(self):
        print('ayy it workie')

    def update(self):
        # print('tick')
        # self.axs.imshow()
        # self.canvas.draw()
        self.w.after(60, self.update)

    def load_map(self):
        self.map_info = load_map(self.map_path.get())
        self.ax_bg.imshow(mpimg.imread(self.map_path.get().split('.txt')[0] + '.png'))
        self.canvas_bg.draw()
        print('background displayed!')

        self.load_map_units()
        dims = self.map_info[0].shape
        # self.axs = [plt.subplot(dims[0], dims[1], i + 1) for i in range(np.product(dims))]
        # for a in self.axs:
        #     a.set_xticklabels([])
        #     a.set_yticklabels([])
        #     a.set_aspect('equal')
        # plt.subplots_adjust(wspace=0, hspace=0)
        # self.canvas.draw()
        print('units displayed!')
        # print(self.axs)

    def load_map_units(self):
        # wipe units
        self.p1['units'] = []
        self.p2['units'] = []

        # load units from file
        with open(self.map_path.get().split('.txt')[0] + ' units.txt') as file:
            for line in file:
                army, typ, x, y, stars = line.split(', ')
                pos = (int(x), int(y))  # todo tuple not list, b careful
                if self.p1['army'] == army:
                    self.p1['units'].append(unit_maker(army, typ, self.p1, pos, stars, self.map_info[5][pos]))
                elif self.p2['army'] == army:
                    self.p2['units'].append(unit_maker(army, typ, self.p2, pos, stars, self.map_info[5][pos]))
                else:
                    raise ImportError(f"neither player is {army}")

    def select_path(self):
        self.map_path.set(filedialog.askdirectory())
        self.entry_path.xview_moveto(1)

    def turn_end(self):
        # in ai it checks all production first?

        self.turns += 1
        self.days = int(self.turns) + 1
        # check win conditions (day limit ig?)
        # todo check

        # p1's turn starts in this order ig
        # self.co1['power'] = 0
        self.p1['funds'] += self.p1['income']
        repair = 1
        fuel_resuuply = 1
        fuel_use = 1
        crashed_planes_check = 1

    def close(self):
        self.Writer.close()
        plt.close("all")
        self.w.destroy()


class Writer:
    def __init__(self, text_holder):
        self.text_holder = text_holder
        self.writestore = sys.stdout.write  # store it for use later when closing
        sys.stdout.write = self.write  # redirect "print" to the GUI

    def write(self, s):
        # s.split("\n")
        #  for loop over all those splits to make sure it is handled correctly?
        if s == '\n' or s == '':
            return
        if s[0:1] == '\r':  # todo this currently deletes the last tqdm line if the next line begins with \r
            s = s[1:]
            last_line = self.text_holder.get("end-2c linestart", "end-2c lineend")
            if len(last_line) >= 7:
                if not (last_line[0] == "[" and last_line[3] == ":" and last_line[6] == "]"):
                    self.text_holder.delete('end-2l', 'end-1l')  # replace previous line if it was tqdm
            self.text_holder.insert(tk.END, s + '\n')
        else:
            if s[0:1] == '\n':
                s = s[1:]
            self.text_holder.insert(tk.END,
                                    '[' + ':'.join([str(e).zfill(2) for e in time.localtime()[3:5]]) + ']' + s + '\n')
        self.text_holder.see(tk.END)

    def close(self):
        sys.stdout.write = self.writestore


def on_pick(event):
    print(event.x)
    print(event.y)
    print(event.button)
