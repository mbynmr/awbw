

def unit_maker(army, typ, co, position, stars=3, terr=5, hp=99, fuel=None, ammo=None):
    # stars defaults to 3 for base etc, same for terr (urban = 5)
    types = {
        'aa': [6, 9, 60, 0, [1, 1], 'treads', 8000],
        'apc': [6, 0, 60, 0, [0, 0], 'treads', 5000],
        'arty': [5, 9, 50, 0, [2, 3], 'treads', 6000],
        'bcopter': [6, 6, 99, 2, [1, 1], 'air', 9000],
        'bship': [5, 9, 99, 1, [2, 6], 'sea', 28000],
        'bboat': [7, -1, 50, 1, [0, 0], 'lander', 7500],
        'bbomb': [9, 0, 45, 5, [0, 0], 'air', 25000],
        'bomber': [7, 9, 99, 5, [1, 1], 'air', 22000],
        'carrier': [5, 9, 99, 1, [3, 8], 'sea', 30000],
        'cruiser': [6, 9, 99, 1, [1, 1], 'sea', 18000],
        'fighter': [9, 9, 99, 5, [1, 1], 'air', 20000],
        'inf': [3, -1, 99, 0, [1, 1], 'inf', 1000],
        'lander': [6, 0, 99, 1, [0, 0], 'lander', 12000],
        'med': [5, 8, 50, 0, [1, 1], 'treads', 16000],
        'mech': [2, 3, 70, 0, [1, 1], 'mech', 3000],
        'mega': [4, 3, 50, 0, [1, 1], 'treads', 28000],
        'missile': [4, 6, 50, 0, [3, 5], 'tyre', 12000],
        'neo': [6, 9, 99, 0, [1, 1], 'treads', 22000],
        'pipe': [9, 9, 99, 0, [2, 5], 'pipe', 20000],
        'recon': [8, -1, 80, 0, [1, 1], 'tyre', 4000],
        'rocket': [5, 6, 50, 0, [3, 5], 'tyre', 15000],
        'stealth': [6, 6, 60, 5, [1, 1], 'air', 24000],
        'sub': [5, 6, 60, 1, [1, 1], 'sea', 20000],
        'tcopter': [6, 0, 99, 2, [0, 0], 'air', 5000],
        'tank': [6, 9, 70, 0, [1, 1], 'treads', 7000]
    }  # move, ammo, fuel, fuel/day, range, tread, value
    this_unit = types[typ]

    unit = {
        'army': army, 'hp': hp, 'type': typ, 'value': this_unit[6],
        'fuel': this_unit[2] if fuel is None else fuel, 'fueluse': this_unit[3],
        'move': this_unit[0], 'tread': this_unit[5], 'Dtr': stars, 'terr': terr, 'position': position,
        'ammo': this_unit[1] if ammo is None else ammo, 'range': this_unit[4],
        'Av': 100, 'Dv': 100, 'L': [0, 9]
    }
    return unit_stats_editor(unit, co['name'], co['comm'], co['power'], co['funds'], co['properties'])


