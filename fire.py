import numpy as np


def fire(unit1, unit2, counter=True):
    dmg = damage_calc(unit1, unit2)
    unit1['ammo'] = unit1['ammo'] - 1
    unit2['hp'] = unit2['hp'] - dmg

    if unit2['hp'] < 0:  # outside hp range (0 to 99 is alive. 90-99 is 10hp, 0-9hp is 1hp)
        return unit1, None  # without counter-attack
    if counter:
        dmg = damage_calc(unit2, unit1)
        unit2['ammo'] = unit2['ammo'] - 1
        unit1['hp'] = unit1['hp'] - dmg

        if unit1['hp'] < 0:
            return None, unit2  # counter-attack destroys attacker
    return unit1, unit2  # no destruction


def damage_calc(u1, u2):
    base = base_damage(u1['type'], u2['type'], 'AMMO' if u1['ammo'] == 0 else '')  # base damage lookup
    if base == 0:
        raise ValueError(f"attack not valid. put an extra check in somewhere to avoid"
                         f"{u1['type']} with ammo {u1['ammo']} on {u2['type']}")
    damage = base * u1['Av'] / 100 + np.random.choice(u1['L'][1] + u1['L'][0]) - u1['L'][0]  # attack value
    hp = int(1 + u1['hp'] / 10) / 10  # hp 'out of 10' divided by 10: full unit is 1x damage, half hp is 0.5x
    defence = 2 - (u2['Dv'] + (u2['Dtr'] * int(1 + u2['hp'] / 10))) / 100  # defence multiplier
    # is rounded up to the nearest interval of 0.05 then rounded down to the nearest integer
    # (float precision needs a round before the int())
    out = int(np.round(damage * hp * defence + 0.05, 5))
    return out if out == 0 else 0


def damage_calc_bounds(u1, u2):
    base = base_damage(u1['type'], u2['type'], 'AMMO' if u1['ammo'] == 0 else '')  # base damage lookup
    if base == 0:
        raise ValueError(f"attack not valid. put an extra check in somewhere to avoid"
                         f"{u1['type']} with ammo {u1['ammo']} on {u2['type']}")
    damageL = base * u1['Av'] / 100 + u1['L'][0]
    damageU = base * u1['Av'] / 100 + u1['L'][1]
    hp = int(1 + u1['hp'] / 10) / 10
    defence = 2 - (u2['Dv'] + (u2['Dtr'] * int(1 + u2['hp'] / 10))) / 100
    return int(np.round(damageL * hp * defence + 0.05, 5)), int(np.round(damageU * hp * defence + 0.05, 5))


