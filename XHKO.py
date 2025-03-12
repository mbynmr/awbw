import numpy as np
import matplotlib.pyplot as plt
# from tqdm import tqdm

from fire import base_damage


def all_damage(base, u1Av, u1hp, u2Dv, u2Dtr, u2health, good_luck, bad_luck):
    good_luck = range(good_luck)
    bad_luck = range(bad_luck if bad_luck > 1 else 1)
    dmg_list = np.zeros([len(good_luck) * len(bad_luck)])
    i = 0
    for gl in good_luck:
        for bl in bad_luck:
            # # damage = base * u1Av / 100 + np.random.choice(u1['L'][1] + u1['L'][0]) - u1['L'][0]  # attack value
            # damage = (base * u1Av / 100) + gl - bl  # attack value
            # h = int(1 + u1hp / 10) / 10  # hp 'out of 10' divided by 10: full unit is 1x damage, half hp is 0.5x
            # defence = 2 - (u2Dv + (u2Dtr * int(1 + u2hp / 10))) / 100  # defence multiplier
            #
            # # is rounded up to the nearest interval of 0.05 then rounded down to the nearest integer
            # out = int(np.round(damage * h * defence + 0.05, 5))  # (float precision needs a round before the int())
            dmg_list[i] = int(np.round(((base * u1Av / 100) + gl - bl) * (int(1 + u1hp / 10) / 10) *
                                       (2 - (u2Dv + (u2Dtr * int(1 + u2health / 10))) / 100) + 0.05, 5))
            i += 1
    return dmg_list


def calc():
    u2t, u2Dv, u2Dtr, u2hp, heals = defender()
    attacks = attackers()
    gl, bl = luck()
    if type(u2Dv) is int:
        u2Dv = [u2Dv for _ in attacks]
    if type(u2Dtr) == int:
        u2Dtr = [u2Dtr for _ in attacks]
    if type(gl) is int:
        gl = [gl for _ in attacks]
    if type(bl) is int:
        bl = [bl for _ in attacks]
    hp_list = np.array([u2hp])
    print(f'defender: {int(1 + u2hp / 10)}hp'
          f' {[e + 100 for e in u2Dv] if u2Dv.count(u2Dv[0]) != len(u2Dv) else (u2Dv[0] + 100)} defence'
          f' {u2t}'
          f' on {u2Dtr if min(u2Dtr) != max(u2Dtr) else min(u2Dtr)}*')

    cum_ko = 0
    for i, a in enumerate(attacks):
        if i + 1 in heals:
            match heals[i + 1]:
                case 'bboat':
                    print('healing (bboat) + 1hp')
                    repair = 10
                case 'property':
                    print('healing (property) +2hp')
                    repair = 20
                case _:
                    raise ValueError('invalid heal type given?')
        else:
            repair = 0

        if repair > 0:
            old_hp_list = np.where(hp_list + repair >= 90, 99, hp_list + repair)  # in case silly me is silly
        else:
            old_hp_list = hp_list
        hp_list = None

        base = base_damage(a[0], u2t, '')  # base damage lookup
        if base == 0:
            base = base_damage(a[0], u2t, 'AMMO')  # secondary base damage lookup
            if base == 0:
                raise Exception(f"{a[0]} can't do damage to {u2t}")

        dmg_list = [[] for _ in range(10)]
        for j in range(10):  # generate damage spread for all 10 visible defender health
            # hp =  j * 10 + 5 # 5, 15, ... 95 with 10 total
            dmg_list[j] = all_damage(base, a[1] + 100, a[2], u2Dv[i] + 100, u2Dtr[i], j * 10 + 9, gl[i], bl[i])

        # todo optimisation required. multiple hps that are the same can be skipped calcing but still added? idk.
        # i silly

        for hp in old_hp_list:  # apply damage to every defender hp
            # if i == 1 and hp < 30:
            #     continue  # todo this is one place where known hp could change the result :>
            if hp_list is None:
                hp_list = hp - dmg_list[int(1 + hp / 10) - 1]
            else:
                hp_list = np.concatenate([hp_list, hp - dmg_list[int(1 + hp / 10) - 1]])

        # if i == 1:  # todo this is the other place where known hp could change the result :>
        #     known_index = np.argwhere(hp_list < 20)
        #     hp_list = np.delete(hp_list, known_index)

        ko_index = np.argwhere(hp_list < 0)
        # hp_list[ko_index] = -1  # optional, changes how the plot looks. imo bad
        values, counts = np.unique(hp_list, return_counts=True)

        hp_list = np.delete(hp_list, ko_index)
        # if i == 0:
        #     hp_list = np.delete(hp_list, np.argwhere(hp_list > 9))  # todo WIP planning after hp is revealed

        ko = len(ko_index) / (len(hp_list) + len(ko_index))
        cum_ko = cum_ko + (1 - cum_ko) * ko

        print(f'attacker {i + 1}: {int(1 + a[2] / 10)}hp {a[1] + 100} attack {a[0]}')

        # all done for this attacker! message and plot to follow, then next attacker
        if ko == 1:
            print(f'garantees {i + 1}HKO')
            if i == 0:
                quit()  # don't wanna plot if 1 attacker garantees 1HKO
            break
        if cum_ko > 0:
            print(f'max possible health after attack: {np.amax(hp_list):.2g}')
            print(f'KO: {ko * 100:.10g}%')
            if ko != cum_ko:
                print(f'cumulative {i + 1}HKO: {cum_ko * 100:.10g}%')
            print(f'number of alive cases: {len(hp_list)}')
        else:
            print(f'min possible health after attack: {np.amin(hp_list):.2g}')
        plt.plot(values, 100 * counts / np.sum(counts), '.',
                 label=f'{i + 1}: {int(1 + a[2] / 10)}hp {a[1]} {a[0]}')

    plt.xlabel('hp (-1 = dead)')
    plt.ylabel('% of results')
    plt.xlim(left=0)
    plt.ylim(bottom=0)
    plt.legend()
    plt.title(f'{[e + 100 for e in u2Dv] if u2Dv.count(u2Dv[0]) != len(u2Dv) else (u2Dv[0] + 100)} def'
              f' {u2t}'
              f' on {u2Dtr if min(u2Dtr) != max(u2Dtr) else min(u2Dtr)}*')
    plt.show()


