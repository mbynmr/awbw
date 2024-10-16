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


# todo sturm & lash movement
# todo snow & rain
# todo missiles (CO and player). sturm needs centred on a unit, others don't and scan top left: farright-down1-r-d-r-d
# todo captures & sami caps
# todo sasha +100 per funds property (not labs, com, or 0 funds games lol)
# todo sasha SCOP turns 0.5*damage to funds
# todo charge meters!
# todo damage:
#  check for ['apc', 'bboat', 'bbomb', 'lander', 'tcopter'] in attacks bcus 0 luck
#  check a 0 base damage isn't gaining luck as well if they can't physically fire. out of ammo 'aa' vs tank.
#  javier indirect defence needs to be BEFORE fire is called.
#  sonja attack order
#  kanbei & sonja counterattack damage

# training idea: a set of stages it has to pass before moving on to the next
# give it a nearly winning position (like 10 of them?) where they just cap hq to win or kill 1 unit
# then level it up, make it so it needs 2 turns to win.
# then add some resistance (inf on hq to kill, then cap)
# then make it a few turns before victory
# then make it play itself from turn 0 lots of times on a few maps
# play me!
# profit??


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
        self.p1funds = tk.IntVar(self.w, value=3000)  # todo
        self.p1unitc = tk.IntVar(self.w, value=0)
        self.p1unitv = tk.IntVar(self.w, value=0)
        self.p1income = tk.IntVar(self.w, value=0)

        self.p2 = co_maker('jess')
        self.p2['army'] = 'yellowcomet'
        self.p2name = self.p2['name']
        self.p2funds = tk.IntVar(self.w, value=0)
        self.p2unitc = tk.IntVar(self.w, value=0)
        self.p2unitv = tk.IntVar(self.w, value=0)
        self.p2income = tk.IntVar(self.w, value=0)

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
        self.update()
        # self.load_map()
        self.w.mainloop()

    def widgets(self):
        parent = self.w
        tk.Button(parent, text='Close', command=self.close).place(relx=0.925, rely=0.925)
        self.canvas.get_tk_widget().place(relx=0.4, rely=0.5, anchor=CENTER)
        # fig.canvas.callbacks.connect('pick_event', on_pick)
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
        # "CO controls go here (power buttons + bars + details ig)

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
        tk.Label(parent, textvariable=self.p1unitc, width=8, anchor="e").place(relx=0.30, rely=0.02)
        tk.Label(parent, textvariable=self.p1unitv, width=8, anchor="e").place(relx=0.30, rely=0.05)
        tk.Label(parent, textvariable=self.p1income, width=8, anchor="e").place(relx=0.30, rely=0.08)
        tk.ttk.Separator(parent, orient='vertical').place(relx=0.5, rely=0, relwidth=0.2, relheight=0.11)
        tk.ttk.Separator(parent, orient='horizontal').place(relx=0, rely=0.11, relwidth=1, relheight=0.2)
        tk.Label(parent, text=self.p2['name'], width=6, anchor="w").place(relx=0.52, rely=0.02)
        tk.Label(parent, text=armies[self.p2['army']], width=6, anchor="w").place(relx=0.52, rely=0.05)
        tk.Label(parent, textvariable=self.p2funds, width=8, anchor="w").place(relx=0.52, rely=0.08)
        tk.Label(parent, textvariable=self.p2unitc, width=8, anchor="e").place(relx=0.80, rely=0.02)
        tk.Label(parent, textvariable=self.p2unitv, width=8, anchor="e").place(relx=0.80, rely=0.05)
        tk.Label(parent, textvariable=self.p2income, width=8, anchor="e").place(relx=0.80, rely=0.08)
        # justify='center'
        # , anchor="w"
        # , sticky="w"
        # https://www.reddit.com/r/learnpython/comments/11p94d5/tkinter_how_can_i_align_the_text_inside_a_label/

        # unit list to select from goes here").place(relx=0.25, rely=0.45)
        # unit controls + details go here").place(relx=0.25, rely=0.45)
        # production controls go here").place(relx=0.25, rely=0.85)
        # tk.Button(parent, text='COP', command=self.COP).place(relx=0.01, rely=0.335)
        # tk.Button(parent, text='SCOP', command=self.SCOP).place(relx=0.11, rely=0.335)
        # tk.ttk.Separator(parent, orient='vertical').place(relx=0.5, rely=0.11, relwidth=0.2, relheight=0.89)
        self.p1combo = tk.StringVar()  # move this plz ty
        self.p1cb = tk.ttk.Combobox(parent, width=23, textvariable=self.p1combo)
        self.p1cb.place(relx=0.03, rely=0.3)
        self.p2combo = tk.StringVar()  # move this plz ty
        self.p2cb = tk.ttk.Combobox(parent, width=23, textvariable=self.p2combo)
        self.p2cb.place(relx=0.53, rely=0.3)
        # self.p1cb['values'] = (' January',
        #                        ' December')

    def buttonfunc(self):
        print('ayy it workie')

    def update(self, dims=None):
        self.p1funds.set(self.p1['funds'])
        self.p1unitc.set(len(self.p1['units']))
        v = 0
        for e in self.p1['units']:
            display_hp = int(1 + e['hp'] / 10)
            v += int(e['value'] * display_hp / 10)  # full value * visible hp
        self.p1unitv.set(v)
        self.p1income.set(self.p1['income'])

        self.p2funds.set(self.p2['funds'])
        self.p2unitc.set(len(self.p2['units']))
        v = 0
        for e in self.p2['units']:
            display_hp = int(1 + e['hp'] / 10)
            v += int(e['value'] * display_hp / 10)  # full value * visible hp / 10
        self.p2unitv.set(v)
        self.p2income.set(self.p2['income'])

        # combobox dropdown list thing
        s = []
        for unit in self.p1['units']:
            s.append(f"{int(1 + unit['hp'] / 10)} {unit['type']} {unit['position']}  m:{unit['move']}")
            # f:{unit['fuel']} a:{unit['ammo']}  # todo display all these things (stars, terr) somewhere
        self.p1cb['values'] = s
        s = []
        for unit in self.p2['units']:
            s.append(f"{int(1 + unit['hp'] / 10)} {unit['type']} {unit['position']} m:{unit['move']}")
        self.p2cb['values'] = s

        # unit visual display
        # [14, 18]
        # 0-13 down, 0-17 across
        if dims is not None:
            r = 1 / dims[1]
            # might be bottom-left centred. not sure
            for unit in self.p1['units']:
                img = mpimg.imread(f"units/pc{name_to_filename(unit['type'])}.gif")
                self.fig.add_axes([r * unit['position'][1], 1 - (14 / 11) * (r * unit['position'][0] + 0.95 * r), r, r]
                                  ).imshow(img)
                plt.gca().axis("off")
                # plt.setp(plt.gca(), xticks=[], yticks=[])  # hide ticks but keep white space and black outline
                # plt.gca().patch.set_alpha(0)  # hide white space
            for unit in self.p2['units']:
                img = mpimg.imread(f"units/bd{name_to_filename(unit['type'])}.gif")
                self.fig.add_axes([r * unit['position'][1], 1 - (14 / 11) * (r * unit['position'][0] + 0.95 * r), r, r]
                                  ).imshow(img)
                plt.gca().axis("off")
            self.canvas.draw()

        # print('updated')
        # self.w.after(60, self.update)  # only update after something happens. not like this plz :>

    def load_map(self):
        self.map_info = load_map(self.map_path.get())
        # self.fig.set_figwidth(1077 / self.my_dpi)  # todo auto do these dims?
        # self.fig.set_figheight(839 / self.my_dpi)
        # ownedby, stars, repair, production, access, special
        # self.ax_bg.set_xlim([0, dims[0]])
        # self.ax_bg.set_ylim([0, dims[1]])
        plt.subplots_adjust(wspace=0, hspace=0)
        plt.tight_layout()
        self.fig.add_axes([0, 0, 1, 1]).imshow(mpimg.imread(self.map_path.get().split('.txt')[0] + '.png'))
        plt.setp(plt.gca(), xticks=[], yticks=[])  # hide axes
        # print('background displayed!')
        self.ax.axis("off")

        self.load_map_units()
        self.update(self.map_info[0].shape)

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

    def select_path(self):
        self.map_path.set(filedialog.askdirectory())
        self.entry_path.xview_moveto(1)

    def turn_end(self):  # p1 -> p2

        self.turns += 1
        self.days.set(int(self.turns / 2) + 1)
        # check win conditions (day limit ig?)
        p1win = False
        if self.p1['income'] > 23000 and self.p1['name'] != 'sasha':
            p1win = True
        elif self.p1['name'] == 'sasha' and self.p1['income'] > 23000 * 1.1:
            p1win = True
        if self.days.get() > 40:  # turn limit 40 days?
            if self.p1['income'] > 15000 and self.p1['name'] != 'sasha':
                p1win = True
            elif self.p1['name'] == 'sasha' and self.p1['income'] > 15000 * 1.1:
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
                units_move_set_0 = 1  # only enemy, even though self damage is done?
        self.update()  # todo probably call here right?

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