def base_damage(type1, type2, ammo=''):  # default ammo is ok. if 'AMMO' is passed in, different calcs are done.
    types = [
        'aa', 'apc', 'arty', 'bcopter', 'bship', 'bboat', 'bbomb', 'bomber', 'carrier', 'cruiser', 'fighter', 'inf',
        'lander', 'med', 'mech', 'mega', 'missile', 'neo', 'pipe', 'recon', 'rocket', 'stealth', 'sub', 'tcopter',
        'tank',  # all units!
        'bcopterAMMO', 'cruiserAMMO', 'medAMMO', 'mechAMMO', 'megaAMMO', 'neoAMMO', 'tankAMMO'  # only these have 2ndary
    ]  # not allowed without ammo: aa, arty, bship, bomber, carrier, fighter, missile, pipe, rocket, stealth, sub
    table = [
        [45, 50, 50, 120, 0, 0, 120, 75, 0, 0, 65, 105, 0, 10, 105, 1, 55, 5, 25, 60, 55, 75, 0, 120, 25],  # aa
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # apc
        [75, 70, 75, 0, 40, 55, 0, 0, 45, 65, 0, 90, 55, 45, 85, 15, 80, 40, 70, 80, 80, 0, 60, 0, 70],  # arty
        [25, 60, 65, 0, 25, 25, 0, 0, 25, 55, 0, 0, 25, 25, 0, 10, 65, 20, 55, 55, 65, 0, 25, 0, 55],  # bcopter
        [85, 80, 80, 0, 50, 95, 0, 0, 60, 95, 0, 95, 95, 55, 90, 25, 90, 50, 80, 90, 85, 0, 95, 0, 80],  # bship
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # bboat
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # bbomb
        [95, 105, 105, 0, 75, 95, 0, 0, 75, 85, 0, 110, 95, 95, 110, 35, 105, 90, 105, 105, 105, 0, 95, 0, 105],  # bomb
        [0, 0, 0, 115, 0, 0, 120, 100, 0, 0, 100, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 100, 0, 115, 0],  # carrier
        [0, 0, 0, 0, 0, 25, 0, 0, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 90, 0, 0],  # cruiser
        [0, 0, 0, 100, 0, 0, 120, 100, 0, 0, 55, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 85, 0, 100, 0],  # fighter
        [5, 12, 15, 7, 0, 0, 0, 0, 0, 0, 0, 55, 0, 1, 45, 1, 25, 1, 5, 12, 25, 0, 0, 30, 5],  # inf
        # line break
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # lander
        [105, 105, 105, 0, 10, 35, 0, 0, 10, 45, 0, 0, 35, 55, 0, 25, 105, 45, 85, 105, 105, 0, 10, 0, 85],   # med
        [65, 75, 70, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 15, 0, 5, 85, 15, 55, 85, 85, 0, 0, 0, 55],  # mech
        [195, 195, 195, 0, 45, 105, 0, 0, 45, 65, 0, 0, 75, 125, 0, 65, 195, 115, 180, 195, 195, 0, 45, 0, 180],  # mega
        [0, 0, 0, 120, 0, 0, 120, 100, 0, 0, 100, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 100, 0, 120, 0],  # missile
        [115, 125, 115, 0, 15, 40, 0, 0, 15, 50, 0, 0, 40, 75, 0, 35, 125, 55, 105, 125, 125, 0, 15, 0, 105],  # neo
        [85, 80, 80, 105, 55, 60, 120, 75, 60, 60, 65, 95, 60, 55, 90, 25, 90, 50, 80, 90, 85, 75, 85, 105, 80],  # pipe
        [4, 45, 45, 10, 0, 0, 0, 0, 0, 0, 0, 70, 0, 1, 65, 1, 28, 1, 6, 35, 55, 0, 0, 35, 6],  # recon
        [85, 80, 80, 0, 55, 60, 0, 0, 60, 85, 0, 95, 60, 55, 90, 25, 90, 50, 80, 90, 85, 0, 85, 0, 80],  # rocket
        [50, 85, 75, 85, 45, 65, 120, 70, 45, 35, 45, 90, 65, 70, 90, 15, 85, 60, 80, 85, 85, 55, 55, 95, 75],  # steal
        [0, 0, 0, 0, 55, 95, 0, 0, 75, 25, 0, 0, 95, 0, 0, 0, 0, 0, 0, 0, 0, 0, 55, 0, 0],  # sub
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],  # tcopter
        # line break
        [65, 75, 70, 0, 1, 10, 0, 0, 1, 5, 0, 0, 10, 15, 0, 10, 85, 15, 55, 85, 85, 0, 1, 0, 55],  # tank
        # AMMO
        [6, 20, 25, 65, 0, 0, 0, 0, 0, 0, 0, 75, 0, 1, 75, 1, 35, 1, 6, 30, 35, 0, 0, 95, 6],  # bcopter
        [0, 0, 0, 115, 0, 0, 120, 65, 0, 0, 55, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 100, 0, 115, 0],  # cruiser
        [7, 45, 45, 12, 0, 0, 0, 0, 0, 0, 0, 105, 0, 1, 95, 1, 35, 1, 8, 45, 45, 0, 0, 45, 8],  # med
        [6, 20, 32, 9, 0, 0, 0, 0, 0, 0, 0, 65, 0, 1, 55, 1, 35, 1, 6, 18, 35, 0, 0, 35, 6],  # mech
        [17, 65, 65, 22, 0, 0, 0, 0, 0, 0, 0, 135, 0, 1, 125, 1, 55, 1, 10, 65, 75, 0, 0, 55, 10],  # mega
        [17, 65, 65, 22, 0, 0, 0, 0, 0, 0, 0, 125, 0, 1, 115, 1, 55, 1, 10, 65, 75, 0, 0, 55, 10],  # neo
        [5, 54, 45, 10, 0, 0, 0, 0, 0, 0, 0, 75, 0, 1, 70, 1, 30, 1, 6, 40, 55, 0, 0, 40, 6]  # tank
    ]
    return table[types.index(type1 + ammo)][types.index(type2)]
