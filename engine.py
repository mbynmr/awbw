import time
import numpy as np
from pycparser.ply.yacc import LRTable

from co import activate_or_deactivate_power, turn_resupplies, com_change
from unit import unit_maker, unit_stats_editor, unit_stats_fire
from map import load_map
from fire import fire, compatible, damage_calc_bounds
from pathfind import path_find
from customerrors import CustomError


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
# todo hidden units being hidden (at that point you can do fog pretty much)
# todo damage:
#  sonja SCOP attack order
#  kanbei & sonja counterattack damage

# todo seperate out Engine (runs game) and GUI (runs graphics, runs an instance of Engine)


class Engine:
    """
    big main class for game
    """

    def __init__(self, map_path, co1, co2, rng_seed):

        self.winner = 0
        self.turns = -1
        self.map_info = ([], [], [], [], [], [])  # ownedby, stars, repair, production, access, special
        self.map_rules = {'unitl':0, 'capturel': 0, 'dayl': 0, 'fog': 0, 'weather': 0, 'fundstart': 0, 'banned': []}
        self.von_bolt_missile = [-20, (-20, -20)]  # [turn popped, (position popped)]
        self.income = 1000  # hf is 2000

        self.mp = map_path
        self.rng_seed = int(rng_seed)

        # co
        self.p1 = co1
        self.p2 = co2

    def load_map(self, path=None):
        if path is None:
            path = self.mp  # todo
        self.map_info, self.map_rules = load_map(path)
        # ownedby, stars, repair, production, access, special
        armies = [
            'neutral', 'amberblaze', 'blackhole', 'bluemoon', 'browndesert', 'greenearth', 'jadesun', 'orangestar',
            'redfire', 'yellowcomet', 'greysky', 'cobaltice', 'pinkcosmos', 'tealgalaxy', 'purplelightning',
            'acidrain', 'whitenova', 'azureasteroid', 'noireclipse'
        ]
        self.income_update()

        for e in np.argwhere(self.map_info[0] != 0):  # 0 is neutral
            if armies[self.map_info[0][e[0], e[1]]] == self.p1['army']:
                self.p1['properties'] += 1
            elif armies[self.map_info[0][e[0], e[1]]] == self.p2['army']:
                self.p2['properties'] += 1
        self.load_map_units(path)
        self.turn_end()

    def load_map_units(self, map_path):
        # wipe units
        self.p1['units'] = []
        self.p2['units'] = []

        # load units from file
        path = map_path.split('.txt')[0] + ' units.txt'

        with open(path) as file:
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

    def return_unit(self, pos):
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
        if u in self.p1['units']:  # todo is this working?
            self.p1['units'].remove(u)
        elif u in self.p2['units']:
            self.p2['units'].remove(u)
        else:
            raise CustomError("oh no big bad, crash crash crash")

    def check_movement(self, u, pos1, pos2=None):
        # returns: movecost (0-11 (fighter with +2 move) is possible, -1 is impossible)
        # todo sturm, lash SCOP, snow, rain affect this function

        if pos2 is not None:
            if pos1 == pos2:  # save some time with this return
                return 0

        access = self.map_info[4]
        # 0: road, 1: plain, 2: wood, 3: river, 4: shoal, 5: sea, 6: pipe, 7: port, 8: base, 9: mountain, 10: reef
        grid = np.zeros_like(access)
        # special = self.map_info[5]
        # # special - 0: misc, 1: pipeseam, 2: missile, 3: road, 4: plain, 5: urban, 6: lab&hq
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
            if enemy_unit['position'][0] != -10:
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

    def action(self, pos, desired_pos, desired_action, target_pos=None):
        if pos[0] == -10:
            raise CustomError("loaded units can't do anything")
        u1 = self.return_unit(pos)  # unit making the move
        if u1 is None:
            raise CustomError(f"somehow no unit is at position {pos} to make the move")
        elif self.turns % 2 == 0:  # even turn means p1 turn
            coname = self.p1['name']
            econame = self.p2['name']
            coarmy = self.p1['army']
            copower = self.p1['power']
            ecopower = self.p2['power']
            self.action_do(self.p1, self.p2, u1, pos, desired_pos, desired_action, target_pos)
        else:  # odd turn means p2 turn
            coname = self.p2['name']
            econame = self.p1['name']
            coarmy = self.p2['army']
            copower = self.p2['power']
            ecopower = self.p1['power']
            self.action_do(self.p2, self.p1, u1, pos, desired_pos, desired_action, target_pos)#


    def action_do(self, p1, p2, u1, pos, desired_pos, desired_action, target_pos=None):
        if u1['army'] != p1['army']:
            raise CustomError("selected unit is not owned by the player who's turn it is!")
        if u1['move'] < 1:
            raise CustomError("unit cannot move anymore")
        SCOP = p1['power'] == 2
        eSCOP = p2['power'] == 2
        eCOP = p2['power'] == 1
        sami = p1['name'] == 'sami'  # this player sami
        sasha = p1['name'] == 'sasha'  # this player sasha
        esasha = p2['name'] == 'sasha'  # other player sasha
        javier = p2['name'] == 'javier'  # other player javier
        sonja = p2['name'] == 'sonja'  # other player sonja
        kanbei = p2['name'] == 'kanbei'  # other player kanbei

        u1store = u1.copy()
        movecost = self.check_movement(u1, u1['position'], desired_pos)
        if movecost < 0:
            if movecost == -3:
                raise CustomError(f"not enough fuel")
            elif movecost == -2:
                raise CustomError(f"not enough move")
            else:
                raise CustomError(f"move is impossible for some reason")

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
                # a friendly unit is on that space. load, join, or fail movement
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
                    if u3['hp'] >= 99:  # if the unit went over 99 hp
                        u3['hp'] = 99  # cap it
                        if display_hp1 + display_hp3 > 10:  # if the display hps add to more than 10, get funds.
                            p1['funds'] = int(p1['funds'] + int(u3['value'] * (display_hp1 + display_hp3 - 10) / 10))
                    elif int(1 + (u3['hp']) / 10) < display_hp1 + display_hp3:  # if display hps didn't add
                        u3['hp'] = (display_hp1 + display_hp3 - 1) * 10  # bump it up a bit to add display hps
                    max_ammo = types[u3['type']][0]
                    max_fuel = types[u3['type']][1]
                    u3['ammo'] = max_ammo if u3['ammo'] > max_ammo else u3['ammo']  # cap it
                    u3['fuel'] = max_fuel if u3['fuel'] > max_fuel else u3['fuel']  # cap it

                elif u3['type'] in ['apc', 'bboat', 'lander', 'tcopter', 'carrier', 'cruiser']:
                    check = len(u3['loaded'])  # attempt loading
                    match u3['type']:
                        # apc is 1x space, foot
                        # bboat is 2x space, foot
                        # lander is 2x space, land unit
                        # tcopter is 1x space, foot
                        # carrier is 2x space, air
                        # cruiser is 2x space, copter (b or t)
                        case 'apc':
                            if len(u3['loaded']) == 0 and u1['type'] in ['inf', 'mech']:
                                u3['loaded'].append(u1)
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
                    if len(u3['loaded']) == check:
                        # doesn't load even tho u tried
                        raise CustomError(
                            f"can't load {u1['type']} into {u3['type']} with loaded: {len(u3['loaded'])}")
                    else:
                        u1['position'] = (-10, -10 - len(u3['loaded']))
                        # all loaded units go to x=-10 and y=-10 - number they are loaded as (so only -11 or -12)
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
                    ][self.map_info[0][desired_pos]] and (
                            self.map_info[5][desired_pos] == 5 or self.map_info[5][desired_pos] == 6):
                        # if tile is not owned by friendly, terrain is urban or hq/lab
                        u1['capture'] += int(int(1 + u1['hp'] / 10) * 15 if sami else 10)
                        # im so confused why is this 10x or 15x for sami??? hp is already out of 10 why not 1x and 1.5x?
                        if u1['capture'] >= 20 or (sami and SCOP):  # capture happened!
                            u1['capture'] = 20
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
                    compat1, ammo1 = compatible(u1, u2)
                    if not compat1:
                        raise CustomError(f"attack not valid: {u1['type']} with ammo {u1['ammo']} on {u2['type']}")
                    counter = True
                    if u1['type'] in indr or u2['type'] in indr:
                        counter = False  # indirects don't get countered or perform counters even if it's valid
                    elif not compatible(u2, u1):
                        counter = False
                    u1['Dtr'] = self.map_info[1][desired_pos]  # 1: stars
                    u1['terr'] = self.map_info[5][desired_pos]  # 5: special (plain=4)

                    # weird CO buffs
                    if u1['type'] in indr and javier:  # if being shot by indirect and javier owns enemy unit
                        u2['Dv'] += 80 if eSCOP else (40 if eCOP else 20)  # enemy javier (power) indirect defence
                    elif (kanbei and eSCOP) or (sonja and not eSCOP):  # sonja doesn't get 1.5x on SCOP right?
                        u2['Av'] = int(u2['Av'] * 1.5)
                    # make sure unit stats are up to date
                    u1 = unit_stats_fire(u1, p1, before=True)

                    if sonja and counter and eSCOP:
                        u2, u1 = fire(u2, u1, counter, self.rng_seed)  # swap order for enemy sonja SCOP
                    else:
                        u1, u2 = fire(u1, u2, counter, self.rng_seed)
                    self.rng_seed += 1  # change rng in a consistent waY
                    # this way you don't get the same engagement giving the same every time in a given match
                    # but you also can predict exactly what damage is done given a set seed and set move order (replays)

                    # reset weird CO buffs
                    u1 = unit_stats_fire(u1, p1, before=False)
                    if u1['type'] in indr and javier:
                        u2['Dv'] -= 80 if eSCOP else (40 if eCOP else 20)
                    elif (kanbei and eSCOP) or (sonja and not eSCOP):
                        u2['Av'] = int(u2['Av'] * 1.5)

            case 'repair':
                if target_pos is None:
                    raise CustomError("why is no target position selected for repairing?")
                if u1['type'] not in ['apc', 'bboat']:
                    raise CustomError(f"{u1['type']} cannot resupply")
                if u2 is None:
                    raise CustomError(f"no unit is at target position {target_pos} for resupply")
                elif u2['army'] != u1['army']:
                    raise CustomError("can't resupply non-friendlies!")
                u2['ammo'] = types[u2['type']][0]
                u2['fuel'] = types[u2['type']][1]
                display_hp2 = int(1 + u1['hp'] / 10)
                if u1['type'] == 'bboat':
                    if self.turns % 2 == 0 and self.p1['funds'] >= u2['value'] / 10:
                        u2['hp'] += 10
                    elif self.turns % 2 == 1 and self.p2['funds'] >= u2['value'] / 10:
                        u2['hp'] += 10
                    if u2['hp'] >= 90:  # is this how it works? not sure rly.
                        # case where co has no funds but repairs a 90 (10hp display) unit, does it still go to 99?
                        u2['hp'] = 99
                    if self.turns % 2 == 0:
                        self.p1['funds'] = int(
                            self.p1['funds'] - int(u2['value'] * (int(1 + u2['hp'] / 10) - display_hp2) / 10))
                    else:
                        self.p2['funds'] = int(
                            self.p2['funds'] - int(u2['value'] * (int(1 + u2['hp'] / 10) - display_hp2) / 10))

            case 'hide':
                if u1['type'] in ['stealth', 'sub']:
                    u1['hidden'] = not u1['hidden']  # wow this one is nice and simple :>
                else:
                    raise CustomError("unit can't hide")
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
            p1['charge'] += u1_dmg_value + int(0.5 * u2_dmg_value)
            p2['charge'] += u2_dmg_value + int(0.5 * u1_dmg_value)
            if sasha and SCOP:  # this player sasha SCOP funds
                p1['funds'] = int(p1['funds'] + int(0.5 * u2_dmg_value))
            elif esasha and eSCOP:  # enemy player sasha SCOP funds
                p2['funds'] = int(p2['funds'] + int(0.5 * u1_dmg_value))

        # manage units that need deleting
        for u in [u1, u2, u3]:
            if u is not None:
                if u['hp'] < 0:
                    self.delete_unit(u)

    def build(self, pos, typ):
        if self.turns % 2 == 0:
            army = self.p1['army']
            funds = self.p1['funds']
            unitc = len(self.p1['units'])
            hachiSCOP = self.p1['name'] == 'hachi' and self.p1['power'] == 2
        else:
            army = self.p2['army']
            funds = self.p2['funds']
            unitc = len(self.p2['units'])
            hachiSCOP = self.p2['name'] == 'hachi' and self.p2['power'] == 2

        if unitc >= self.map_rules['unitl']:
            raise CustomError(f"map doesn't allow more than {unitc} units")

        if army != [
            'neutral', 'amberblaze', 'blackhole', 'bluemoon', 'browndesert', 'greenearth', 'jadesun',
            'orangestar', 'redfire', 'yellowcomet', 'greysky', 'cobaltice', 'pinkcosmos', 'tealgalaxy',
            'purplelightning', 'acidrain', 'whitenova', 'azureasteroid', 'noireclipse'
        ][self.map_info[0][pos]]:  # if that space (production hopefully) owned by this turn's player
            raise CustomError("this player doesn't own that space")

        if typ in self.map_rules['banned']:
            raise CustomError(f"map doesn't allow production of {typ}")

        sea = typ in ['bship', 'bboat', 'carrier', 'cruiser', 'lander', 'sub']
        air = typ in ['bcopter', 'bbomb', 'bomber', 'fighter', 'stealth', 'tcopter']
        typfail = True
        match self.map_info[3][pos]:  # combination base + land unit, port + sea unit,...
            case 1:  # base
                if not sea and not air:
                    typfail = False
            case 2:  # port
                if sea:
                    typfail = False
            case 3:  # airport
                if air:
                    typfail = False
            case 0:  # 0 = none, any building that isn't production
                if not sea and not air and hachiSCOP and self.map_info[1][pos] == 3 and self.map_info[2][pos] == 1:
                    typfail = False  # hachi SCOP: ground unit on city [can repair, not build, 3 stars]
                else:
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
            'missile': 12000,
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
            self.p1['funds'] = int(self.p1['funds'] - int(costs[typ]))
        elif army == self.p2['army']:
            self.p2['units'].append(unit_maker(army, typ, self.p2, pos, move=0))
            self.p2['funds'] = int(self.p2['funds'] - int(costs[typ]))

    def delete_coords(self, pos):
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

    def unload(self, pos, target_pos, choice):

        u = self.return_unit(pos)
        if u is None:
            raise CustomError(f"no unit at coords {pos}")
        if self.turns % 2 == 0:
            army = self.p1['army']
        else:
            army = self.p2['army']
        if u['army'] != army:
            raise CustomError(f"unit doesn't belong to player who's turn it is")
        if u['type'] not in ['apc', 'bboat', 'lander', 'tcopter', 'carrier', 'cruiser']:
            raise CustomError(f"{u['type']} can't have units inside it!")
        choicepos = (pos[0], pos[1] - choice)
        check = True
        for ul in u['loaded']:
            if ul['position'] == choicepos:
                check = False
                break
        if check:
            raise CustomError("no unit to unload")
        if abs((pos[0] - target_pos[0]) + (pos[1] - target_pos[1])) != 1:
            raise CustomError("unload tile is not adjacent to carrier")
        ul['position'] = target_pos
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
        ul['ammo'] = types[ul['type']][0]
        ul['fuel'] = types[ul['type']][1]
        # set fuel, ammo to full
        u['loaded'].remove(ul)
        if len(u['loaded']) == 1:  # shouldn't ever be bigger than 2 so only checking if == 1 after 1 removed.
            ul2 = u['loaded'][0]
            ul2['position'] = (-10, -10 - 1)

    def capture_success(self, position):
        armies = [
            'neutral', 'amberblaze', 'blackhole', 'bluemoon', 'browndesert', 'greenearth', 'jadesun',
            'orangestar', 'redfire', 'yellowcomet', 'greysky', 'cobaltice', 'pinkcosmos', 'tealgalaxy',
            'purplelightning', 'acidrain', 'whitenova', 'azureasteroid', 'noireclipse'
        ]
        if self.map_info[1][position] == 3 and self.map_info[5][position] == 5:
            com = True  # com tower got captured
        else:
            com = False
        preowned = False
        if self.turns % 2 == 0:
            self.p1['properties'] += 1
            props = self.p1['properties']
            army = self.p1['army']
            if self.p2['army'] == armies[self.map_info[0][position]]:  # check whether enemy owned this property before
                preowned = True
            self.map_info[0][position] = armies.index(self.p1['army'])  # set new owner
        else:
            self.p2['properties'] += 1
            props = self.p2['properties']
            army = self.p2['army']
            if self.p1['army'] == armies[self.map_info[0][position]]:  # check whether enemy owned this property before
                preowned = True
            self.map_info[0][position] = armies.index(self.p2['army'])

        if props >= self.map_rules['capturel']:
            self.winner = army
            print(f"{self.winner} win by reaching capture limit!")

        if preowned:
            if self.map_info[1][position] == 4 and self.map_info[5][position] == 6:  # if hq
                self.winner = army
                print(f"{self.winner} win by hq cap!")
            elif self.map_info[1][position] == 3 and self.map_info[5][position] == 6:  # if lab
                enemy_labs = 0
                for x in range(len(self.map_info[0].shape[0])):
                    for y in range(len(self.map_info[0].shape[0])):
                        if self.map_info[1][(x, y)] == 3 and self.map_info[5][(x, y)] == 6:
                            enemy_labs += 1
                            break
                    if enemy_labs != 0:
                        break
                if enemy_labs == 0:
                    self.winner = army
                    print(f"{self.winner} win by final enemy lab capture!")
            if self.turns % 2 == 0:
                self.p2['properties'] -= 1
                if com:
                    self.p1['com'] += 1
                    self.p2['com'] -= 1
            else:
                self.p1['properties'] -= 1
                if com:
                    self.p1['com'] -= 1
                    self.p2['com'] += 1

        if com:
            self.p1, self.p2 = com_change(self.p1, self.p2)

        self.income_update()

    def income_update(self):
        armies = [
            'neutral', 'amberblaze', 'blackhole', 'bluemoon', 'browndesert', 'greenearth', 'jadesun', 'orangestar',
            'redfire', 'yellowcomet', 'greysky', 'cobaltice', 'pinkcosmos', 'tealgalaxy', 'purplelightning',
            'acidrain', 'whitenova', 'azureasteroid', 'noireclipse'
        ]
        sasha1 = 0 if self.p1['name'] != 'sasha' else 100
        sasha2 = 0 if self.p2['name'] != 'sasha' else 100
        p1army = armies.index(self.p1['army'])
        p2army = armies.index(self.p2['army'])
        p1in = 0
        p2in = 0
        for e in np.argwhere(self.map_info[0] != 0):
            # todo change to just [e] instead of [e[0], e[1]]
            if self.map_info[2][e[0], e[1]] != 0:  # if it can repair it provides income :>
                if self.map_info[0][e[0], e[1]] == p1army:
                    p1in += self.income + sasha1
                elif self.map_info[0][e[0], e[1]] == p2army:
                    p2in += self.income + sasha2
                else:
                    raise CustomError("Somehow a property is not neutral and not either army. huh")
        self.p1['income'] = p1in
        self.p2['income'] = p2in

    def power(self, level):
        if self.turns % 2 == 0:
            self.p1, self.p2 = power(self.p1, self.p2, level)
        else:
            self.p2, self.p1 = power(self.p2, self.p1, level)

    def turn_end(self):
        if len(self.map_info[0]) == 0:
            print("load a map before ending turn please")
            return  # todo should be a raise?

        self.turns += 1
        self.turn_swap()

    def turn_swap(self):  # p1 -> p2 turn end/start
        if self.turns % 2 == 1:  # going to p2 from p1
            p1, p2 = self.p1, self.p2
        else:  # going to p1 from p2
            p1, p2 = self.p2, self.p1

        # check win conditions (day limit ig?)
        p1win = False
        if p1['properties'] >= self.map_rules['capturel']:
            p1win = True
        if int((self.turns + 1) / 2) + 1 >= self.map_rules['dayl'] > 0:  # turn limit in days
            if p1['properties'] > p2['properties']:  # tiebreaker number of properties
                p1win = True
        if self.turns >= 2 and len(p2['units']) == 0:  # if p2 has no units and it's not the start of the game
            p1win = True
        if p1win:
            self.winner = p1['army']

        p2, p1 = activate_or_deactivate_power(p2, p1, -p2['power'])  # p2's power gets deactivated if it was on
        p2['funds'] = int(p2['funds'] + int(p2['income']))  # income before property repairs
        p2 = turn_resupplies(p2, self.map_info)

        if p1['name'] == 'von bolt':  # check for von bolt power after giving units move so you can take it away
            if self.von_bolt_missile[0] == self.turns - 1:
                pos = self.von_bolt_missile[1]
                x = pos[1]
                y = pos[0]
                for pos in [
                    (y + 2, x),
                    (y + 1, x - 1), (y + 1, x), (y + 1, x + 1),
                    (y, x - 2), (y, x - 1), (y, x), (y, x + 1), (y, x + 2),
                    (y - 1, x - 1), (y - 1, x), (y - 1, x + 1),
                    (y - 2, x)
                ]:  # coordinates surrounding the missile centre
                    if 0 <= pos[1] < self.map_info[0].shape[1] and 0 <= pos[0] < self.map_info[0].shape[0]:
                        # if the position is a valid coordinate
                        for target in p2['units']:  # only enemy get stunned even though self damage is done? todo check
                            if target['position'] == pos:  # search for a unit in that position
                                target['move'] = 0
        elif p1['name'] in ['drake', 'olaf']:
            rain_snow = 1  # todo remove rain/snow
            # only remove it if the other player hasn't made it also happen before they ended turn!!!!!

        self.income_update()


def power(co1, co2, level):
    if co1['power'] != 0:
        raise CustomError ("power already activated!")
    if level == 1 and co1['name'] == 'von bolt':
        raise CustomError("von bolt doesn't have a COP!")
    return activate_or_deactivate_power(co1, co2, level)


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
