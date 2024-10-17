import numpy as np

from unit import unit_maker


def co_maker(name='jake'):
    co_list = {
        'andy': [3, 6], 'hachi': [3, 5], 'jake': [3, 6], 'max': [3, 6], 'nell': [3, 6], 'rachel': [3, 6],
        'sami': [3, 8],
        'colin': [2, 6], 'grit': [3, 6], 'olaf': [3, 7], 'sasha': [2, 6],
        'drake': [4, 7], 'eagle': [3, 9], 'javier': [3, 6], 'jess': [3, 6],
        'grimm': [3, 6], 'kanbei': [4, 7], 'sensei': [2, 6],  'sonja': [3, 5],
        'adder': [2, 5], 'flak': [3, 6], 'hawke': [5, 9],  'jugger': [3, 7], 'kindle': [3, 6], 'koal': [3, 5],
        'lash': [4, 7],  'sturm': [6, 10], 'von bolt': [0, 10]
    }
    power_cost = co_list[name]
    return {
        'name': name, 'army': 'neutral', 'comm': 0, 'properties': 0, 'income': 0, 'funds': 0,
        'power': 0, 'charge': 0, 'COP': power_cost[0], 'SCOP': power_cost[1], 'starcost': 0, 'units': []
    }  # power: 0=CO, 1=COP, 2=SCOP


def activate_or_deactivate_power(co1, co2, power_level_change):
    # set co stats
    # remake all units

    # set
    co1['power'] += power_level_change
    if power_level_change >= 1:
        if co1['starcost'] < 10:
            co1['starcost'] += 1

    match co1['name']:
        case 'andy':
            if power_level_change >= 1:
                for i, unit in enumerate(co1['units']):
                    unit['hp'] += (20 if power_level_change == 1 else 50)
                    if unit['hp'] >= 90:  # todo check this rounding. I'm p sure if it shows as full hp it gets all 99
                        unit['hp'] = 99
                    co1['units'][i] = unit
        case 'rachel':
            if power_level_change == 2:
                x = 1  # todo missiles.
                # can be done here. co1 and co2 are put in, and they contain units.
                # The missiles target the opponents' greatest accumulation of:
                #  footsoldier HP (hp damage dealt, not hp in blob)
                #  unit value(value damage dealt, not value in blob)
                #  unit HP (hp damage dealt, not hp in blob)
        case 'colin':
            if power_level_change == 1:
                co1['funds'] = int(co1['funds'] * 1.5)  # assuming this is how it rounds
        case 'olaf':  # todo snow cover/uncover
            if power_level_change == 2:
                for i, unit in enumerate(co2['units']):
                    unit['hp'] -= 20
                    if unit['hp'] <= 1:
                        unit['hp'] = 1
                    co2['units'][i] = unit
        case 'sasha':
            if power_level_change == 1:
                c = co2['charge'] - co2['SCOP'] * (co1['funds'] * 10 / 50)
                co2['charge'] = (int(c) if c > 0 else 0)
        case 'drake':
            if power_level_change >= 1:
                for i, unit in enumerate(co2['units']):
                    if unit['position'] != (-10, -10):  # units in transports don't get hit
                        unit['hp'] -= (10 if power_level_change == 1 else 20)
                        if unit['hp'] <= 1:
                            unit['hp'] = 1
                        unit['fuel'] = int(unit['fuel'] / 2)  # do 0 fuel things crash instantly?
                        co2['units'][i] = unit
        case 'sensei':
            x = 1
            # spawn first
            # todo spawn lol that's hard.
            # set stats second bcus all units are getting remade after anyway.
        case 'javier':
            if power_level_change < 0:
                co1['comm'] /= 1 - power_level_change
            else:
                co1['comm'] *= 1 + power_level_change
            # [-2, -1, 0, 1, 2]
            # [1/3, 1/2, 1, 2, 3]
        case 'lash':
            if power_level_change == -2:
                for i, unit in enumerate(co1['units']):
                    unit['Dtr'] /= 2
                    co1['units'][i] = unit  # todo check this works. is same below. check plz ty

    # remake
    for i, unit in enumerate(co1['units']):
        co1['units'][i] = unit_maker(
            unit['army'], unit['type'], co1, unit['position'], stars=unit['Dtr'], terr=unit['terr'], hp=unit['hp'],
            fuel=unit['fuel'], ammo=unit['ammo'], hidden=unit['hidden'], loaded=unit['loaded']
        )
    return co1, co2

# thing = {'0': -0, '1': -1, '2': -2, '3': -3, '4': -4}
# for i, (k, e) in enumerate(thing.items()):
#     thing[k] = e + 5
