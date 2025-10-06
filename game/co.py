import numpy as np

from unit import unit_maker
from customerrors import CustomError


def co_maker(name='jake', army='neutral'):
    co_list = {
        'andy': [3, 6], 'hachi': [3, 5], 'jake': [3, 6], 'max': [3, 6], 'nell': [3, 6], 'rachel': [3, 6],
        'sami': [3, 8],
        'colin': [2, 6], 'grit': [3, 6], 'olaf': [3, 7], 'sasha': [2, 6],
        'drake': [4, 7], 'eagle': [3, 9], 'javier': [3, 6], 'jess': [3, 6],
        'grimm': [3, 6], 'kanbei': [4, 7], 'sensei': [2, 6], 'sonja': [3, 5],
        'adder': [2, 5], 'flak': [3, 6], 'hawke': [5, 9], 'jugger': [3, 7], 'kindle': [3, 6], 'koal': [3, 5],
        'lash': [4, 7], 'sturm': [6, 10], 'von bolt': [0, 10]
    }
    power_cost = co_list[name]
    return {
        'name': name, 'army': army, 'com': int(0), 'properties': int(0), 'income': int(0), 'funds': int(0),
        'power': int(0), 'charge': int(0), 'COP': power_cost[0], 'SCOP': power_cost[1], 'starcost': int(0), 'units': []
    }  # power: 0=CO, 1=COP, 2=SCOP


def com_change(co1, co2):
    return activate_or_deactivate_power(co1, co2, 0)  # the one time power=0 is input to a_o_d_p


def activate_or_deactivate_power(co1, co2, power_level_change):
    # set co stats
    # remake all units

    # costs = {0: 1, 1: 1.2, 2: 1.4, 3: 1.6, 4: 1.8, 5: 2, 6: 2.2, 7: 2.4, 8: 2.6, 9: 2.8, 10: 2}  # cart accurate?
    costs = {0: 1, 1: 1.2, 2: 1.4, 3: 1.6, 4: 1.8, 5: 2, 6: 2.2, 7: 2.4, 8: 2.6, 9: 2.8, 10: 3}  # awbw accurate
    if power_level_change == 2:
        if co1['charge'] >= co1['SCOP'] * costs[co1['starcost']] * 9000:
            co1['charge'] -= co1['SCOP'] * costs[co1['starcost']] * 9000
        else:
            raise CustomError("not enough charge for SCOP")
    elif power_level_change == 1:
        if co1['charge'] >= co1['COP'] * costs[co1['starcost']] * 9000:
            co1['charge'] -= co1['COP'] * costs[co1['starcost']] * 9000
        else:
            raise CustomError("not enough charge for COP")

    # set
    co1['power'] += power_level_change
    if power_level_change >= 1:
        if co1['starcost'] < 10:
            co1['starcost'] += 1

    if power_level_change >= 1:  # powers going on
        match co1['name']:
            case 'andy':
                for unit in co1['units']:
                    unit['hp'] += (20 if power_level_change == 1 else 50)
                    if unit['hp'] >= 90:  # check this rounding. I'm p sure if it shows as full hp it gets all 99
                        unit['hp'] = 99
                    # co1['units'][i] = unit
            case 'rachel':
                if power_level_change == 2:
                    # The missiles target the opponents' greatest accumulation of:
                    #  footsoldier HP (hp damage dealt, not hp in blob)
                    #  unit value(value damage dealt, not value in blob)
                    #  unit HP (hp damage dealt, not hp in blob)

                    # todo missile locations
                    pos = (1, 2)  # primary: inf hp, seconday: value (including friendly!!)
                    co1['units'] = missile(pos, units=co1['units'])
                    co2['units'] = missile(pos, units=co2['units'])
                    pos = (3, 2)  # value todo indirects have 2x value
                    co1['units'] = missile(pos, units=co1['units'])
                    co2['units'] = missile(pos, units=co2['units'])
                    pos = (6, 2)  # hp
                    co1['units'] = missile(pos, units=co1['units'])
                    co2['units'] = missile(pos, units=co2['units'])
            case 'colin':
                if power_level_change == 1:
                    co1['funds'] = int(co1['funds'] * 1.5)  # assuming this is how it rounds
            case 'olaf':  # todo snow cover
                if power_level_change == 2:
                    for unit in co2['units']:
                        unit['hp'] -= 20
                        if unit['hp'] <= 1:
                            unit['hp'] = 1
                        # co2['units'][i] = unit
            case 'sasha':
                if power_level_change == 1:
                    c = co2['charge'] - co2['SCOP'] * (co1['funds'] * 10 / 50)
                    co2['charge'] = (int(c) if c > 0 else 0)
            case 'drake':  # todo rain cover
                for unit in co2['units']:  # damage enemies
                    if unit['position'] != (-10, -10):  # units in transports don't get hit
                        unit['hp'] -= 10 if power_level_change == 1 else 20
                        if unit['hp'] < 0:
                            unit['hp'] = 0
                        unit['fuel'] = int(unit['fuel'] / 2)  # do 0 fuel things crash instantly? start of p2 turn?
                        # co2['units'][i] = unit
            case 'eagle':
                if power_level_change == 2:
                    for unit in co1['units']:
                        unit['move'] = None  # setting None tricks unit_maker into resetting it to full
            case 'javier':
                co1['com'] *= 1 + power_level_change
                # [-2, -1, 0, 1, 2]
                # [1/3, 1/2, 1, 2, 3]
            case 'jess':
                for unit in co1['units']:
                    unit['ammo'] = None  # setting None tricks unit_maker into resetting it to full
                    unit['fuel'] = None  # setting None tricks unit_maker into resetting it to full
            case 'sensei':
                x = 1
                # spawn first
                # todo spawn lol that's hard.
                # set stats second bcus all units are getting remade after anyway.
            case 'hawke':
                for unit in co2['units']:  # damage enemies
                    if unit['position'] != (-10, -10):  # units in transports don't get hit
                        unit['hp'] -= 10 if power_level_change == 1 else 20
                        if unit['hp'] < 0:
                            unit['hp'] = 0
                for unit in co1['units']:  # heal friendlies
                    if unit['position'] != (-10, -10):  # units in transports don't get healed
                        unit['hp'] += 10 if power_level_change == 1 else 20
                        if unit['hp'] > 99:
                            unit['hp'] = 99
            case 'lash':
                if power_level_change == 2:
                    for unit in co1['units']:
                        unit['Dtr'] *= 2
                        # co1['units'][i] = unit
            case 'sturm':
                pos = (6, 2)  # todo missile position
                # The missile targets an enemy unit located at the greatest accumulation of unit value.
                # key: sturm requires a unit to be at the centre of the missile.
                co1['units'] = missile(pos, units=co1['units'], hp=(4 if power_level_change == 1 else 8))
                co2['units'] = missile(pos, units=co2['units'], hp=(4 if power_level_change == 1 else 8))
            case 'von bolt':
                pos = (6, 2)  # todo missile position
                # The missile targets the opponents' greatest accumulation of unit value.
                co1['units'] = missile(pos, units=co1['units'])
                co2['units'] = missile(pos, units=co2['units'])
    elif power_level_change <= -1:  # powers going off
        match co1['name']:
            case 'lash':
                if power_level_change == -2:
                    for unit in co1['units']:
                        unit['Dtr'] /= 2
            case 'javier':
                co1['com'] /= 1 - power_level_change

    # remake
    for i, unit in enumerate(co1['units']):
        co1['units'][i] = unit_maker(
            unit['army'], unit['type'], co1, unit['position'], stars=unit['Dtr'], terr=unit['terr'], hp=unit['hp'],
            fuel=unit['fuel'], ammo=unit['ammo'], capture=unit['capture'], hidden=unit['hidden'], loaded=unit['loaded'],
            move=unit['move']
        )
    return co1, co2