def unit_stats_editor(unit, name, comm, power, funds, properties):
    # all_unit_typ = [
    #     'aa', 'apc', 'arty', 'bcopter', 'bship', 'bboat', 'bbomb', 'bomber', 'carrier', 'cruiser', 'fighter', 'inf',
    #     'lander', 'med', 'mech', 'mega', 'missile', 'neo', 'pipe', 'recon', 'rocket', 'stealth', 'sub', 'tcopter',
    #     'tank'
    #     ]
    # direct = [
    #     'aa', 'bcopter', 'bomber', 'cruiser', 'fighter', 'inf',
    #     'med', 'mech', 'mega', 'neo', 'recon', 'stealth', 'sub',
    #     'tank'
    #     ]
    foot = unit['type'] in ['inf', 'mech']
    veh = unit['type'] in ['aa', 'apc', 'arty', 'med', 'mega', 'missile', 'neo', 'pipe', 'recon', 'rocket', 'tank']
    indirect = unit['type'] in ['arty', 'bship', 'carrier', 'missile', 'pipe', 'rocket']
    transport = unit['type'] in ['apc', 'bboat', 'lander', 'tcopter']
    air = unit['type'] in ['bcopter', 'bbomb', 'bomber', 'fighter', 'stealth', 'tcopter']
    sea = unit['type'] in ['bship', 'bboat', 'carrier', 'cruiser', 'lander', 'sub']

    # attack
    unit['Av'] += comm
    # luck
    # range
    # move
    # fuel
    # value
    # stars
    match name:
        case 'andy':
            if power == 2:
                unit['move'] += 1
                unit['Av'] += 10
        case 'hachi':
            unit['value'] = int(unit['value'] * (0.9 if power == 0 else 0.5))
        case 'jake':
            if power != 0:
                if indirect and not (air or sea):
                    unit['range'][-1] += 1
                if veh:
                    unit['move'] += 2
                if unit['terr'] == 4:  # 4 is code for plain
                    unit['Av'] += 20 * power
            elif unit['terr'] == 4:
                unit['Av'] += 10
        case 'max':
            if indirect:
                unit['range'][-1] -= 1
                unit['Av'] -= 10
            if not indirect and not (foot or transport):
                unit['Av'] += 20
                unit['move'] += power  # hehe
                if power == 1:
                    unit['Av'] += 10
                if power == 2:
                    unit['Av'] += 30
        case 'nell':
            if not transport:
                unit['L'][-1] += 10 + 40 * power
        case 'rachel':
            if power == 1 and not transport:
                unit['L'][-1] += 30
        case 'sami':
            if foot:
                unit['Av'] += 30 + 20 * power
                unit['move'] += power
            elif not indirect:
                unit['Av'] -= 10
                if transport:
                    unit['move'] += 1
        case 'colin':
            unit['value'] = int(unit['value'] * 0.8)
            # I don't think I'll ever know how value rounding works but that's my guess!
            unit['Av'] -= 10
            if power == 2:
                unit['Av'] += int(3 * funds / 1000)
            # I don't think I'll ever know how attack rounding works but that's my guess!
        case 'grit':
            if indirect:
                unit['range'][-1] += 1 + power
                unit['Av'] += 20 + (0 if power == 0 else 20)
            else:
                unit['Av'] -= 20
        # case 'olaf':
        # case 'sasha':
        case 'drake':
            if sea:
                unit['move'] += 1
                unit['Dv'] += 10
            elif air:
                unit['Av'] -= 30
        case 'eagle':
            if air:
                unit['Av'] += 15 + (0 if power == 0 else 5)
                unit['Dv'] += 10 + (0 if power == 0 else 10)
                unit['fueluse'] -= 2
            elif sea:
                unit['Av'] -= 30
        case 'javier':
            unit['Dv'] += comm
        case 'jess':
            if veh:
                if power != 0:
                    unit['Av'] += 20 * power
                    unit['move'] += power
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
                    unit['ammo'] = types[unit['type']][0]
                    unit['fuel'] = types[unit['type']][1]
                else:
                    unit['Av'] += 10
            else:
                unit['Av'] -= 10
        case 'grimm':
            unit['Dv'] -= 20
            if power != 0:
                unit['Av'] += 50 + (30 if power == 2 else 0)
            else:
                unit['Av'] += 30
        case 'kanbei':
            unit['value'] = int(unit['value'] * 1.2)
            unit['Dv'] += 30
            if power != 0:
                unit['Av'] += 40
                if power == 2:
                    unit['Dv'] += 20
            else:
                unit['Av'] += 30
        case 'sensei':
            if unit['type'] == 'bcopter':
                unit['Av'] += 50 + (15 if power != 0 else 0)
            elif foot:
                unit['Av'] += 40
            elif transport:
                unit['move'] += 1
            elif not air:
                unit['Av'] -= 10
        case 'sonja':
            if not transport:
                unit['L'][0] -= 9
        case 'adder':
            unit['move'] += power
        case 'flak':
            if not transport:
                if power == 0:
                    unit['L'][0] -= 9
                    unit['L'][1] += 15
                elif power == 1:
                    unit['L'][0] -= 19
                    unit['L'][1] += 40
                else:
                    unit['L'][0] -= 39
                    unit['L'][1] += 80
        case 'hawke':
            unit['Av'] += 10
        case 'jugger':
            if not transport:
                if power == 0:
                    unit['L'][0] -= 14
                    unit['L'][1] += 20
                elif power == 1:
                    unit['L'][0] -= 24
                    unit['L'][1] += 45
                else:
                    unit['L'][0] -= 44
                    unit['L'][1] += 85
        case 'kindle':
            if power == 2:
                unit['Av'] += 3 * properties
            if unit['terr'] == 5:  # 5 is code for urban
                if power == 0:
                    unit['Av'] += 40
                elif power == 1:
                    unit['Av'] += 80
                else:
                    unit['Av'] += 130
        case 'koal':
            unit['move'] += power
            if unit['terr'] == 3:  # 3 is code for road
                unit['Av'] += 10 + 10 * power
        case 'lash':
            if not air:
                if power == 2:
                    unit['Dtr'] *= 2
                unit['Av'] += 10 * unit['Dtr']
        case 'sturm':
            unit['Av'] -= 20
            unit['Dv'] += 20
        case 'von bolt':
            unit['Av'] += 10
            unit['Dv'] += 10

    if power != 0:
        unit['Av'] += 10
        unit['Dv'] += 10

    return unit


