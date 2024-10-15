
def co_maker(name):
    name = 'jake'
    co = {
        'name': name, 'army': 'neutral', 'comm': 0, 'properties': 0, 'funds': 0, 'power': 0, 'units': []
    }  # power: 0=CO, 1=COP, 2=SCOP
    # todo sort out CO things. there's a lot to do herererererere.
    # L defaults to [0, 9] but sonja gets like [-9, 9]
    # Av starts at 0. comm tower or CO power etc brings it to 10.
    # Dv starts at 100. grimm 80, sturm 120 etc
    return co


def activate_power(co, level):
    # copy unit details to a safe place
    # set co stats
    # delete all units
    # remake all units
    co['power'] = level

    if co['name'] == 'javier':
        co['comm'] = co['comm'] * (1 + level)


def deactivate_power(co):
    # copy unit details to a safe place
    # set co stats
    # delete all units
    # remake all units
    x = 1


def unit_stats_maker(unit, name, comm, power, funds, properties):
    # co_list = [
    #     'andy', 'hachi', 'jake', 'max', 'nell', 'rachel', 'sami',
    #     'colin', 'grit', 'olaf', 'sasha',
    #     'drake', 'eagle', 'javier', 'jess',
    #     'grimm', 'kanbei', 'sensei',  'sonja',
    #     'adder', 'flak', 'hawke',  'jugger', 'kindle', 'koal', 'lash',  'sturm', 'von bolt'
    # ]
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
    foot = (unit['type'] == 'inf' or unit['type'] == 'mech')
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
            else:
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