def defender():
    # u2Dv = 0 # -20=grimm, +10=COP
    # u2Dtr = [3, 0, 0, 0]  # city for attacker 1, roads for future attackers
    # heals = {1: 'bboat', 2: 'property'}  # repair by bboat before attacker 1, sits on owned property before attacker 2
    u2t = 'inf'
    u2Dv = 0
    # u2Dv = [10, 10, 0, 0]
    u2Dtr = 3
    # u2Dtr = [2, 1, 1, 1]
    u2hp = 99  # 99 is full, 0 is alive, -1 is dead. This way hp = the 10s didget + 1, no confusion.
    heals = {-3: 'bboat', -2: 'property'}  # heals *before* attacker number x
    return u2t, u2Dv, u2Dtr, u2hp, heals  # u2t = str, u2hp = int(0-99), u2Dv & u2Dtr = int OR list of int, heals = dict


def luck():
    # good_luck=10, bad_luck=0  # default 0 to 9
    # good_luck=10, bad_luck=10  # sonja default -9 to +9
    # good_luck=25, bad_luck=10  # flak default -9 to +24
    # good_luck=30, bad_luck=15  # jugger default -14 to +29
    # good_luck = [10, 40, 40, 40]  # rachel activates COP after first attack to go from 0-9 to 0-39
    good_luck = 25
    bad_luck = 10
    return good_luck, bad_luck


def attackers():  # don't do more than 7ish please. :>
    return [
        ['inf', 20, 99],
        ['inf', 20, 99],
        ['inf', 20, 99],
        ['mega', 80, 99],
        # ['tank', 100, 29],
        # ['inf', 100, 99],
    ]
    # ['tank', 10, 99],  # full hp andy tank with 1 tower
    # ['aa', 10, 99],
    # ['inf', 20, 45],  # 2 towers 5hp
    # ['inf', 20, 40],  # 5hp

    # imfamous minty game (target is my andy tank on road which I wanted to die for wallbreak. It healed to 6hp)
    # ['inf', 10, 40],
    # ['tank', 10, 99],
    # ['tank', 20, 70],

    # interesting profile attacking andy tank on road - alive cases go 10, 100, 28, (+2heal), 280, 2170, 3734, 924, 8, 0
    # ['tank', 60, 99],
    # ['inf', 0, 99],
    # ['inf', 0, 99],
    # ['inf', 0, 99],
    # ['inf', 0, 99],
    # ['inf', 0, 99],
    # ['inf', 0, 99],
    # ['inf', 0, 99],