def name_to_filename(name):
    types = {
        'aa': 'anti-air',
        # 'apc': 'apc',
        'arty': 'artillery',
        'bcopter': 'b-copter',
        # 'bship': ,
        'bboat': 'blackboat',
        # 'bbomb': ,
        'bomber': 'bomber',
        # 'carrier':,
        # 'cruiser':,
        'fighter': 'fighter',
        'inf': 'infantry',
        # 'lander': ,
        'med': 'md.tank',
        'mech': 'mech',
        'mega': 'megatank',
        # 'missile': ,
        # 'neo': ,
        # 'pipe': ,
        'recon': 'recon',
        'rocket': 'rocket',
        # 'stealth':,
        # 'sub': ,
        # 'tcopter': ,
        'tank': 'tank'
    }  # move, ammo, fuel, fuel/day, range, tread, value
    if name in types:
        return types[name]
    else:
        return 'rocket'  # both have rocket for now


def junk():
    # not needed anymore now we're using a big dict
    move = [
        6, 6, 5, 6, 5, 7, 9, 7, 5, 6, 9, 3,
        6, 5, 2, 4, 4, 6, 9, 8, 5, 6, 5, 6,
        6,
    ]
    ammo = [
        9, 0, 9, 6, 9, -1, 0, 9, 9, 9, 9, -1,
        0, 8, 3, 3, 6, 9, 9, -1, 6, 6, 6, 0,
        9
    ]
    fuel = [
        60, 60, 50, 99, 99, 50, 45, 99, 99, 99, 99, 99,
        99, 50, 70, 50, 50, 99, 99, 80, 50, 60, 60, 99,
        70
    ]
    fuel_per_day = [
        0, 0, 0, 2, 1, 1, 5, 5, 1, 1, 5, 0,
        1, 0, 0, 0, 0, 0, 0, 0, 0, 5, 1, 2,
        0
    ]
    range = [
        [1, 1], [0, 0], [2, 3], [1, 1], [2, 6], [0, 0], [0, 0], [1, 1], [3, 8], [1, 1], [1, 1], [1, 1],
        [0, 0], [1, 1], [1, 1], [1, 1], [3, 5], [1, 1], [2, 5], [1, 1], [3, 5], [1, 1], [1, 1], [0, 0],
        [1, 1]
    ]  # [2, 3] means ----xx-o-xx---- where o is position of the unit, - not shootable, x shootable
    tread = [
        'treads', 'treads', 'treads', 'air', 'sea', 'lander', 'air', 'air', 'sea', 'sea', 'air', 'inf',
        'lander', 'treads', 'mech', 'treads', 'tyre', 'treads', 'pipe', 'tyre', 'tyre', 'air', 'sea', 'air',
        'treads'
    ]
    value = [
        8000, 5000, 6000, 9000, 28000, 7500, 25000, 22000, 30000, 18000, 20000, 1000,
        12000, 16000, 3000, 28000, 12000, 22000, 20000, 4000, 15000, 24000, 20000, 5000,
        7000
    ]