def missile(pos, units, hp=3):
    x = pos[1]
    y = pos[0]
    for pos in [
        (y + 2, x),
        (y + 1, x - 1), (y + 1, x), (y + 1, x + 1),
        (y, x - 2), (y, x - 1), (y, x), (y, x + 1), (y, x + 2),
        (y - 1, x - 1), (y - 1, x), (y - 1, x + 1),
        (y - 2, x)
    ]:  # coordinates surrounding the missile centre (some are outside the map, who cares)
        for target in units:
            if target['position'] == pos:  # search for a unit in that position
                target['hp'] -= hp * 10
                if target['hp'] < 0:
                    target['hp'] = 0  # missiles never kill but they can leave units on minimum hp
    return units


def turn_resupplies(co, map_info):
    # does property resupply & repair
    # does apc + bboat resupply
    # crashes air and sinks sea that are out of fuel
    # calculates fuel usage for air and sea

    coname = co['name']
    coarmy = [
        'neutral', 'amberblaze', 'blackhole', 'bluemoon', 'browndesert', 'greenearth', 'jadesun', 'orangestar',
        'redfire', 'yellowcomet', 'greysky', 'cobaltice', 'pinkcosmos', 'tealgalaxy', 'purplelightning',
        'acidrain', 'whitenova', 'azureasteroid', 'noireclipse'
    ].index(co['army'])
    types = {
        'aa': [6, 9, 60, 0, [1, 1], 'tracks', 8000],
        'apc': [6 if coname not in ['sami', 'sensei'] else 7, 0, 60, 0, [0, 0], 'tracks', 5000],
        'arty': [5, 9, 50, 0, [2, 3], 'tracks', 6000],
        'bcopter': [6, 6, 99, 2, [1, 1], 'air', 9000],
        'bship': [5 if coname != 'drake' else 6, 9, 99, 1, [2, 6], 'sea', 28000],
        'bboat': [7 if coname not in ['sami', 'sensei', 'drake'] else 8, -1, 50, 1, [0, 0], 'lander', 7500],
        'bbomb': [9, 0, 45, 5, [0, 0], 'air', 25000],
        'bomber': [7, 9, 99, 5, [1, 1], 'air', 22000],
        'carrier': [5 if coname != 'drake' else 6, 9, 99, 1, [3, 8], 'sea', 30000],
        'cruiser': [6 if coname != 'drake' else 7, 9, 99, 1, [1, 1], 'sea', 18000],
        'fighter': [9, 9, 99, 5, [1, 1], 'air', 20000],
        'inf': [3, -1, 99, 0, [1, 1], 'inf', 1000],
        'lander': [6 if coname not in ['sami', 'sensei', 'drake'] else 7, 0, 99, 1, [0, 0], 'lander', 12000],
        'med': [5, 8, 50, 0, [1, 1], 'tracks', 16000],
        'mech': [2, 3, 70, 0, [1, 1], 'mech', 3000],
        'mega': [4, 3, 50, 0, [1, 1], 'tracks', 28000],
        'missile': [4, 6, 50, 0, [3, 5], 'tyre', 12000],
        'neo': [6, 9, 99, 0, [1, 1], 'tracks', 22000],
        'pipe': [9, 9, 99, 0, [2, 5], 'pipe', 20000],
        'recon': [8, -1, 80, 0, [1, 1], 'tyre', 4000],
        'rocket': [5, 6, 50, 0, [3, 5], 'tyre', 15000],
        'stealth': [6, 6, 60, 5, [1, 1], 'air', 24000],
        'sub': [5 if coname != 'drake' else 6, 6, 60, 1, [1, 1], 'sea', 20000],
        'tcopter': [6 if coname not in ['sami', 'sensei'] else 7, 0, 99, 2, [0, 0], 'air', 5000],
        'tank': [6, 9, 70, 0, [1, 1], 'tracks', 7000]
    }  # move, ammo, fuel, fuel/day, range, tread, value
    sea = ['bboat', 'lander', 'bship', 'bboat', 'carrier', 'cruiser', 'lander', 'sub']
    air = ['tcopter', 'bcopter', 'bbomb', 'bomber', 'fighter', 'stealth', 'tcopter']

    for u in co['units']:
        utype = u['type']
        if utype in air or utype in sea:
            u['fuel'] -= u['fueluse']
            if u['fuel'] < 0:
                co['units'].remove(u)  # todo check order. do stealths on airports get resupplied or crash?
                continue  # todo check order. does a sinking black boat resupply units next to it before sploosh?
        u['move'] = types[utype][0]  # every unit gets full move again

        repair = False
        if u['position'] != (-10, -10):  # loaded units break this so make sure we don't include them
            if coarmy == map_info[0][u['position']]:  # if this tile is owned by this co
                # map_info[2] (repair) - 0: none, 1: ground, 2: sea, 3: air
                match map_info[2][u['position']]:
                    case 1:
                        if utype not in air and utype not in sea:
                            repair = True
                    case 2:
                        if utype in sea:
                            repair = True
                    case 3:
                        if utype in air:
                            repair = True
        if repair:
            display_hp = int(1 + u['hp'] / 10)
            if co['funds'] >= u['value'] / 10:  # heal 1hp
                u['hp'] += 10
            if co['funds'] >= u['value'] * 2 / 10:  # heal 2hp
                u['hp'] += 10
            if co['funds'] >= u['value'] * 3 / 10 and coname == 'rachel':  # heal 3hp
                u['hp'] += 10
            if u['hp'] >= 90:  # doesn't matter if we go over 99 because you only lose funds for visible hp
                u['hp'] = 99  # and it gets capped to 99
            u['ammo'] = types[utype][1]
            u['fuel'] = types[utype][2]
            co['funds'] = int(co['funds'] - u['value'] * (int(1 + u['hp'] / 10) - display_hp) / 10)

        if utype in ['apc', 'bboat']:  # find every apc and black boat
            x = u['position'][1]
            y = u['position'][0]
            for test_pos in [(y - 1, x), (y, x - 1), (y + 1, x), (y, x + 1)]:  # 4 coordinates next to that unit
                if 0 <= test_pos[1] < map_info[0].shape[1] and 0 <= test_pos[0] < map_info[0].shape[0]:
                    # if the position is a valid coordinate
                    for target in co['units']:
                        if target['position'] == test_pos:  # search for a unit in that position
                            target['ammo'] = types[target['type']][1]
                            target['fuel'] = types[target['type']][2]

    return co

# thing = {'0': -0, '1': -1, '2': -2, '3': -3, '4': -4}
# for i, (k, e) in enumerate(thing.items()):
#     thing[k] = e + 5
