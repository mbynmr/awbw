from co import unit_stats_maker


def unit_maker(army, typ, co, position, stars=3, terr=5):  # stars defaults to 3 for base etc, same for terr (urban = 5)
    types = {
        'aa': [6, 9, 60, 0, [1, 1], 'treads', 8000],
        'apc': [6, 0, 60, 0, [0, 0], 'treads', 5000],
        'arty': [6, 9, 50, 0, [2, 3], 'treads', 6000],
        'bcopter': [6, 6, 99, 2, [1, 1], 'air', 9000],
        'bship': [6, 9, 99, 1, [2, 6], 'sea', 28000],
        'bboat': [6, -1, 50, 1, [0, 0], 'lander', 7500],
        'bbomb': [6, 0, 45, 5, [0, 0], 'air', 25000],
        'bomber': [6, 9, 99, 5, [1, 1], 'air', 22000],
        'carrier': [6, 9, 99, 1, [3, 8], 'sea', 30000],
        'cruiser': [6, 9, 99, 1, [1, 1], 'sea', 18000],
        'fighter': [6, 9, 99, 5, [1, 1], 'air', 20000],
        'inf': [6, -1, 99, 0, [1, 1], 'inf', 1000],
        'lander': [6, 0, 99, 1, [0, 0], 'lander', 12000],
        'med': [6, 8, 50, 0, [1, 1], 'treads', 16000],
        'mech': [6, 3, 70, 0, [1, 1], 'mech', 3000],
        'mega': [6, 3, 50, 0, [1, 1], 'treads', 28000],
        'missile': [6, 6, 50, 0, [3, 5], 'tyre', 12000],
        'neo': [6, 9, 99, 0, [1, 1], 'treads', 22000],
        'pipe': [6, 9, 99, 0, [2, 5], 'pipe', 20000],
        'recon': [6, -1, 80, 0, [1, 1], 'tyre', 4000],
        'rocket': [6, 6, 50, 0, [3, 5], 'tyre', 15000],
        'stealth': [6, 6, 60, 5, [1, 1], 'air', 24000],
        'sub': [6, 6, 60, 1, [1, 1], 'sea', 20000],
        'tcopter': [6, 0, 99, 2, [0, 0], 'air', 5000],
        'tank': [6, 9, 70, 0, [1, 1], 'treads', 7000]
    }  # move, ammo, fuel, fuel/day, range, tread, value
    this_unit = types[typ]

    unit = {
        'army': army, 'hp': 99, 'type': typ, 'value': this_unit[6],
        'fuel': this_unit[2], 'fueluse': this_unit[3],
        'move': this_unit[0], 'tread': this_unit[5], 'Dtr': stars, 'terr': terr, 'position': position,
        'ammo': this_unit[1], 'range': this_unit[4],
        'Av': 0, 'Dv': 100, 'L': [0, 9]
    }
    return unit_stats_maker(unit, co['name'], co['comm'], co['power'], co['funds'], co['properties'])


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
