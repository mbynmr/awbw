import time
import tkinter as tk
from tkinter.ttk import Notebook as notebook
from tkinter import filedialog, scrolledtext, CENTER
import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
# from PIL import Image
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg  # , NavigationToolbar2Tk
# from tkinter.ttk import Combobox
# from tkinter import filedialog, scrolledtext
# from matplotlib.pyplot import close as matplotlibclose

from co import co_maker, activate_or_deactivate_power
from unit import unit_maker, name_to_filename
from map import load_map
from fire import fire, compatible, damage_calc_bounds
from pathfind import path_find


# todo sturm & lash movement
# todo snow & rain movement
# todo missiles (CO and player). sturm needs centred on a unit, others don't and scan top left: farright-down1-r-d-r-d
# todo sasha +100 per funds property (not labs, com, or 0 funds games lol)
# todo sasha SCOP turns 0.5*damage to funds
# todo sonja hiding unit hps and total value and damage calc numbers
# todo pipseam attacks & destruction
# todo fuel use + (hidden/submerged)
# todo unit cap (50 units per side?)
# todo lab cap win
# todo damage:
#  sonja SCOP attack order
#  kanbei & sonja counterattack damage

# reward:
#  ++++winning in as few turns as possible
#  +++winning
#  ++unit count advantage (prevents stalls where ai just builds units and hides them)
#  ++income advantage
#  +moving
#  +attacking
# punish:
#  ----losing
#  0.00001-CustomError (very very very small punish, we want it to try things before assuming it won't work)
# training idea: a set of stages it has to pass before moving on to the next
# give it a nearly winning position (like 10 of them?) where they just cap hq to win or kill 1 unit
# then level it up, make it so it needs 2 turns to win.
# then add some resistance (inf on hq to kill, then cap)
# then make it a few turns before victory
# then make it play itself from turn 0 lots of times on a few maps
# then let it choose CO and repeat
# play me!
# profit??
# play against sensei a lot bcus the "calcs" the ai has won't account for 9hp inf/mech spawns: spawns are always 10hp


