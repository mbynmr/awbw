
import platform
import time
import numpy as np
import tkinter as tk
from tkinter.ttk import Notebook as notebook
from tkinter import filedialog, scrolledtext, CENTER
import tkinter.font as tkFont
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg  # , NavigationToolbar2Tk
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

from engine import Engine, calc, CustomError
from unit import name_to_filename
from co import co_maker
from writer import Writer


class GUI:
    """
    big main class for GUI. can open instances of Engine
    """

    def __init__(self):
        self.w = tk.Tk(className='awbw')
        self.w.geometry("1920x1030")  # this is the worst. i hate it.
        # self.w.resizable(False, False)

        # font setup
        default_font = tkFont.nametofont("TkDefaultFont")
        # default_font.configure(family='Arial')  # todo ?? i can set size fine but not family?
        default_font.configure(size=10)
        self.w.option_add("*Font", default_font)

        # variable setup
        if platform.system() == 'Linux':
            mp = r"/home/nathaniel/PycharmProjects/awbw/maps/Last Vigil.txt"
            rp = r"/home/nathaniel/PycharmProjects/awbw/replays/yyyy_mm_dd_hh_mm_ss.txt"
        else:
            mp = r"maps/Last Vigil.txt"
            rp = r"replays/yyyy_mm_dd_hh_mm_ss.txt"
            self.w.state('zoomed')
        self.replayfile = None
        self.costs = {0: 1, 1: 1.2, 2: 1.4, 3: 1.6, 4: 1.8, 5: 2, 6: 2.2, 7: 2.4, 8: 2.6, 9: 2.8, 10: 2}
        self.i = 0
        self.lines = []
        # GUI variables
        self.prodcombo = tk.StringVar(self.w)
        self.turns_display = tk.IntVar(self.w, value=0)
        self.days = tk.IntVar(self.w, value=int(1))
        # co1
        self.p1name = tk.StringVar(self.w, value='co1 name')
        self.p1army = tk.StringVar(self.w, value='co1 army')
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
        # co2
        self.p2name = tk.StringVar(self.w, value='co2 name')
        self.p2army = tk.StringVar(self.w, value='co2 army')
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

        # figure display
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
        self.widgets()  # general widgets

        # tabs
        details_nb = notebook(self.w, width=370, height=900)
        details_nb.place(relx=0.8, rely=0.01)
        game_tab = tk.Frame(details_nb)
        details_nb.add(game_tab, text='Game')
        co_tab = tk.Frame(details_nb)
        details_nb.add(co_tab, text='CO & unit')
        page3 = tk.Frame(details_nb)
        details_nb.add(page3, text='debug')
        calc_nb = tk.Frame(details_nb)
        details_nb.add(calc_nb, text='calcs')
        # game
        self.map_path = tk.StringVar(self.w, value=mp)
        self.replay_path = tk.StringVar(self.w, value=rp)
        self.entry_map_path = tk.Entry(game_tab, textvariable=self.map_path, width=44)
        self.entry_replay_path = tk.Entry(game_tab, textvariable=self.replay_path, width=44)
        self.game_widgets(game_tab)
        # co tab
        self.scale_curx = tk.Scale(co_tab, from_=0, to=200, length=200, orient='horizontal')
        self.scale_cury = tk.Scale(co_tab, from_=0, to=200, length=100, orient='vertical')
        self.scale_desx = tk.Scale(co_tab, from_=0, to=200, length=200, orient='horizontal')
        self.scale_desy = tk.Scale(co_tab, from_=0, to=200, length=100, orient='vertical')
        self.scale_tarx = tk.Scale(co_tab, from_=0, to=200, length=200, orient='horizontal')
        self.scale_tary = tk.Scale(co_tab, from_=0, to=200, length=100, orient='vertical')
        self.p1cop = tk.Button(co_tab, text='COP', command=self.cop)
        self.p1scop = tk.Button(co_tab, text='SCOP', command=self.scop)
        self.p2cop = tk.Button(co_tab, text='COP', command=self.cop)
        self.p2scop = tk.Button(co_tab, text='SCOP', command=self.scop)
        self.p1cb = tk.ttk.Combobox(co_tab, width=23, textvariable=self.p1combo)
        self.p2cb = tk.ttk.Combobox(co_tab, width=23, textvariable=self.p2combo)
        self.productioncb = tk.ttk.Combobox(co_tab, width=13, textvariable=self.prodcombo)
        production = [
            'aa', 'apc', 'arty', 'bcopter', 'bship', 'bboat', 'bbomb', 'bomber', 'carrier', 'cruiser', 'fighter', 'inf',
            'lander', 'med', 'mech', 'mega', 'missile', 'neo', 'pipe', 'recon', 'rocket', 'stealth', 'sub', 'tcopter',
            'tank'
        ]
        self.productioncb['values'] = production
        self.co_widgets(co_tab)
        # calc tab
        self.calc_widgets(calc_nb)
        # debug tab
        # print command redirect
        self.print_box = scrolledtext.ScrolledText(page3, width=43, height=50)
        self.print_box.place(relx=0.01, rely=0.02)
        self.Writer = Writer(self.print_box)

        # wrapping up :D
        self.E = None

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
        tk.Button(parent, text='Path', command=self.select_map_path).place(relx=0.9, rely=0.0365)
        self.entry_map_path.place(relx=0.05, rely=0.04)
        self.entry_map_path.xview_moveto(1)
        tk.Button(parent, text='Live play with this map', command=self.live_play).place(relx=0.05, rely=0.07)
        tk.Label(parent, text="Replay path").place(relx=0.05, rely=0.41)
        tk.Button(parent, text='Path', command=self.select_replay_path).place(relx=0.9, rely=0.4365)
        self.entry_replay_path.place(relx=0.05, rely=0.44)
        self.entry_replay_path.xview_moveto(1)
        tk.Button(parent, text='Load replay', command=self.replay_view).place(relx=0.05, rely=0.47)
        tk.Button(parent, text='Next move', command=self.replay_move).place(relx=0.35, rely=0.47)
        tk.Button(parent, text='Next turn', command=self.replay_turn).place(relx=0.35, rely=0.50)
        tk.ttk.Separator(parent, orient='horizontal').place(relx=0, rely=0.11, relwidth=1, relheight=0.2)
        tk.Label(parent, text='Day: ', width=5, anchor="e").place(relx=0.15, rely=0.275)
        tk.Label(parent, textvariable=self.days, width=4, anchor="w").place(relx=0.3, rely=0.275)
        tk.Label(parent, text='Turn: ', width=5, anchor="e").place(relx=0.15, rely=0.25)
        tk.Label(parent, textvariable=self.turns_display, width=4, anchor="w").place(relx=0.3, rely=0.25)
        tk.Button(parent, text='End turn', command=self.turn_end).place(relx=0.15, rely=0.3)

    def co_widgets(self, parent):
        # CO controls go here (power buttons + bars + details ig)
        tk.ttk.Separator(parent, orient='vertical').place(relx=0.5, rely=0, relwidth=0.001, relheight=0.49)

        tk.Label(parent, textvariable=self.p1name, width=7, anchor="w").place(relx=0.05, rely=0.02)
        tk.Label(parent, textvariable=self.p1army, width=7, anchor="w").place(relx=0.05, rely=0.05)
        tk.Label(parent, textvariable=self.p1funds, width=7, anchor="w").place(relx=0.05, rely=0.08)
        tk.Label(parent, textvariable=self.p1unitc, width=7, anchor="e").place(relx=0.30, rely=0.02)
        tk.Label(parent, textvariable=self.p1unitv, width=7, anchor="e").place(relx=0.30, rely=0.05)
        tk.Label(parent, textvariable=self.p1income, width=7, anchor="e").place(relx=0.30, rely=0.08)
        tk.Label(parent, textvariable=self.p2name, width=7, anchor="w").place(relx=0.52, rely=0.02)
        tk.Label(parent, textvariable=self.p2army, width=7, anchor="w").place(relx=0.52, rely=0.05)
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
        tk.Button(parent, text='Move & repair/supply', command=self.repair).place(relx=0.2, rely=0.90)
        # tk.ttk.Separator(parent, orient='horizontal').place(relx=0, rely=0.8, relwidth=1, relheight=0.001)

        # tk.ttk.Separator(parent, orient='vertical').place(relx=0.68, rely=0.49, relwidth=0.001, relheight=0.2)
        tk.ttk.Separator(parent, orient='horizontal').place(relx=0.68, rely=0.64, relwidth=0.32, relheight=0.001)
        tk.Button(parent, text='Delete', command=self.delete_coords).place(relx=0.74, rely=0.52)
        tk.Button(parent, text='Build', command=self.build).place(relx=0.74, rely=0.56)
        self.productioncb.place(relx=0.7, rely=0.6)

    def calc_widgets(self, parent):
        tk.Button(parent, text='Calc selection 1 on 2', command=self.calc1).place(relx=0.1, rely=0.3)
        tk.Button(parent, text='Calc selection 2 on 1', command=self.calc2).place(relx=0.6, rely=0.3)
        # todo multi-hit calc
        # todo customise each hit of multi-hit
        # todo customise number of hits
        # todo probabilities :>

    def select_map_path(self):
        self.map_path.set(filedialog.askdirectory())
        self.entry_map_path.xview_moveto(1)

    def select_replay_path(self):
        self.replay_path.set(filedialog.askopenfilename())
        self.entry_replay_path.xview_moveto(1)

    def get_poses_from_UI(self, num):
        match num:
            case 1:
                return self.scale_cury.get(), self.scale_curx.get()
            case 2:
                return (self.scale_cury.get(), self.scale_curx.get()), \
                    (self.scale_desy.get(), self.scale_desx.get())
            case 3:
                return (self.scale_cury.get(), self.scale_curx.get()), \
                    (self.scale_desy.get(), self.scale_desx.get()), \
                    (self.scale_tary.get(), self.scale_tarx.get())

    def combochange(self, *args):
        if len(self.p1cb['values']) > 0:
            u1 = self.E.return_unit(pos_from_combobox(self.p1combo))
            if u1 is not None:
                self.p1detailammo.set(u1['ammo'])
                self.p1detailfuel.set(u1['fuel'])
                self.p1detailstars.set(u1['Dtr'])
                self.p1detailrange.set(f"{u1['range'][0]}-{u1['range'][1]}")
        if len(self.p2cb['values']) > 0:
            u2 = self.E.return_unit(pos_from_combobox(self.p2combo))
            if u2 is not None:
                self.p2detailammo.set(u2['ammo'])
                self.p2detailfuel.set(u2['fuel'])
                self.p2detailstars.set(u2['Dtr'])
                self.p2detailrange.set(f"{u2['range'][0]}-{u2['range'][1]}")

    def combobox_update(self):
        # combobox dropdown list thing
        s = []
        # if not sonja bcus she hides her unit hps!
        for unit in self.E.p1['units']:
            if unit['position'] != (-10, -10):
                s.append(f"{int(1 + unit['hp'] / 10)} {unit['type']} ({unit['position'][1]}, {unit['position'][0]})"
                         f" m:{unit['move']}")
            else:
                s.append(f"{int(1 + unit['hp'] / 10)} {unit['type']} '(loaded)' m:{unit['move']}")
        self.p1cb['values'] = s
        if len(s) > 0:
            self.p1cb.current(0)
        s = []
        for unit in self.E.p2['units']:
            if unit['position'] != (-10, -10):
                s.append(f"{int(1 + unit['hp'] / 10)} {unit['type']} ({unit['position'][1]}, {unit['position'][0]})"
                         f" m:{unit['move']}")
            else:
                s.append(f"{int(1 + unit['hp'] / 10)} {unit['type']} '(loaded)' m:{unit['move']}")
        self.p2cb['values'] = s
        if len(s) > 0:
            self.p2cb.current(0)

        self.combochange()

    def charge_update(self):
        self.p1charge.set(self.E.p1['charge'])
        self.p1copcost.set(self.E.p1['COP'] * self.costs[self.E.p1['starcost']] * 9000)
        self.p1scopcost.set(self.E.p1['SCOP'] * self.costs[self.E.p1['starcost']] * 9000)
        self.p2charge.set(self.E.p2['charge'])
        self.p2copcost.set(self.E.p2['COP'] * self.costs[self.E.p2['starcost']] * 9000)
        self.p2scopcost.set(self.E.p2['SCOP'] * self.costs[self.E.p2['starcost']] * 9000)

    def load_map(self):
        self.E.load_map(self.map_path.get())
        self.scale_curx.configure(to=self.E.map_info[0].shape[1] - 1)
        self.scale_cury.configure(to=self.E.map_info[0].shape[0] - 1)
        self.scale_desx.configure(to=self.E.map_info[0].shape[1] - 1)
        self.scale_desy.configure(to=self.E.map_info[0].shape[0] - 1)
        self.scale_tarx.configure(to=self.E.map_info[0].shape[1] - 1)
        self.scale_tary.configure(to=self.E.map_info[0].shape[0] - 1)
        plt.subplots_adjust(wspace=0, hspace=0)
        plt.tight_layout()
        # print('background displayed!')
        # self.ax.axis("off")
        self.map_bg = mpimg.imread(self.map_path.get().split('.txt')[0] + '.png')
        # self.map_bg = mpimg.imread('/home/nathaniel/PycharmProjects/awbw/maps/Last Vigil.png')

    def update(self, draw=None):
        armies = {
            'neutral': 'n', 'amberblaze': 'ab', 'blackhole': 'bh', 'bluemoon': 'bm', 'browndesert': 'bd',
            'greenearth': 'ge', 'jadesun': 'js', 'orangestar': 'os',
            'redfire': 'rf', 'yellowcomet': 'yc', 'greysky': 'gs', 'cobaltice': 'ci', 'pinkcosmos': 'pc',
            'tealgalaxy': 'tg', 'purplelightning': 'pl',
            'acidrain': 'ar', 'whitenova': 'wn', 'azureasteroid': 'aa', 'noireclipse': 'ne'
        }
        self.p1name.set(self.E.p1['name'])
        self.p1army.set(armies[self.E.p1['army']])
        self.p1funds.set(self.E.p1['funds'])
        self.p1income.set(self.E.p1['income'])
        self.p1unitc.set(len(self.E.p1['units']))
        v = 0
        # if not sonja bcus she hides her total unit value!
        for e in self.E.p1['units']:
            display_hp = int(1 + e['hp'] / 10)
            v += int(e['value'] * display_hp / 10)  # full value * visible hp
        self.p1unitv.set(v)

        self.p2name.set(self.E.p2['name'])
        self.p2army.set(armies[self.E.p2['army']])
        self.p2funds.set(self.E.p2['funds'])
        self.p2income.set(self.E.p2['income'])
        self.p2unitc.set(len(self.E.p2['units']))
        v = 0
        for e in self.E.p2['units']:
            display_hp = int(1 + e['hp'] / 10)
            v += int(e['value'] * display_hp / 10)  # full value * visible hp / 10
        self.p2unitv.set(v)

        self.charge_update()
        self.combobox_update()

        # unit display on axes
        if draw is None:
            dims = self.E.map_info[0].shape
            r = 1 / dims[1]
            self.fig.clear()  # find a better way than this. deleting and remaking every time isn't the best
            self.fig.add_axes([0, 0, 1, 1]).imshow(self.map_bg)
            plt.setp(plt.gca(), xticks=[], yticks=[])  # hide axes
            # might be bottom-left centred. not sure
            for unit in self.E.p1['units']:
                if unit['position'] != (-10, -10):
                    # /home/nathaniel/PycharmProjects/awbw/units/pc{name_to_filename(unit['type'])}.gif
                    # img = mpimg.imread(f"units/pc{name_to_filename(unit['type'])}.gif")
                    self.fig.add_axes(
                        [r * unit['position'][1], 1 - (14 / 11) * (r * unit['position'][0] + 0.95 * r), r, r]
                    ).imshow(mpimg.imread(f"units/pc{name_to_filename(unit['type'])}.gif"))
                    plt.gca().axis("off")
                    # plt.setp(plt.gca(), xticks=[], yticks=[])  # hide ticks but keep white space and black outline
                    # plt.gca().patch.set_alpha(0)  # hide white space
            for unit in self.E.p2['units']:
                if unit['position'] != (-10, -10):
                    # /home/nathaniel/PycharmProjects/awbw/units/bd{name_to_filename(unit['type'])}.gif
                    # img = mpimg.imread(f"units/bd{name_to_filename(unit['type'])}.gif")
                    self.fig.add_axes(
                        [r * unit['position'][1], 1 - (14 / 11) * (r * unit['position'][0] + 0.95 * r), r, r]
                    ).imshow(mpimg.imread(f"units/bd{name_to_filename(unit['type'])}.gif"))
                    plt.gca().axis("off")
            self.canvas.draw()

    def calc1(self):
        calc(pos_from_combobox(self.p1combo), pos_from_combobox(self.p2combo), self.E.p1['units'], self.E.p2['units'])

    def calc2(self):
        calc(pos_from_combobox(self.p2combo), pos_from_combobox(self.p1combo), self.E.p2['units'], self.E.p1['units'])

    def display_move(self):
        pos = self.get_poses_from_UI(1)
        unit = self.E.return_unit(pos)
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
            for coords in self.E.check_movement(unit, unit['position']):
                # x = coords[0]
                # y = coords[1]
                # print(f"({x}, {y})")  # these are all allowed positions, it seems to work good but it spams prints
                r = 1 / self.E.map_info[0].shape[1]
                self.ax_display_move.append(self.fig.add_axes(
                    [r * coords[1], 1 - (14 / 11) * (r * coords[0] + 0.95 * r), r, r]
                ))
                img = np.ones([9, 9, 4]) * [0, 0.4, 0.8, 0.8]
                img[1:-1, 1:-1, :] = [0, 0.4, 0.8, 0.3]
                self.ax_display_move[-1].imshow(img)
                self.ax_display_move[-1].axis("off")
        self.canvas.draw()

    def build(self, pos=None, typ=None):
        if pos is None:
            pos = self.get_poses_from_UI(1)
            typ = self.productioncb.get()
        try:
            self.E.build(pos, typ)
        except CustomError as Err:
            print(Err)
        else:
            self.update()
            if self.replayfile is not None:
                self.replayfile.write(f"build {pos[1]} {pos[0]} {typ}" + '\n')

    def fire(self, pos=None, desired_pos=None, target_pos=None):
        if pos is None:
            pos, desired_pos, target_pos = self.get_poses_from_UI(3)
        try:
            self.E.action(pos, desired_pos, desired_action='fire', target_pos=target_pos)
        except CustomError as Err:
            print(Err)
        else:
            self.update()
            if self.replayfile is not None:
                self.replayfile.write(
                    f"fire {pos[1]} {pos[0]} {desired_pos[1]} {desired_pos[0]} {target_pos[1]} {target_pos[0]}" + '\n')

    def move(self, pos=None, desired_pos=None):
        if pos is None:
            pos, desired_pos = self.get_poses_from_UI(2)
        try:
            self.E.action(pos, desired_pos, desired_action='wait')
        except CustomError as Err:
            print(Err)
        else:
            self.update()
            if self.replayfile is not None:
                self.replayfile.write(f"wait {pos[1]} {pos[0]} {desired_pos[1]} {desired_pos[0]}" + '\n')

    def hide(self, pos=None, desired_pos=None, target_pos=None):
        if pos is None:
            pos, desired_pos, target_pos = self.get_poses_from_UI(3)
        try:
            self.E.action(pos, desired_pos, desired_action='hide')
        except CustomError as Err:
            print(Err)
        else:
            self.update()
            if self.replayfile is not None:
                self.replayfile.write(
                    f"hide {pos[1]} {pos[0]} {desired_pos[1]} {desired_pos[0]} {target_pos[1]} {target_pos[0]}" + '\n')

    def repair(self, pos=None, desired_pos=None, target_pos=None):
        if pos is None:
            pos, desired_pos, target_pos = self.get_poses_from_UI(3)
        try:
            self.E.action(pos, desired_pos, desired_action='repair', target_pos=target_pos)
        except CustomError as Err:
            print(Err)
        else:
            self.update()
            if self.replayfile is not None:
                self.replayfile.write(
                    f"repair {pos[1]} {pos[0]} {desired_pos[1]} {desired_pos[0]} {target_pos[1]} {target_pos[0]}" + '\n')

    def unload(self, pos=None, target_pos=None):
        if pos is None:
            pos, target_pos = self.get_poses_from_UI(2)
        try:
            self.E.unload(pos, target_pos=target_pos)
        except CustomError as Err:
            print(Err)
        else:
            self.update()
            if self.replayfile is not None:
                self.replayfile.write(f"unload {pos[1]} {pos[0]} {target_pos[1]} {target_pos[0]}" + '\n')

    def delete_coords(self, pos=None):
        if pos is None:
            pos = self.get_poses_from_UI(1)
        try:
            self.E.delete_coords(pos)
            if self.replayfile is not None:
                self.replayfile.write(f"delete {pos[1]} {pos[0]}" + '\n')
        except CustomError as Err:
            print(Err)
        else:
            self.update()
            if self.replayfile is not None:
                self.replayfile.write(f"delete {pos[1]} {pos[0]}" + '\n')

    def cop(self):
        try:
            self.E.power(1)
        except CustomError as Err:
            print(Err)
        else:
            self.update()
            if self.replayfile is not None:
                self.replayfile.write(f"COP" + '\n')

    def scop(self):
        try:
            self.E.power(2)
        except CustomError as Err:
            print(Err)
        else:
            self.update()
            if self.replayfile is not None:
                self.replayfile.write(f"SCOP" + '\n')

    def turn_end(self):
        self.turns_display.set(self.E.turns + 1)
        self.days.set(int((self.E.turns + 1) / 2) + 1)
        self.E.turn_end()
        self.update()
        if self.replayfile is not None:
            self.replayfile.write('turn' + '\n')

    def live_play(self):
        # live play mode
        self.E = Engine(self.map_path.get(), co_maker('jake', 'purplelightning'), co_maker('jess', 'yellowcomet'))
        self.replayfile = open('replays/' + '_'.join([str(e).zfill(2) for e in time.localtime()[0:6]]) + '.txt',
                                'w')  # save replay file in this mode
        self.replayfile.write(self.map_path.get() + '\n')
        self.replayfile.write(str(self.E.p1) + '\n')
        self.replayfile.write(str(self.E.p2) + '\n')
        self.load_map()
        self.update()

    def replay_view(self):
        # replay viewer mode
        if self.replayfile is not None:
            self.replayfile.close()
            self.replayfile = None
        replay = self.replay_path.get()
        self.lines = []
        with open(replay, 'r') as replayfile:
            # toplines = replayfile[0:3]  # top 3 lines are details
            # line0: map
            # line1: co1
            # line2: co2

            # play the game action by action (line by line)
            self.i = 0
            for i, line in enumerate(replayfile):
                line = line.split('\n')[0]
                if i > 2:
                    self.lines.append(line)
                elif i == 0:
                    self.map_path.set(line)
                elif i == 1:
                    co1 = eval(line)
                elif i == 2:
                    co2 = eval(line)
                    self.E = Engine(self.map_path.get(), co1, co2)
                    self.load_map()

        self.update()

    def replay_move(self, turn=None):
        self.i += 1
        if self.i >= len(self.lines):
            print("replay finished sry")
            return False
        line = self.lines[self.i]
        if line != 'turn' and line != 'winner':
            line = line.split(' ')
            pos = (int(line[2]), int(line[1]))
            match line[0]:  # action
                case 'build':
                    # unit_being_built = line[3]
                    self.build(pos, line[3])
                case 'fire':
                    # pos_destination = (line[4], line[3])
                    # pos_target = (line[6], line[5])
                    self.fire(pos, (int(line[4]), int(line[3])), (int(line[6]), int(line[5])))
                case 'wait':
                    # pos_destination = (line[4], line[3])
                    # print('move')  todo find out what it's doing since it won't display hehe
                    self.move(pos, (int(line[4]), int(line[3])))
                case 'delete':
                    self.delete_coords(pos)
                case 'unload':
                    self.unload(pos, (int(line[4]), int(line[3])))
                # todo continue cases. there's probably other actions? yea like turn end, cop, etc
        elif line == 'turn':
            self.turn_end()
            if turn is not None:
                return False
        else:
            print(line)
            self.winner = 1  # todo make sure this is the last line in the file?

    def replay_turn(self):
        turn = True
        while turn:
            turn = self.replay_move(turn)

    def close(self):
        if self.replayfile is not None:
            self.replayfile.close()
        self.Writer.close()
        plt.close("all")
        self.w.destroy()


def pos_from_combobox(combobox_option):
    pos = combobox_option.get().split(' ')[2:4]
    return int(pos[1][:-1]), int(pos[0][1:-1])


def on_pick(event):
    print(f"({event.x}, {event.y}) {event.button}")

