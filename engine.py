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


# todo sturm & lash movement
# todo snow & rain movement
# todo missiles (CO and player). sturm needs centred on a unit, others don't and scan top left: farright-down1-r-d-r-d
# todo sasha +100 per funds property (not labs, com, or 0 funds games lol)
# todo sasha SCOP turns 0.5*damage to funds
# todo sonja hiding unit hps and total value and damage calc numbers
# todo charge meters!
# todo pipseam attacks & destruction
# todo joining
# todo damage:
#  check for ['apc', 'bboat', 'bbomb', 'lander', 'tcopter'] in attacks bcus 0 luck
#  check a 0 base damage isn't gaining luck as well if they can't physically fire. out of ammo 'aa' vs tank.
#  javier indirect defence needs to be BEFORE fire is called.
#  sonja attack order
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

    def __init__(self):
        self.w = tk.Tk(className='awbw')
        # self.w.geometry("100x400")  # this is the worst. i hate it.
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

        self.costs = {0: 1, 1: 1.2, 2: 1.4, 3: 1.6, 4: 1.8, 5: 2, 6: 2.2, 7: 2.4, 8: 2.6, 9: 2.8, 10: 2}
        self.turns = 0
        self.days = tk.IntVar(self.w, value=int(self.turns / 2) + 1)
        self.map_info = ([], [], [], [], [], [])  # ownedby, stars, repair, production, access, special
        self.von_bolt_missiles = []  # [[turn popped, (position popped)], [turn, (pos)], [turn, (pos)], ...] missiles

        # figure display
        self.my_dpi = 102
        # self.figdims = [662, 515]  # *2 works for this map ig [1324, 1030] with max of roughly [1500, 1000]
        self.figdims = [662 * 2, 515 * 2]
        self.fig, self.ax = plt.subplots(figsize=(self.figdims[0] / self.my_dpi, self.figdims[1] / self.my_dpi),
                                         dpi=self.my_dpi)
        # self.ax.set(frame_on=False, bbox_inches='tight')
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.w)
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
        self.p1cop = tk.Button(co_tab, text='COP', command=self.p1COP)
        self.p1scop = tk.Button(co_tab, text='SCOP', command=self.p1SCOP)
        self.p2cop = tk.Button(co_tab, text='COP', command=self.p2COP)
        self.p2scop = tk.Button(co_tab, text='SCOP', command=self.p2SCOP)
        self.p1cb = tk.ttk.Combobox(co_tab, width=23, textvariable=self.p1combo)
        self.p2cb = tk.ttk.Combobox(co_tab, width=23, textvariable=self.p2combo)
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

        # self.w.after(60, self.update)
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

    def co_widgets(self, parent):
        #todo check anchor=e and w for all of them. need to add a number rly to check!
        # "CO controls go here (power buttons + bars + details ig)
        tk.ttk.Separator(parent, orient='vertical').place(relx=0.5, rely=0, relwidth=0.001, relheight=0.35)

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
        tk.Label(parent, textvariable=self.p1copcost, width=7, anchor="w").place(relx=0.55, rely=0.17)
        tk.Label(parent, textvariable=self.p1scopcost, width=7, anchor="e").place(relx=0.80, rely=0.17)
        self.p2cop.place(relx=0.55, rely=0.2)
        self.p2scop.place(relx=0.85, rely=0.2)
        tk.ttk.Separator(parent, orient='horizontal').place(relx=0, rely=0.25, relwidth=1, relheight=0.001)

        self.p1cb.place(relx=0.03, rely=0.27)
        self.p2cb.place(relx=0.53, rely=0.27)
        # calc button (never needs to check if it's an allowed move, firing has no consequence just prints hps)
        tk.Button(parent, text='Calc selection 1 on 2', command=self.calc1).place(relx=0.1, rely=0.3)
        tk.Button(parent, text='Calc selection 2 on 1', command=self.calc2).place(relx=0.6, rely=0.3)
        tk.ttk.Separator(parent, orient='horizontal').place(relx=0, rely=0.44, relwidth=1, relheight=0.001)

        tk.Button(parent, text='Move & join/load/cap/wait', command=self.fire).place(relx=0.4, rely=0.37)
        tk.Button(parent, text='Move & (un/)hide', command=self.fire).place(relx=0.4, rely=0.37)
        tk.Button(parent, text='Move & fire', command=self.fire).place(relx=0.4, rely=0.37)
        tk.Button(parent, text='Move & repair', command=self.fire).place(relx=0.4, rely=0.37)
        tk.Button(parent, text='Unload (doesn\'t wait)', command=self.fire).place(relx=0.4, rely=0.37)
        # capture becomes wait if (not inf on prop owned by (not current army))

        # unit controls + details go here").place(relx=0.25, rely=0.45)
        # production controls go here").place(relx=0.25, rely=0.85

    def update(self, draw=None):
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

        # visual things below this point! can be fully commented out im p sure for speedy sims

        self.p1copcost.set(self.p1['COP'] * self.costs[self.p1['starcost']] * 9000)
        self.p1scopcost.set(self.p1['SCOP'] * self.costs[self.p1['starcost']] * 9000)
        self.p2copcost.set(self.p2['COP'] * self.costs[self.p2['starcost']] * 9000)
        self.p2scopcost.set(self.p2['SCOP'] * self.costs[self.p2['starcost']] * 9000)

        # combobox dropdown list thing
        s = []
        # if not sonja bcus she hides her unit hps!
        for unit in self.p1['units']:
            if unit['position'] != (-10, -10):
                s.append(f"{int(1 + unit['hp'] / 10)} {unit['type']} {unit['position']} m:{unit['move']}")
            else:
                s.append(f"{int(1 + unit['hp'] / 10)} {unit['type']} '(loaded)' m:{unit['move']}")
            # f:{unit['fuel']} a:{unit['ammo']}  # todo display all these things (stars, terr) somewhere
        self.p1cb['values'] = s
        s = []
        for unit in self.p2['units']:
            if unit['position'] != (-10, -10):
                s.append(f"{int(1 + unit['hp'] / 10)} {unit['type']} {unit['position']} m:{unit['move']}")
            else:
                s.append(f"{int(1 + unit['hp'] / 10)} {unit['type']} '(loaded)' m:{unit['move']}")
        self.p2cb['values'] = s

        # unit visual display
        if draw is None:
            dims = self.map_info[0].shape
            r = 1 / dims[1]
            # might be bottom-left centred. not sure
            for unit in self.p1['units']:
                if unit['position'] != (-10, -10):
                    img = mpimg.imread(f"units/pc{name_to_filename(unit['type'])}.gif")
                    self.fig.add_axes(
                        [r * unit['position'][1], 1 - (14 / 11) * (r * unit['position'][0] + 0.95 * r), r, r]
                    ).imshow(img)
                    plt.gca().axis("off")
                    # plt.setp(plt.gca(), xticks=[], yticks=[])  # hide ticks but keep white space and black outline
                    # plt.gca().patch.set_alpha(0)  # hide white space
            for unit in self.p2['units']:
                if unit['position'] != (-10, -10):
                    img = mpimg.imread(f"units/bd{name_to_filename(unit['type'])}.gif")
                    self.fig.add_axes(
                        [r * unit['position'][1], 1 - (14 / 11) * (r * unit['position'][0] + 0.95 * r), r, r]
                    ).imshow(img)
                    plt.gca().axis("off")
            self.canvas.draw()

    def load_map(self):
        self.map_info = load_map(self.map_path.get())
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
        self.fig.add_axes([0, 0, 1, 1]).imshow(mpimg.imread(self.map_path.get().split('.txt')[0] + '.png'))
        plt.setp(plt.gca(), xticks=[], yticks=[])  # hide axes
        # print('background displayed!')
        self.ax.axis("off")

        self.load_map_units()
        self.update()

    def load_map_units(self):
        # wipe units
        self.p1['units'] = []
        self.p2['units'] = []

        # load units from file
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
                    raise ImportError(f"neither player is {army}")

    def calc1(self):
        calc(self.p1combo.get().split(' ')[2:4], self.p2combo.get().split(' ')[2:4], self.p1['units'], self.p2['units'])

    def calc2(self):
        calc(self.p2combo.get().split(' ')[2:4], self.p1combo.get().split(' ')[2:4], self.p2['units'], self.p1['units'])

    def return_unit(self, pos):
        for unit in self.p1['units']:
            if unit['position'] == pos:
                return unit
        for unit in self.p2['units']:
            if unit['position'] == pos:
                return unit
        return None

    def delete_unit(self, pos):
        for unit in self.p1['units']:
            if unit['position'] == pos:
                self.p1['units'].remove(unit)
                return
        for unit in self.p2['units']:
            if unit['position'] == pos:
                self.p2['units'].remove(unit)
                return

    def action(self, pos, desired_pos, desired_action='wait', target_pos=None):
        # todo recons make movement hard bcus u can move around more than you can move through sometimes.
        #  actual path finding is needed :/

        # todo check movement to desired_pos

        if pos == (-10, -10):
            raise CustomError("loaded units can't do anything")
        u1 = self.return_unit(pos)  # unit making the move
        u2 = self.return_unit(target_pos)  # unit being fired on
        if pos == desired_pos:
            u3 = None  # no u3 if u3 is the same unit as u1
        else:
            u1['capture'] = 0  # set this unit's capture value to 0 because it isn't in the same place anymore
            u3 = self.return_unit(desired_pos)  # unit at desired position

            if u3 is not None:  # if there is actually a unit there, see what we can do
                if u3['army'] != u1['army']:  # trapped in fog (other traps are possible)
                    raise CustomError(f"can't move, enemy {u3['type']} already there")
                else:  # a friendly unit is on that space. load, join, or fail movement
                    if desired_action != 'wait':  # don't allow join + fire 🤣
                        raise CustomError(f"can't do that! Friendly {u3['type']} already in that space")
                    elif u3['type'] == u1['type'] and u3['hp'] <= 89:
                        x = 1  # join!!!
                        # not allowed to enter that space if it's not a transport or the same unit below 10hp
                        # todo work on joining
                        # transports with units in CANNOT join ever
                        # joined units have a minimum cap of their VISIBLE health adding. I thinkkkkkkkkkkkkkkk?
                        # 5(1) + 18(2) = 23(3)
                        # 5(1) + 12(2) = 20(3) NOT 17(2)
                    elif u3['type'] in ['apc', 'bboat', 'lander', 'tcopter', 'carrier', 'cruiser']:
                        check = u3['loaded']  # attempt loading
                        match u3['type']:
                            # apc is 1x space, foot
                            # bboat is 2x space, foor
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
                            # todo more cases to fill out now
                        if u3['loaded'] == check:
                            # doesn't load even tho u tried
                            raise CustomError(
                                f"can't load {u1['type']} into {u3['type']} with loaded: {len(u3['loaded'])}")
                        else:
                            u1['position'] = (-10, -10)  # all loaded units go to these coords off the map
                    else:
                        raise CustomError(f"can't move, friendly {u3['type']} already there")

        # no enemy unit is in the way, the action is allowed
        match desired_action:
            case 'wait':  # cap, if not cap, no action
                if u3 is None and u1['type'] in ['inf', 'mech'] and u1['army'] != [
                    'neutral', 'amberblaze', 'blackhole', 'bluemoon', 'browndesert', 'greenearth', 'jadesun',
                    'orangestar', 'redfire', 'yellowcomet', 'greysky', 'cobaltice', 'pinkcosmos', 'tealgalaxy',
                    'purplelightning', 'acidrain', 'whitenova', 'azureasteroid', 'noireclipse'
                ][self.map_info[0][desired_pos]]:
                    capture = 1  # todo capture numbers
                    if self.p2['properties'] == 1:  # search through for this property, if it is owned by p2
                        # then take away
                        self.p2['properties'] -= 1
                    # add property number
                    self.p1['properties'] += 1

                    # update a little bit (we don't render owning properties that's hard :>)
                    self.income_update()

            case 'fire':
                if target_pos is None:
                    raise CustomError("why is no unit selected for firing on?")
                elif u2['army'] == u1['army']:
                    raise CustomError("can't fire on friendlies!")
                else:
                    indr = ['arty', 'bship', 'carrier', 'missile', 'pipe', 'rocket']
                    desired_to_target_dist = abs((desired_pos[0] - desired_pos[1]) + (target_pos[0] - target_pos[1]))
                    # we don't care about diagonal distance here, just grid distance
                    if not indr:
                        if desired_to_target_dist != 1:
                            raise CustomError(f"attack not valid. {u1['type']} is not an indirect and"
                                              f" moving to {desired_pos} is not next to the target {target_pos}")
                    elif abs((pos[0] - pos[1]) + (desired_pos[0] - desired_pos[1])) != 0:
                        raise CustomError("attack not valid. indirects have to stay where they are to shoot!")
                    elif desired_to_target_dist > u1['range'][1] or desired_to_target_dist < u1['range'][0]:
                        raise CustomError(f"{desired_to_target_dist} too far to shoot for range {u1['range']}")

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
                    u1, u2 = fire(u1, u2, counter)

            case 'repair':
                if target_pos is None:
                    raise CustomError("why is no unit selected for repairing?")
                elif u2['army'] != u1['army']:
                    raise CustomError("can't repair non-friendlies!")
                else:
                    repair = 1  # todo

            case 'hide':
                u1['hidden'] = not u1['hidden']  # wow this one is nice and simple :>

        # all actions if successful move and set fuel
        u1['position'] = desired_pos  # everything went smoothly let's update position :D
        movecost = 0  # todo
        u1['fuel'] = u1['fuel'] - movecost
        u1['Dtr'] = self.map_info[1][desired_pos]
        u1['terr'] = self.map_info[5][desired_pos]

        # upon destruction, check for loaded units and destroy them in the normal unit list :>

        self.delete_unit(u1)
        self.delete_unit(u2)
        if u3 is not None:
            self.delete_unit(u3)

        if u2['hp'] >= 0:  # attack doesn't destroy defender
            if u2['army'] == self.p1['army']:
                self.p1['units'].append(u2)
            else:
                self.p2['units'].append(u2)
        else:
            if len(u2['loaded']) > 0:
                x = 1  # todo find and delete

        if u1['hp'] >= 0:  # counter-attack doesn't destroy attacker
            self.p1['units'].append()
            # cruisers force us to have this clause here. the only transport that can die to counter-attack :c

    def fire(self):
        pos = self.p2combo.get().split(' ')[2:4]  # todo
        desired_pos = (2, 1)  # todo
        target_pos = (3, 1)
        self.action(pos, desired_pos, desired_action='wait', target_pos=target_pos)

    def capture(self):  # todo call and stuff. previous check that the property wasn't owned by this army :>
        # todo this is just the format needed (appending to p1 caps)
        x = 1

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
                    raise IndexError("Somehow a property is not neutral and not either army. huh")
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

    def turn_end(self):  # p1 -> p2

        self.turns += 1
        self.days.set(int(self.turns / 2) + 1)
        # check win conditions (day limit ig?)
        p1win = False
        if self.p1['properties'] > 23:
            p1win = True
        if self.days.get() > 40:  # turn limit 40 days?
            if self.p1['properties'] > 15:
                p1win = True
        if self.days.get() >= 2 and len(self.p2['units']) == 0:  # if p2 has no units and it's not the start of the game
            p1win = True
        if p1win:
            print('p1 wins')

        # turn starts in this order ig (p1 ending, p2 beginning)
        self.p2, self.p1 = activate_or_deactivate_power(self.p2, self.p1, -self.p2['power'])
        self.p2['funds'] += self.p2['income']
        repair = 1  # todo rachel +1 repair
        fuel_and_ammo_resuuply = 1
        fuel_use = 1
        crashed_planes_check = 1
        if self.p1['name'] == 'von bolt':
            if self.von_bolt_missiles[-1][0] == self.turns - 1:
                pos = self.von_bolt_missiles[-1][1]
                units_move_set_0 = 1  # only enemy get stunned, even though self damage is done? check in a game ig?
        self.update()

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
    pos = (int(pos1[0][1:-1]), int(pos1[1][:-1]))
    for unit in units1:
        if unit['position'] == pos:
            u1 = unit

    pos = (int(pos2[0][1:-1]), int(pos2[1][:-1]))
    for unit in units2:
        if unit['position'] == pos:
            u2 = unit
    # print(u1)
    # print(u2)
    print(damage_calc_bounds(u1, u2))


def buttonfunc():
    print('ayy it workie')


class CustomError(Exception):
    def __init__(self, message):
        super().__init__(message)
        # if I want extra arguments, go to https://stackoverflow.com/a/1319675