class Engine:
    """
    big main class for GUI (which deals with everything else)
    """

    def __init__(self, render=False):
        self.render = render

        self.w = tk.Tk(className='awbw')
        self.w.geometry("1920x1030")  # this is the worst. i hate it.
        self.w.state('zoomed')
        # self.w.resizable(False, False)

        # tk.StringVar(self.w, value='single')
        # tk.IntVar(self.w, value=1)
        # tk.BooleanVar(self.w, value=True)
        # tk.DoubleVar(self.w, value=50)

        # co & stats
        self.p1 = co_maker('jake')
        self.p1['army'] = 'purplelightning'
        self.p1funds = tk.IntVar(self.w, value=0)
        self.p1unitc = tk.IntVar(self.w, value=0)
        self.p1unitv = tk.IntVar(self.w, value=0)
        self.p1income = tk.IntVar(self.w, value=0)
        self.p1charge = tk.IntVar(self.w, value=0)
        self.p1copcost = tk.IntVar(self.w, value=0)
        self.p1scopcost = tk.IntVar(self.w, value=0)
        self.p1combo = tk.StringVar(self.w)
        self.p1combo.trace('w', self.combochange)
        self.p1detailammo = tk.IntVar(self.w, value=0)
        self.p1detailfuel = tk.IntVar(self.w, value=0)
        self.p1detailstars = tk.IntVar(self.w, value=0)
        self.p1detailrange = tk.StringVar(self.w, value='1-1')

        self.p2 = co_maker('jess')
        self.p2['army'] = 'yellowcomet'
        self.p2name = self.p2['name']
        self.p2funds = tk.IntVar(self.w, value=0)
        self.p2unitc = tk.IntVar(self.w, value=0)
        self.p2unitv = tk.IntVar(self.w, value=0)
        self.p2income = tk.IntVar(self.w, value=0)
        self.p2charge = tk.IntVar(self.w, value=0)
        self.p2copcost = tk.IntVar(self.w, value=0)
        self.p2scopcost = tk.IntVar(self.w, value=0)
        self.p2combo = tk.StringVar(self.w)
        self.p2combo.trace('w', self.combochange)
        self.p2detailammo = tk.IntVar(self.w, value=0)
        self.p2detailfuel = tk.IntVar(self.w, value=0)
        self.p2detailstars = tk.IntVar(self.w, value=0)
        self.p2detailrange = tk.StringVar(self.w, value='1-1')

        self.winner = 0
        self.prodcombo = tk.StringVar(self.w)
        self.costs = {0: 1, 1: 1.2, 2: 1.4, 3: 1.6, 4: 1.8, 5: 2, 6: 2.2, 7: 2.4, 8: 2.6, 9: 2.8, 10: 2}
        self.turns = -1
        self.turns_display = tk.IntVar(self.w, value=int(self.turns))
        self.days = tk.IntVar(self.w, value=int(self.turns / 2) + 1)
        self.map_info = ([], [], [], [], [], [])  # ownedby, stars, repair, production, access, special
        self.von_bolt_missiles = []  # [[turn popped, (position popped)], [turn, (pos)], [turn, (pos)], ...] missiles

        # figure display
        if self.render:
            self.my_dpi = 102
            # self.figdims = [662, 515]  # *2 works for this map ig [1324, 1030] with max of roughly [1500, 1000]
            self.figdims = [662 * 2, 515 * 2]
            self.fig, self.ax = plt.subplots(figsize=(self.figdims[0] / self.my_dpi, self.figdims[1] / self.my_dpi),
                                             dpi=self.my_dpi)
            self.ax_display_move = []
            # self.ax.set(frame_on=False, bbox_inches='tight')
            self.canvas = FigureCanvasTkAgg(self.fig, master=self.w)
            self.map_bg = None
            # imageHand = Image.open('hand.png')
            # imageHead.paste(imageHand, (20, 40), imageHand)
            # # Convert the Image object into a TkPhoto object
            # tkimage = ImageTk.PhotoImage(imageHead)
            #
            # panel1 = tk.Label(root, image=tkimage)
            # panel1.grid(row=0, column=2, sticky=E)

        # tabs
        details_nb = notebook(self.w, width=370, height=900)
        details_nb.place(relx=0.8, rely=0.01)
        game_tab = tk.Frame(details_nb)
        details_nb.add(game_tab, text='Game')
        mp = r"maps\Last Vigil.txt"
        self.map_path = tk.StringVar(self.w, value=mp)
        self.entry_path = tk.Entry(game_tab, textvariable=self.map_path, width=55)
        self.game_widgets(game_tab)
        co_tab = tk.Frame(details_nb)
        details_nb.add(co_tab, text='CO & unit')
        self.scale_curx = tk.Scale(co_tab, from_=0, to=200, length=200, orient='horizontal')
        self.scale_cury = tk.Scale(co_tab, from_=0, to=200, length=100, orient='vertical')
        self.scale_desx = tk.Scale(co_tab, from_=0, to=200, length=200, orient='horizontal')
        self.scale_desy = tk.Scale(co_tab, from_=0, to=200, length=100, orient='vertical')
        self.scale_tarx = tk.Scale(co_tab, from_=0, to=200, length=200, orient='horizontal')
        self.scale_tary = tk.Scale(co_tab, from_=0, to=200, length=100, orient='vertical')
        self.p1cop = tk.Button(co_tab, text='COP', command=self.p1COP)
        self.p1scop = tk.Button(co_tab, text='SCOP', command=self.p1SCOP)
        self.p2cop = tk.Button(co_tab, text='COP', command=self.p2COP)
        self.p2scop = tk.Button(co_tab, text='SCOP', command=self.p2SCOP)
        self.p1cb = tk.ttk.Combobox(co_tab, width=23, textvariable=self.p1combo)
        self.p2cb = tk.ttk.Combobox(co_tab, width=23, textvariable=self.p2combo)
        self.productioncb = tk.ttk.Combobox(co_tab, width=13, textvariable=self.prodcombo)
        self.productioncb['values'] = [
            'aa', 'apc', 'arty', 'bcopter', 'bship', 'bboat', 'bbomb', 'bomber', 'carrier', 'cruiser', 'fighter', 'inf',
            'lander', 'med', 'mech', 'mega', 'missile', 'neo', 'pipe', 'recon', 'rocket', 'stealth', 'sub', 'tcopter',
            'tank'
        ]
        self.co_widgets(co_tab)
        page3 = tk.Frame(details_nb)
        details_nb.add(page3, text='debug')

        # other widgets
        # map_nb = notebook(self.w)
        self.widgets()
        # print command redirect
        self.print_box = scrolledtext.ScrolledText(page3, width=43, height=50)
        self.print_box.place(relx=0.01, rely=0.02)
        self.Writer = Writer(self.print_box)

        self.update(False)  # don't load map & units in update bcus it isn't loaded yet.
        # self.load_map()
        self.w.mainloop()

    def widgets(self):
        parent = self.w
        tk.Button(parent, text='Close', command=self.close).place(relx=0.925, rely=0.925)
        self.canvas.get_tk_widget().place(relx=0.4, rely=0.5, anchor=CENTER)
        self.fig.canvas.mpl_connect('button_press_event', on_pick)
        # self.canvas.callbacks.connect('pick_event', on_pick)
        # self.fig.set_facecolor('none')
        # self.ax.set_facecolor('none')

    def game_widgets(self, parent):
        tk.Label(parent, text="Map path").place(relx=0.05, rely=0.01)
        tk.Button(parent, text='Path', command=self.select_path).place(relx=0.9, rely=0.0365)
        self.entry_path.place(relx=0.05, rely=0.04)
        self.entry_path.xview_moveto(1)
        tk.Button(parent, text='Load map', command=self.load_map).place(relx=0.05, rely=0.07)
        tk.ttk.Separator(parent, orient='horizontal').place(relx=0, rely=0.11, relwidth=1, relheight=0.2)
        tk.Label(parent, text='Day: ', width=5, anchor="e").place(relx=0.15, rely=0.275)
        tk.Label(parent, textvariable=self.days, width=4, anchor="w").place(relx=0.3, rely=0.275)
        tk.Label(parent, text='Turn: ', width=5, anchor="e").place(relx=0.15, rely=0.25)
        tk.Label(parent, textvariable=self.turns_display, width=4, anchor="w").place(relx=0.3, rely=0.25)
        tk.Button(parent, text='End turn', command=self.turn_end).place(relx=0.15, rely=0.3)

    def co_widgets(self, parent):
        #todo check anchor=e and w for all of them. need to add a number rly to check!
        # "CO controls go here (power buttons + bars + details ig)
        tk.ttk.Separator(parent, orient='vertical').place(relx=0.5, rely=0, relwidth=0.001, relheight=0.49)

        armies = {
            'neutral': 'n', 'amberblaze': 'ab', 'blackhole': 'bh', 'bluemoon': 'bm', 'browndesert': 'bd',
            'greenearth': 'ge', 'jadesun': 'js', 'orangestar': 'os',
            'redfire': 'rf', 'yellowcomet': 'yc', 'greysky': 'gs', 'cobaltice': 'ci', 'pinkcosmos': 'pc',
            'tealgalaxy': 'tg', 'purplelightning': 'pl',
            'acidrain': 'ar', 'whitenova': 'wn', 'azureasteroid': 'aa', 'noireclipse': 'ne'
        }
        tk.Label(parent, text=self.p1['name'], anchor="w").place(relx=0.05, rely=0.02)
        tk.Label(parent, text=armies[self.p1['army']], anchor="w").place(relx=0.05, rely=0.05)
        tk.Label(parent, textvariable=self.p1funds, anchor="w").place(relx=0.05, rely=0.08)
        tk.Label(parent, textvariable=self.p1unitc, width=7, anchor="e").place(relx=0.30, rely=0.02)
        tk.Label(parent, textvariable=self.p1unitv, width=7, anchor="e").place(relx=0.30, rely=0.05)
        tk.Label(parent, textvariable=self.p1income, width=7, anchor="e").place(relx=0.30, rely=0.08)
        tk.Label(parent, text=self.p2['name'], width=6, anchor="w").place(relx=0.52, rely=0.02)
        tk.Label(parent, text=armies[self.p2['army']], width=6, anchor="w").place(relx=0.52, rely=0.05)
        tk.Label(parent, textvariable=self.p2funds, width=7, anchor="w").place(relx=0.52, rely=0.08)
        tk.Label(parent, textvariable=self.p2unitc, width=7, anchor="e").place(relx=0.80, rely=0.02)
        tk.Label(parent, textvariable=self.p2unitv, width=7, anchor="e").place(relx=0.80, rely=0.05)
        tk.Label(parent, textvariable=self.p2income, width=7, anchor="e").place(relx=0.80, rely=0.08)
        tk.ttk.Separator(parent, orient='horizontal').place(relx=0, rely=0.11, relwidth=1, relheight=0.001)

        # COP and SCOP buttons with number above button
        tk.Label(parent, textvariable=self.p1charge, width=7, anchor="w").place(relx=0.05, rely=0.13)
        tk.Label(parent, textvariable=self.p1copcost, width=7, anchor="w").place(relx=0.05, rely=0.17)
        tk.Label(parent, textvariable=self.p1scopcost, width=7, anchor="e").place(relx=0.3, rely=0.17)
        self.p1cop.place(relx=0.05, rely=0.2)
        self.p1scop.place(relx=0.35, rely=0.2)
        tk.Label(parent, textvariable=self.p2charge, width=7, anchor="e").place(relx=0.80, rely=0.13)
        tk.Label(parent, textvariable=self.p2copcost, width=7, anchor="w").place(relx=0.55, rely=0.17)
        tk.Label(parent, textvariable=self.p2scopcost, width=7, anchor="e").place(relx=0.80, rely=0.17)
        self.p2cop.place(relx=0.55, rely=0.2)
        self.p2scop.place(relx=0.85, rely=0.2)
        tk.ttk.Separator(parent, orient='horizontal').place(relx=0, rely=0.25, relwidth=1, relheight=0.001)

        self.p1cb.place(relx=0.03, rely=0.27)
        self.p2cb.place(relx=0.53, rely=0.27)
        # calc button (never needs to check if it's an allowed move, firing has no consequence just prints hps)
        tk.Button(parent, text='Calc selection 1 on 2', command=self.calc1).place(relx=0.1, rely=0.3)
        tk.Button(parent, text='Calc selection 2 on 1', command=self.calc2).place(relx=0.6, rely=0.3)

        tk.Label(parent, text='ammo', anchor="w").place(relx=0.05, rely=0.35)
        tk.Label(parent, text='fuel', anchor="w").place(relx=0.05, rely=0.38)
        tk.Label(parent, text='stars', anchor="w").place(relx=0.05, rely=0.41)
        tk.Label(parent, text='range', anchor="w").place(relx=0.05, rely=0.44)
        tk.Label(parent, textvariable=self.p1detailammo, width=7, anchor="e").place(relx=0.30, rely=0.35)
        tk.Label(parent, textvariable=self.p1detailfuel, width=7, anchor="e").place(relx=0.30, rely=0.38)
        tk.Label(parent, textvariable=self.p1detailstars, width=7, anchor="e").place(relx=0.30, rely=0.41)
        tk.Label(parent, textvariable=self.p1detailrange, width=7, anchor="e").place(relx=0.30, rely=0.44)
        tk.Label(parent, text='ammo', width=6, anchor="w").place(relx=0.52, rely=0.35)
        tk.Label(parent, text='fuel', width=6, anchor="w").place(relx=0.52, rely=0.38)
        tk.Label(parent, text='stars', width=7, anchor="w").place(relx=0.52, rely=0.41)
        tk.Label(parent, text='range', width=7, anchor="w").place(relx=0.52, rely=0.44)
        tk.Label(parent, textvariable=self.p2detailammo, width=7, anchor="e").place(relx=0.80, rely=0.35)
        tk.Label(parent, textvariable=self.p2detailfuel, width=7, anchor="e").place(relx=0.80, rely=0.38)
        tk.Label(parent, textvariable=self.p2detailstars, width=7, anchor="e").place(relx=0.80, rely=0.41)
        tk.Label(parent, textvariable=self.p2detailrange, width=7, anchor="e").place(relx=0.80, rely=0.44)

        tk.ttk.Separator(parent, orient='horizontal').place(relx=0, rely=0.49, relwidth=1, relheight=0.001)

        self.scale_curx.place(relx=0.12, rely=0.49)
        self.scale_cury.place(relx=0.01, rely=0.53)
        tk.Label(parent, text='current (x, y)').place(relx=0.14, rely=0.535)
        tk.Button(parent, text='Display move (doesn\'t wait)', command=self.display_move).place(relx=0.2, rely=0.56)
        tk.Button(parent, text='Unload (doesn\'t wait)', command=self.unload).place(relx=0.2, rely=0.60)
        self.scale_desx.place(relx=0.12, rely=0.64)
        self.scale_desy.place(relx=0.01, rely=0.68)
        tk.Label(parent, text='final (x, y)').place(relx=0.14, rely=0.685)
        tk.Button(parent, text='Move & join/load/cap/wait', command=self.move).place(relx=0.2, rely=0.71)
        tk.Button(parent, text='Move & (un/)hide', command=self.hide).place(relx=0.2, rely=0.75)
        self.scale_tarx.place(relx=0.12, rely=0.79)
        self.scale_tary.place(relx=0.01, rely=0.83)
        tk.Label(parent, text='target (x, y)').place(relx=0.14, rely=0.835)
        tk.Button(parent, text='Move & fire', command=self.fire).place(relx=0.2, rely=0.86)
        tk.Button(parent, text='Move & repair', command=self.repair).place(relx=0.2, rely=0.90)
        # tk.ttk.Separator(parent, orient='horizontal').place(relx=0, rely=0.8, relwidth=1, relheight=0.001)

        # tk.ttk.Separator(parent, orient='vertical').place(relx=0.68, rely=0.49, relwidth=0.001, relheight=0.2)
        tk.ttk.Separator(parent, orient='horizontal').place(relx=0.68, rely=0.64, relwidth=0.32, relheight=0.001)
        tk.Button(parent, text='Delete', command=self.delete_coords).place(relx=0.74, rely=0.52)
        tk.Button(parent, text='Build', command=self.build).place(relx=0.74, rely=0.56)
        self.productioncb.place(relx=0.7, rely=0.6)

    def update(self, draw=None):
        if self.winner != 0:
            if self.turns % 2 == 0:
                raise WinError(f"winner!!!! p1 in {self.turns} turns")
            else:
                raise WinError(f"winner!!!! p2 in {self.turns} turns")
        self.p1funds.set(self.p1['funds'])
        self.p1unitc.set(len(self.p1['units']))
        v = 0
        # if not sonja bcus she hides her total unit value!
        for e in self.p1['units']:
            display_hp = int(1 + e['hp'] / 10)
            v += int(e['value'] * display_hp / 10)  # full value * visible hp
        self.p1unitv.set(v)

        self.p2funds.set(self.p2['funds'])
        self.p2unitc.set(len(self.p2['units']))
        v = 0
        for e in self.p2['units']:
            display_hp = int(1 + e['hp'] / 10)
            v += int(e['value'] * display_hp / 10)  # full value * visible hp / 10
        self.p2unitv.set(v)

        # visual things below this point!

        self.charge_update()
        self.p1copcost.set(self.p1['COP'] * self.costs[self.p1['starcost']] * 9000)
        self.p1scopcost.set(self.p1['SCOP'] * self.costs[self.p1['starcost']] * 9000)
        self.p2copcost.set(self.p2['COP'] * self.costs[self.p2['starcost']] * 9000)
        self.p2scopcost.set(self.p2['SCOP'] * self.costs[self.p2['starcost']] * 9000)
        self.combobox_update()

        # unit visual display
        if draw is None and self.render:
            dims = self.map_info[0].shape
            r = 1 / dims[1]
            self.fig.clear()  # find a better way than this. deleting and remaking every time isn't the best
            self.fig.add_axes([0, 0, 1, 1]).imshow(self.map_bg)
            plt.setp(plt.gca(), xticks=[], yticks=[])  # hide axes
            # might be bottom-left centred. not sure
            for unit in self.p1['units']:
                if unit['position'] != (-10, -10):
                    # /home/nathaniel/PycharmProjects/awbw/units/pc{name_to_filename(unit['type'])}.gif
                    # img = mpimg.imread(f"units/pc{name_to_filename(unit['type'])}.gif")
                    self.fig.add_axes(
                        [r * unit['position'][1], 1 - (14 / 11) * (r * unit['position'][0] + 0.95 * r), r, r]
                    ).imshow(mpimg.imread(f"units/pc{name_to_filename(unit['type'])}.gif"))
                    plt.gca().axis("off")
                    # plt.setp(plt.gca(), xticks=[], yticks=[])  # hide ticks but keep white space and black outline
                    # plt.gca().patch.set_alpha(0)  # hide white space
            for unit in self.p2['units']:
                if unit['position'] != (-10, -10):
                    # /home/nathaniel/PycharmProjects/awbw/units/bd{name_to_filename(unit['type'])}.gif
                    # img = mpimg.imread(f"units/bd{name_to_filename(unit['type'])}.gif")
                    self.fig.add_axes(
                        [r * unit['position'][1], 1 - (14 / 11) * (r * unit['position'][0] + 0.95 * r), r, r]
                    ).imshow(mpimg.imread(f"units/bd{name_to_filename(unit['type'])}.gif"))
                    plt.gca().axis("off")
            self.canvas.draw()

    def load_map(self):
        self.map_info = load_map(self.map_path.get())
        self.scale_curx.configure(to=self.map_info[0].shape[1] - 1)
        self.scale_cury.configure(to=self.map_info[0].shape[0] - 1)
        self.scale_desx.configure(to=self.map_info[0].shape[1] - 1)
        self.scale_desy.configure(to=self.map_info[0].shape[0] - 1)
        self.scale_tarx.configure(to=self.map_info[0].shape[1] - 1)
        self.scale_tary.configure(to=self.map_info[0].shape[0] - 1)
        # ownedby, stars, repair, production, access, special
        armies = [
            'neutral', 'amberblaze', 'blackhole', 'bluemoon', 'browndesert', 'greenearth', 'jadesun', 'orangestar',
            'redfire', 'yellowcomet', 'greysky', 'cobaltice', 'pinkcosmos', 'tealgalaxy', 'purplelightning',
            'acidrain', 'whitenova', 'azureasteroid', 'noireclipse'
        ]
        for e in np.argwhere(self.map_info[0] != 0):  # 0 is neutral
            if armies[self.map_info[0][e[0], e[1]]] == self.p1['army']:
                self.p1['properties'] += 1
            elif armies[self.map_info[0][e[0], e[1]]] == self.p2['army']:
                self.p2['properties'] += 1
        self.income_update()
        plt.subplots_adjust(wspace=0, hspace=0)
        plt.tight_layout()
        # print('background displayed!')
        # self.ax.axis("off")
        self.map_bg = mpimg.imread(self.map_path.get().split('.txt')[0] + '.png')
        # self.map_bg = mpimg.imread('/home/nathaniel/PycharmProjects/awbw/maps/Last Vigil.png')

        self.load_map_units()
        self.turn_end()

    def charge_update(self):
        self.p1charge.set(self.p1['charge'])
        self.p2charge.set(self.p2['charge'])

    def combobox_update(self):
        # combobox dropdown list thing
        s = []
        # if not sonja bcus she hides her unit hps!
        for unit in self.p1['units']:
            if unit['position'] != (-10, -10):
                s.append(f"{int(1 + unit['hp'] / 10)} {unit['type']} ({unit['position'][1]}, {unit['position'][0]})"
                         f" m:{unit['move']}")
            else:
                s.append(f"{int(1 + unit['hp'] / 10)} {unit['type']} '(loaded)' m:{unit['move']}")
        self.p1cb['values'] = s
        if len(s) > 0:
            self.p1cb.current(0)
        s = []
        for unit in self.p2['units']:
            if unit['position'] != (-10, -10):
                s.append(f"{int(1 + unit['hp'] / 10)} {unit['type']} ({unit['position'][1]}, {unit['position'][0]})"
                         f" m:{unit['move']}")
            else:
                s.append(f"{int(1 + unit['hp'] / 10)} {unit['type']} '(loaded)' m:{unit['move']}")
        self.p2cb['values'] = s
        if len(s) > 0:
            self.p2cb.current(0)

        self.combochange()

    def combochange(self, *args):
        if len(self.p1cb['values']) > 0:
            u1 = self.return_unit(pos_from_combobox(self.p1combo))
            if u1 is not None:
                self.p1detailammo.set(u1['ammo'])
                self.p1detailfuel.set(u1['fuel'])
                self.p1detailstars.set(u1['Dtr'])
                self.p1detailrange.set(f"{u1['range'][0]}-{u1['range'][1]}")
        if len(self.p2cb['values']) > 0:
            u2 = self.return_unit(pos_from_combobox(self.p2combo))
            if u2 is not None:
                self.p2detailammo.set(u2['ammo'])
                self.p2detailfuel.set(u2['fuel'])
                self.p2detailstars.set(u2['Dtr'])
                self.p2detailrange.set(f"{u2['range'][0]}-{u2['range'][1]}")

    def display_move(self):
        pos = self.get_poses_from_UI(1)
        unit = self.return_unit(pos)
        if unit is None:
            raise CustomError(f"coords {pos} don't correspond to a unit")
        if unit['move'] >= 1:
            self.display_movement(unit)
        else:
            self.display_movement(None)

    def display_movement(self, unit=None):
        for ax in self.ax_display_move:
            if ax in self.fig.axes:  # find out whether they have already been cleared
                ax.remove()  # clear first
        self.ax_display_move = []
        if unit is not None:
            for coords in self.check_movement(unit, unit['position']):
                # x = coords[0]
                # y = coords[1]
                # print(f"({x}, {y})")  # these are all allowed positions, it seems to work good but it spams prints
                r = 1 / self.map_info[0].shape[1]
                self.ax_display_move.append(self.fig.add_axes(
                    [r * coords[1], 1 - (14 / 11) * (r * coords[0] + 0.95 * r), r, r]
                ))
                img = np.ones([9, 9, 4]) * [0, 0.4, 0.8, 0.8]
                img[1:-1, 1:-1, :] = [0, 0.4, 0.8, 0.3]
                self.ax_display_move[-1].imshow(img)
                self.ax_display_move[-1].axis("off")
        self.canvas.draw()

    def load_map_units(self):
        # wipe units
        self.p1['units'] = []
        self.p2['units'] = []

        # load units from file
        # with open('') as file:
        # /home/nathaniel/PycharmProjects/awbw/maps/Last Vigil units.txt
        with open(self.map_path.get().split('.txt')[0] + ' units.txt') as file:
            for line in file:
                army, typ, x, y = line.split(', ')
                pos = (int(y), int(x))  # todo tuple not list, b careful
                if self.p1['army'] == army:
                    self.p1['units'].append(unit_maker(army, typ, self.p1, pos,
                                                       self.map_info[1][pos], self.map_info[5][pos]))
                elif self.p2['army'] == army:
                    self.p2['units'].append(unit_maker(army, typ, self.p2, pos,
                                                       self.map_info[1][pos], self.map_info[5][pos]))
                else:
                    raise CustomError(f"neither player is {army}")

    def calc1(self):
        calc(pos_from_combobox(self.p1combo), pos_from_combobox(self.p2combo), self.p1['units'], self.p2['units'])

    def calc2(self):
        calc(pos_from_combobox(self.p2combo), pos_from_combobox(self.p1combo), self.p2['units'], self.p1['units'])

    def return_unit(self, pos=None):
        if pos is None:
            return None
        for unit in self.p1['units']:
            if unit['position'] == pos:
                return unit
        for unit in self.p2['units']:
            if unit['position'] == pos:
                return unit
        return None

    def delete_unit(self, u):
        if u is None:
            return
        if len(u['loaded']) > 0:
            for u in u['loaded']:
                self.delete_unit(u)  # before deleting the unit, delete all units loaded inside it! (calls itself wowwe)
                # could be an inf on a tcopter on a cruiser
                # could be an inf on an apc on a lander
        if u in self.p1['units']:
            self.p1['units'].remove(u)
        elif u in self.p2['units']:
            self.p2['units'].remove(u)
        else:
            raise CustomError("oh no big bad, crash crash crash")

    def check_movement(self, u, pos1, pos2=None):
        # returns: movecost (0-11 (fighter with +2 move) is possible, -1 is impossible)
        # todo sturm, lash SCOP, snow, rain affect this function

        if pos2 is not None:
            if pos1 == pos2:
                return 0

        access = self.map_info[4]
        # 0: road, 1: plain, 2: wood, 3: river, 4: shoal, 5: sea, 6: pipe, 7: port, 8: base, 9: mountain, 10: reef
        grid = np.zeros_like(access)
        # special = self.map_info[5]
        # # special - 0: misc, 1: pipeseam, 2: missile, 3: road, 4: plain, 5: urban
        match u['tread']:
            case 'treads':
                grid = np.where(access == 0, 1, 12)  # road
                grid = np.where(access == 1, 1, grid)  # plain
                grid = np.where(access == 2, 2, grid)  # wood
                grid = np.where(access == 4, 1, grid)  # shoal
                grid = np.where(access == 7, 1, grid)  # port
                grid = np.where(access == 8, 1, grid)  # base
            case 'air':
                grid = np.where(access != 6, 1, 12)  # just not pipe :>
            case 'sea':
                grid = np.where(access == 5, 1, 12)
                grid = np.where(access == 10, 2, grid)
            case 'lander':
                grid = np.where(access == 5, 1, 12)
                grid = np.where(access == 10, 2, grid)
                grid = np.where(access == 4, 1, grid)
            case 'inf':
                grid = np.where(access == 0, 1, 12)
                grid = np.where(access == 1, 1, grid)
                grid = np.where(access == 2, 1, grid)
                grid = np.where(access == 3, 2, grid)  # river
                grid = np.where(access == 4, 1, grid)
                grid = np.where(access == 7, 1, grid)
                grid = np.where(access == 8, 1, grid)
                grid = np.where(access == 9, 2, grid)  # mtn
            case 'mech':
                grid = np.where(access == 0, 1, 12)
                grid = np.where(access == 1, 1, grid)
                grid = np.where(access == 2, 1, grid)
                grid = np.where(access == 3, 1, grid)
                grid = np.where(access == 4, 1, grid)
                grid = np.where(access == 7, 1, grid)
                grid = np.where(access == 8, 1, grid)
                grid = np.where(access == 9, 1, grid)
            case 'tyre':
                grid = np.where(access == 0, 1, 12)
                grid = np.where(access == 1, 2, grid)
                grid = np.where(access == 2, 3, grid)
                grid = np.where(access == 4, 1, grid)
                grid = np.where(access == 7, 1, grid)
                grid = np.where(access == 8, 1, grid)
            case 'pipe':
                grid = np.where(access == 6, 1, 12)

        if u['army'] == self.p1['army']:
            enemy_units = self.p2['units']
        else:
            enemy_units = self.p1['units']
        # add enemy units as blockers
        for enemy_unit in enemy_units:
            if enemy_unit['position'] != (-10, -10):
                grid[enemy_unit['position']] = 12

        if pos2 is None:
            all_costs = path_find(grid, pos1)  # evaluate costs of the whole grid from start position
            all_costs = np.where(all_costs <= u['move'], all_costs, 100)
            return np.argwhere(all_costs <= u['fuel'])  # return indexes where movement is allowed to
        movecost = path_find(grid, pos1, pos2)
        if movecost > u['move']:  # costs too much movement so it is impossible
            return -2
        elif movecost > u['fuel']:
            return -3
        return movecost

    def action(self, pos, desired_pos, desired_action='wait', target_pos=None):
        if pos == (-10, -10):
            raise CustomError("loaded units can't do anything")
        u1 = self.return_unit(pos)  # unit making the move
        if u1 is None:
            raise CustomError(f"somehow no unit is at position {pos} to make the move")
        elif self.turns % 2 == 0:  # even turn means p1 turn
            if u1['army'] != self.p1['army']:
                raise CustomError("selected unit is not owned by the player who's turn it is!")
            else:
                sami = self.p1['name'] == 'sami'  # this player sami
                javier = self.p2['name'] == 'javier'  # other player javier
        else:  # odd turn means p2 turn
            if u1['army'] != self.p2['army']:
                raise CustomError("selected unit is not owned by the player who's turn it is!")
            else:
                sami = self.p2['name'] == 'sami'  # this player sami
                javier = self.p1['name'] == 'javier'  # other player javier
        if u1['move'] < 1:
            raise CustomError("unit cannot move anymore")
        u1store = u1.copy()

        movecost = self.check_movement(u1, u1['position'], desired_pos)
        if movecost < 0:
            if movecost == -3:
                raise CustomError(f"not enough fuel")
            elif movecost == -2:
                raise CustomError(f"not enough move")
            else:
                raise CustomError(f"move is impossible for some reason")
        # elif movecost >

        u2 = self.return_unit(target_pos)  # unit being fired on
        if u2 is not None:
            u2store = u2.copy()
        else:
            u2store = None
        if pos == desired_pos:
            u3 = None  # no u3 if u3 is the same unit as u1
        else:
            u1['capture'] = 0  # set this unit's capture value to 0 because it isn't in the same place anymore
            u3 = self.return_unit(desired_pos)  # unit at desired position

            if u3 is not None:  # if there is actually a unit there, see what we can do
                if u3['army'] != u1['army']:  # trapped in fog (other traps are possible)
                    raise CustomError(f"can't move, enemy {u3['type']} already there")
                else:  # a friendly unit is on that space. load, join, or fail movement
                    if desired_action != 'wait':  # don't allow join/load with fire/hide/repair
                        raise CustomError(f"can't do that! Friendly {u3['type']} already in that space")
                    elif u3['type'] == u1['type'] and u3['hp'] <= 89:
                        if len(u1['loaded']) != 0 or len(u3['loaded']) != 0:  # transports with units in cannot join
                            raise CustomError(f"can't join: units are loaded in the joiner or joinee")
                        display_hp1 = int(1 + u1['hp'] / 10)
                        display_hp3 = int(1 + u3['hp'] / 10)
                        u3['hp'] += u1['hp']
                        u3['ammo'] += u1['ammo']
                        u3['fuel'] += u1['fuel']
                        u3['move'] = 0  # joined units aren't allowed to move this turn nomatter what
                        u1['hp'] = -1  # kill this unit the same way firing kills it

                        # joined units have a minimum cap of their VISIBLE health adding. I think?
                        # 5(1) + 18(2) = 23(3)
                        # 5(1) + 12(2) = 20(3) NOT 17(2)
                        # 45(5) + 40(5) = 95(10)
                        # 55(6) + 40(5) = 105-99(10)
                        if u3['hp'] > 99:  # if the unit went over 99 hp
                            u3['hp'] = 99  # cap it
                        elif int(1 + (u3['hp']) / 10) < display_hp1 + display_hp3:
                            u3['hp'] = (display_hp1 + display_hp3 - 1) * 10  # bump it up a bit to add display hps
                        types = {
                            'aa': [9, 60],
                            'apc': [0, 60],
                            'arty': [9, 50],
                            'bcopter': [6, 99],
                            'bship': [9, 99],
                            'bboat': [-1, 50],
                            'bbomb': [0, 45],
                            'bomber': [9, 99],
                            'carrier': [9, 99],
                            'cruiser': [9, 99],
                            'fighter': [9, 99],
                            'inf': [-1, 99],
                            'lander': [0, 99],
                            'med': [8, 50],
                            'mech': [3, 70],
                            'mega': [3, 50],
                            'missile': [6, 50],
                            'neo': [9, 99],
                            'pipe': [9, 99],
                            'recon': [-1, 80],
                            'rocket': [6, 50],
                            'stealth': [6, 60],
                            'sub': [6, 60],
                            'tcopter': [0, 99],
                            'tank': [9, 70]
                        }  # ammo, fuel
                        max_ammo = types[u3['type']][0]
                        max_fuel = types[u3['type']][1]
                        u3['ammo'] = max_ammo if u3['ammo'] > max_ammo else u3['ammo']  # cap it
                        u3['fuel'] = max_fuel if u3['fuel'] > max_fuel else u3['fuel']  # cap it

                    elif u3['type'] in ['apc', 'bboat', 'lander', 'tcopter', 'carrier', 'cruiser']:
                        check = u3['loaded']  # attempt loading
                        match u3['type']:
                            # apc is 1x space, foot
                            # bboat is 2x space, foot
                            # lander is 2x space, land unit
                            # tcopter is 1x space, foot
                            # carrier is 2x space, air
                            # cruiser is 2x space, copter (b or t)
                            case 'apc':
                                if len(u3['loaded']) == 0 and u1['type'] in ['inf', 'mech']:
                                    u3['loaded'] = u1
                            case 'bboat':
                                if len(u3['loaded']) < 2 and u1['type'] in ['inf', 'mech']:
                                    u3['loaded'].append(u1)
                            case 'lander':
                                if len(u3['loaded']) < 2 and u1['tread'] not in ['pipe', 'air', 'sea', 'lander']:
                                    u3['loaded'].append(u1)
                            case 'tcopter':
                                if len(u3['loaded']) == 0 and u1['type'] in ['inf', 'mech']:
                                    u3['loaded'].append(u1)
                            case 'carrier':
                                if len(u3['loaded']) < 2 and u1['tread'] == 'air':
                                    u3['loaded'].append(u1)
                            case 'cruiser':
                                if len(u3['loaded']) < 2 and u1['type'] in ['bcopter', 'tcopter']:
                                    u3['loaded'].append(u1)
                        if u3['loaded'] == check:
                            # doesn't load even tho u tried
                            raise CustomError(
                                f"can't load {u1['type']} into {u3['type']} with loaded: {len(u3['loaded'])}")
                        else:
                            u1['position'] = (-10, -10)  # all loaded units go to these coords off the map
                    else:
                        # not allowed to enter that space if it's not a transport or the same unit below 10hp
                        raise CustomError(f"can't move, friendly {u3['type']} already there")

        # no enemy unit is in the way, the action is allowed
        match desired_action:

            case 'wait':  # cap. if not cap: no action
                if u1['type'] in ['inf', 'mech']:  # if this unit is footsoldier
                    if u1['army'] != [
                        'neutral', 'amberblaze', 'blackhole', 'bluemoon', 'browndesert', 'greenearth', 'jadesun',
                        'orangestar', 'redfire', 'yellowcomet', 'greysky', 'cobaltice', 'pinkcosmos', 'tealgalaxy',
                        'purplelightning', 'acidrain', 'whitenova', 'azureasteroid', 'noireclipse'
                    ][self.map_info[0][desired_pos]] and self.map_info[5][desired_pos] == 5:
                        # if tile is not owned by friendly, terrain is urban
                        if sami:
                            u1['capture'] += int(int(1 + u1['hp'] / 10) * 1.5)
                        else:
                            u1['capture'] += int(1 + u1['hp'] / 10)
                        if u1['capture'] >= 20:  # capture happened!
                            self.capture_success(desired_pos)

            case 'fire':
                if target_pos is None:
                    raise CustomError("why is no target position selected for firing on?")
                if u2 is None:
                    raise CustomError(f"no unit is at target position {target_pos}")
                elif u2['army'] == u1['army']:
                    raise CustomError("can't fire on friendlies!")
                else:
                    indr = ['arty', 'bship', 'carrier', 'missile', 'pipe', 'rocket']
                    desired_to_target_dist = abs((desired_pos[0] - target_pos[0]) + (desired_pos[1] - target_pos[1]))
                    # we don't care about diagonal distance here, just grid distance
                    if u1['type'] not in indr:
                        if desired_to_target_dist != 1:
                            raise CustomError(f"attack not valid. {u1['type']} is not an indirect and"
                                              f" moving to {desired_pos} is not next to the target {target_pos}")
                    elif abs((pos[0] - desired_pos[0]) + (pos[1] - desired_pos[1])) != 0:
                        raise CustomError("attack not valid. indirects have to stay where they are to shoot!")
                    elif desired_to_target_dist > u1['range'][1] or desired_to_target_dist < u1['range'][0]:
                        raise CustomError(f"{desired_to_target_dist} is out of range for unit with range {u1['range']}")

                    # distance checks are complete, now let's try unit attack checks
                    if not compatible(u1, u2):
                        raise CustomError(f"attack not valid: {u1['type']} with ammo {u1['ammo']} on {u2['type']}")
                    counter = True
                    if u1['type'] in indr or u2['type'] in indr:
                        counter = False  # indirects don't get countered or perform counters even if it's valid
                    elif not compatible(u2, u1):
                        counter = False
                    u1['Dtr'] = self.map_info[1][desired_pos]  # 1: stars
                    u1['terr'] = self.map_info[5][desired_pos]  # 5: special (plain=4)
                    if u1['type'] in indr and javier:  # if javier owns this
                        u2['Dv'] += 40
                    u1, u2 = fire(u1, u2, counter)
                    if u1['type'] in indr and javier:  # reset javier
                        u2['Dv'] -= 40

            case 'repair':
                if target_pos is None:
                    raise CustomError("why is no target position selected for repairing?")
                if u2 is None:
                    raise CustomError(f"no unit is at target position {target_pos} for repairing")
                elif u2['army'] != u1['army']:
                    raise CustomError("can't repair non-friendlies!")
                else:
                    u2['hp'] += 10
                    if u2['hp'] > 99:
                        u2['hp'] = 99
                        types = {
                            'aa': [9, 60],
                            'apc': [0, 60],
                            'arty': [9, 50],
                            'bcopter': [6, 99],
                            'bship': [9, 99],
                            'bboat': [-1, 50],
                            'bbomb': [0, 45],
                            'bomber': [9, 99],
                            'carrier': [9, 99],
                            'cruiser': [9, 99],
                            'fighter': [9, 99],
                            'inf': [-1, 99],
                            'lander': [0, 99],
                            'med': [8, 50],
                            'mech': [3, 70],
                            'mega': [3, 50],
                            'missile': [6, 50],
                            'neo': [9, 99],
                            'pipe': [9, 99],
                            'recon': [-1, 80],
                            'rocket': [6, 50],
                            'stealth': [6, 60],
                            'sub': [6, 60],
                            'tcopter': [0, 99],
                            'tank': [9, 70]
                        }  # ammo, fuel
                        u2['ammo'] = types[u2['type']][0]
                        u2['fuel'] = types[u2['type']][1]

            case 'hide':
                u1['hidden'] = not u1['hidden']  # wow this one is nice and simple :>
                # if i do fog then forests mess with this. be careful! (and i guess normal fog too)

        # all actions if successful move and set fuel
        u1['position'] = desired_pos  # everything went smoothly let's update position :D
        u1['move'] = 0  # unit has used it's turn, set move to 0
        u1['fuel'] = u1['fuel'] - movecost
        u1['Dtr'] = self.map_info[1][desired_pos]
        u1['terr'] = self.map_info[5][desired_pos]

        # charge calculations
        if desired_action == 'fire':
            if u1['hp'] >= 0:
                u1_dmg_value = int((int(1 + u1store['hp'] / 10) - int(1 + u1['hp'] / 10)) * u1['value'])
            else:
                u1_dmg_value = int(int(1 + u1store['hp'] / 10) * u1['value'])
            if u2['hp'] >= 0:
                u2_dmg_value = int((int(1 + u2store['hp'] / 10) - int(1 + u2['hp'] / 10)) * u2['value'])
            else:
                u2_dmg_value = int(int(1 + u2store['hp'] / 10) * u2['value'])
            if self.turns % 2 == 0:  # even turn means p1 turn
                self.p1['charge'] += u1_dmg_value + int(0.5 * u2_dmg_value)
                self.p2['charge'] += u2_dmg_value + int(0.5 * u1_dmg_value)
            else:
                self.p2['charge'] += u1_dmg_value + int(0.5 * u2_dmg_value)
                self.p1['charge'] += u2_dmg_value + int(0.5 * u1_dmg_value)

        # manage units that need deleting
        for u in [u1, u2, u3]:
            if u is not None:
                if u['hp'] < 0:
                    self.delete_unit(u)

        self.update()  # after the move is done, update the board!

    # def mange_units_after_action(self, u1, u2, u3):
    #     # upon destruction, check for loaded units and destroy them in the normal unit list :>
    #     # (don't get charge for loaded units when the carrier is destroyed)
    #
    #     # self.delete_unit(u1store)
    #     # self.delete_unit(u2store)
    #     # self.delete_unit(u3store)  # handles None unit just fine
    #
    #     for u in [u1, u2, u3]:
    #         if u is not None:
    #             if u['hp'] < 0:
    #                 self.delete_unit(u)

    def get_poses_from_UI(self, num):
        match num:
            case 1:
                return self.scale_cury.get(), self.scale_curx.get()
            case 2:
                return (self.scale_cury.get(), self.scale_curx.get()),\
                    (self.scale_desy.get(), self.scale_desx.get())
            case 3:
                return (self.scale_cury.get(), self.scale_curx.get()),\
                    (self.scale_desy.get(), self.scale_desx.get()),\
                    (self.scale_tary.get(), self.scale_tarx.get())

    # def get_poses_from_UI_old(self):
    #     if self.turns % 2 == 0:  # even turn means p1 turn
    #         pos = pos_from_combobox(self.p1combo)
    #         target_pos = pos_from_combobox(self.p2combo)
    #     else:  # odd turn means p2 turn
    #         pos = pos_from_combobox(self.p2combo)
    #         target_pos = pos_from_combobox(self.p1combo)
    #     return pos, (self.scale_desy.get(), self.scale_desx.get()), target_pos

    def fire(self):
        pos, desired_pos, target_pos = self.get_poses_from_UI(3)
        try:
            self.action(pos, desired_pos, desired_action='fire', target_pos=target_pos)
        except CustomError as Err:
            print(Err)

    def move(self):
        pos, desired_pos = self.get_poses_from_UI(2)
        try:
            self.action(pos, desired_pos, desired_action='wait')
        except CustomError as Err:
            print(Err)

    def hide(self):
        pos, desired_pos = self.get_poses_from_UI(2)
        try:
            self.action(pos, desired_pos, desired_action='hide')
        except CustomError as Err:
            print(Err)

    def repair(self):
        pos, desired_pos, target_pos = self.get_poses_from_UI(3)
        try:
            self.action(pos, desired_pos, desired_action='repair', target_pos=target_pos)
        except CustomError as Err:
            print(Err)

    def build(self):
        pos = self.get_poses_from_UI(1)

        if self.turns % 2 == 0:
            army = self.p1['army']
            funds = self.p1['funds']
        else:
            army = self.p2['army']
            funds = self.p2['funds']

        if army != [
            'neutral', 'amberblaze', 'blackhole', 'bluemoon', 'browndesert', 'greenearth', 'jadesun',
            'orangestar', 'redfire', 'yellowcomet', 'greysky', 'cobaltice', 'pinkcosmos', 'tealgalaxy',
            'purplelightning', 'acidrain', 'whitenova', 'azureasteroid', 'noireclipse'
        ][self.map_info[0][pos]]:  # if that space (production hopefully) owned by this turn's player
            raise CustomError("this player doesn't own that space")

        typ = self.prodcombo.get()
        typfail = True
        match self.map_info[3][pos]:  # combination base + land unit, port + sea unit,...
            case 1:  # base
                if typ in ['aa', 'apc', 'arty', 'inf',
                           'med', 'mech', 'mega', 'missile', 'neo', 'pipe', 'recon', 'rocket',
                           'tank']:
                    typfail = False
            case 2:  # port
                if typ in ['bship', 'bboat', 'carrier', 'cruiser', 'lander', 'sub']:
                    typfail = False
            case 3:  # airport
                if typ in ['bcopter', 'bbomb', 'bomber', 'fighter', 'stealth', 'tcopter']:
                    typfail = False
            case _:  # 0 = none, any building that isn't production (hq hehe)
                raise CustomError("no production at that location")
        if typfail:
            raise CustomError("bases make land/pipe, ports make sea, airports make air. wrong combo attempted")

        if self.return_unit(pos) is not None:  # if unit is there
            raise CustomError("unit already in that location")

        costs = {
            'aa': 8000,
            'apc': 5000,
            'arty': 6000,
            'bcopter': 9000,
            'bship': 28000,
            'bboat': 7500,
            'bbomb': 25000,
            'bomber': 22000,
            'carrier': 30000,
            'cruiser': 18000,
            'fighter': 20000,
            'inf': 1000,
            'lander': 12000,
            'med': 16000,
            'mech': 3000,
            'mega': 28000,
            'missile':  12000,
            'neo': 22000,
            'pipe': 20000,
            'recon': 4000,
            'rocket': 15000,
            'stealth': 24000,
            'sub': 20000,
            'tcopter': 5000,
            'tank': 7000
        }
        if funds < costs[typ]:  # if funds for this turn's player
            raise CustomError(f"unit costs {costs[typ]} but player only has funds {funds}")

        # todo if unit cap hasn't been hit

        # build the unit with 0 move so it can't instantly move this turn.
        if army == self.p1['army']:
            self.p1['units'].append(unit_maker(army, typ, self.p1, pos, move=0))
            self.p1['funds'] -= costs[typ]
        elif army == self.p2['army']:
            self.p2['units'].append(unit_maker(army, typ, self.p2, pos, move=0))
            self.p2['funds'] -= costs[typ]

        self.update()

    def delete_coords(self):
        pos = self.get_poses_from_UI(1)
        u = self.return_unit(pos)
        if u is None:
            raise CustomError("no unit at that location")
        if u['move'] < 1:
            raise CustomError("can't delete: unit has already moved")
        if self.turns % 2 == 0 and u['army'] == self.p1['army']:
            self.delete_unit(u)
        elif self.turns % 2 == 1 and u['army'] == self.p2['army']:
            self.delete_unit(u)
        else:
            raise CustomError("can't delete: that unit isn't owned by the player who's turn it is!")
        self.update()

    def unload(self):
        pos = self.get_poses_from_UI(1)
        # todo this isn't finished. all it does is resupply the lander!
        #  the choice of unit to unload needs to be somewhere in UI, then that fed in here.
        #  the destination of the unloaded unit also needs to be in UI (target pos should b good)
        u = self.return_unit(pos)
        # self.delete_unit(u)  # why was a delete here? bad idea uhh

        types = {
            'aa': [9, 60],
            'apc': [0, 60],
            'arty': [9, 50],
            'bcopter': [6, 99],
            'bship': [9, 99],
            'bboat': [-1, 50],
            'bbomb': [0, 45],
            'bomber': [9, 99],
            'carrier': [9, 99],
            'cruiser': [9, 99],
            'fighter': [9, 99],
            'inf': [-1, 99],
            'lander': [0, 99],
            'med': [8, 50],
            'mech': [3, 70],
            'mega': [3, 50],
            'missile': [6, 50],
            'neo': [9, 99],
            'pipe': [9, 99],
            'recon': [-1, 80],
            'rocket': [6, 50],
            'stealth': [6, 60],
            'sub': [6, 60],
            'tcopter': [0, 99],
            'tank': [9, 70]
        }  # ammo, fuel
        u['ammo'] = types[u['type']][0]
        u['fuel'] = types[u['type']][1]
        # set fuel, ammo to full
        if self.p1['army'] == u['army']:
            self.p1['units'].append(u)
        else:
            self.p2['units'].append(u)

        self.update()

    def capture_success(self, position):
        armies = [
            'neutral', 'amberblaze', 'blackhole', 'bluemoon', 'browndesert', 'greenearth', 'jadesun',
            'orangestar', 'redfire', 'yellowcomet', 'greysky', 'cobaltice', 'pinkcosmos', 'tealgalaxy',
            'purplelightning', 'acidrain', 'whitenova', 'azureasteroid', 'noireclipse'
        ]
        if self.turns % 2 == 0:
            self.p1['properties'] += 1
            self.map_info[0][position] = armies.index(self.p1['army'])
            enemy_army = self.p2['army']
        else:
            self.p2['properties'] += 1
            self.map_info[0][position] = armies.index(self.p2['army'])
            enemy_army = self.p1['army']

        if enemy_army == [
                    'neutral', 'amberblaze', 'blackhole', 'bluemoon', 'browndesert', 'greenearth', 'jadesun',
                    'orangestar', 'redfire', 'yellowcomet', 'greysky', 'cobaltice', 'pinkcosmos', 'tealgalaxy',
                    'purplelightning', 'acidrain', 'whitenova', 'azureasteroid', 'noireclipse'
                ][self.map_info[0][position]]:  # check whether enemy owned this property before
            if self.map_info[1][position] == 4 and self.map_info[5][position] == 5:  # if hq
                player_wins_by_hq_cap = 1  # todo
            if self.turns % 2 == 0:
                self.p2['properties'] -= 1
            else:
                self.p1['properties'] -= 1

        # update a little bit (we don't render owning properties that's hard :>)
        self.income_update()

    def income_update(self):
        self.p1['income'] = 0
        self.p2['income'] = 0
        armies = [
            'neutral', 'amberblaze', 'blackhole', 'bluemoon', 'browndesert', 'greenearth', 'jadesun', 'orangestar',
            'redfire', 'yellowcomet', 'greysky', 'cobaltice', 'pinkcosmos', 'tealgalaxy', 'purplelightning',
            'acidrain', 'whitenova', 'azureasteroid', 'noireclipse'
        ]
        for e in np.argwhere(self.map_info[0] != 0):
            if self.map_info[2][e[0], e[1]] != 0:  # if it can repair it provides income :>
                if armies[self.map_info[0][e[0], e[1]]] == self.p1['army']:
                    self.p1['income'] += 1000
                elif armies[self.map_info[0][e[0], e[1]]] == self.p2['army']:
                    self.p2['income'] += 1000
                else:
                    raise CustomError("Somehow a property is not neutral and not either army. huh")
        self.p1income.set(self.p1['income'])
        self.p2income.set(self.p2['income'])

    def p1COP(self):
        if self.p1['name'] != 'von bolt':
            # normal power penalty is it costing 20% extra is only on cartridge?
            if self.p1['charge'] >= self.p1['COP'] * self.costs[self.p1['starcost']] * 9000 and self.p1['power'] == 0:
                self.p1['charge'] -= self.p1['COP'] * self.costs[self.p1['starcost']] * 9000
                self.p1, self.p2 = activate_or_deactivate_power(self.p1, self.p2, 1)
                self.update()
            else:
                print("not enough charge or power already activated!")
        else:
            print("von bolt doesn't have a COP!")

    def p1SCOP(self):
        if self.p1['charge'] >= self.p1['SCOP'] * self.costs[self.p1['starcost']] * 9000 and self.p1['power'] == 0:
            self.p1['charge'] -= self.p1['SCOP'] * self.costs[self.p1['starcost']] * 9000
            self.p1, self.p2 = activate_or_deactivate_power(self.p1, self.p2, 2)
            self.update()
        else:
            print("not enough charge or power already activated!")

    def p2COP(self):
        if self.p2['name'] != 'von bolt':
            if self.p2['charge'] >= self.p2['COP'] * self.costs[self.p2['starcost']] * 9000 and self.p2['power'] == 0:
                self.p2['charge'] -= self.p2['COP'] * self.costs[self.p2['starcost']] * 9000
                self.p2, self.p1 = activate_or_deactivate_power(self.p2, self.p1, 1)
                self.update()
            else:
                print("not enough charge or power already activated!")
        else:
            print("von bolt doesn't have a COP!")

    def p2SCOP(self):
        if self.p2['charge'] >= self.p2['SCOP'] * self.costs[self.p2['starcost']] * 9000 and self.p2['power'] == 0:
            self.p2['charge'] -= self.p2['SCOP'] * self.costs[self.p2['starcost']] * 9000
            self.p2, self.p1 = activate_or_deactivate_power(self.p2, self.p1, 2)
            self.update()
        else:
            print("not enough charge or power already activated!")

    def turn_end(self):
        if len(self.map_info[0]) == 0:
            print("load a map before ending turn please")
            return
        self.turns += 1
        self.turns_display.set(self.turns)
        self.days.set(int(self.turns / 2) + 1)
        if self.turns % 2 == 1:  # going to p2 from p1
            self.p1, self.p2 = self.turn_swap(self.p1, self.p2)
        else:  # going to p1 from p2
            self.p2, self.p1 = self.turn_swap(self.p2, self.p1)
        self.update()

    def turn_swap(self, p1, p2):  # p1 -> p2 turn end/start
        # check win conditions (day limit ig?)
        p1win = False
        if p1['properties'] > 23:
            p1win = True
        if self.days.get() > 40:  # turn limit 40 days?
            if p1['properties'] > 15:
                p1win = True
        if self.days.get() >= 2 and len(p2['units']) == 0:  # if p2 has no units and it's not the start of the game
            p1win = True
        if p1win:
            self.winner = p1['army']

        p2, p1 = activate_or_deactivate_power(p2, p1, -p2['power'])  # p2's power gets deactivated if it was on
        p2['funds'] += p2['income']
        repair = 1  # todo rachel +1 repair
        fuel_and_ammo_resuuply = 1
        fuel_use = 1
        crashed_planes_check = 1
        if p1['name'] == 'von bolt':
            if self.von_bolt_missiles[-1][0] == self.turns - 1:
                pos = self.von_bolt_missiles[-1][1]
                units_move_set_0 = 1  # only enemy get stunned, even though self damage is done? check in a game ig?
        self.income_update()
        self.update()
        return p1, p2  # not needed  # todo not needed :D

    def select_path(self):
        self.map_path.set(filedialog.askdirectory())
        self.entry_path.xview_moveto(1)

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
    print(f"({event.x}, {event.y}) {event.button}")


def calc(pos1, pos2, units1, units2):
    for unit in units1:
        if unit['position'] == pos1:
            u1 = unit

    for unit in units2:
        if unit['position'] == pos2:
            u2 = unit
    # print(u1)
    # print(u2)
    print(damage_calc_bounds(u1, u2))


def pos_from_combobox(combobox_option):
    pos = combobox_option.get().split(' ')[2:4]
    return int(pos[1][:-1]), int(pos[0][1:-1])


def buttonfunc():
    print('ayy it workie')


class CustomError(Exception):
    def __init__(self, message):
        super().__init__(message)
        # if I want extra arguments, go to https://stackoverflow.com/a/1319675


class WinError(Exception):
    def __init__(self, message):
        super().__init__(message)
