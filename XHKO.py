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
            dmg_list[i] = int(np.round(
                ((base * u1Av / 100) + gl - bl)  # attacker damage
                * (int(1 + u1hp / 10) / 10)  # attacker hp multiplier
                * (2 - (u2Dv + (u2Dtr * int(1 + u2health / 10))) / 100)  # defender defence
                + 0.05, 5  # rounding according to awbw formula
            ))
            if dmg_list[i] < 0:
                dmg_list[i] = 0
            i += 1
    return dmg_list


def reformat(var, length):
    if type(var) is int:
        return [var for _ in range(length)]
    return var[:length]


def calc():
    u2t, u2Dv, u2Dtr, u2hp, heals = defender()
    if u2t in ['bcopter', 'tcopter', 'fighter', 'bomber', 'stealth', 'bbomb']:
        u2Dtr = 0  # ignore erroneous defence stars
    attacks = attackers()
    gl, bl = luck()
    known_hp_dict = known_hp()
    u2Dv = reformat(u2Dv, len(attacks))
    u2Dtr = reformat(u2Dtr, len(attacks))
    gl = reformat(gl, len(attacks))
    bl = reformat(bl, len(attacks))
    print(f'defender: {int(1 + u2hp / 10)}hp'
          f' {[e + 100 for e in u2Dv] if u2Dv.count(u2Dv[0]) != len(u2Dv) else (u2Dv[0] + 100)} defence'
          f' {u2t}'
          f' on {u2Dtr if min(u2Dtr) != max(u2Dtr) else min(u2Dtr)}*')

    plot_hp = np.arange(100)  # 0-99 x axis for plot
    tally = np.zeros_like(plot_hp)  # corresponding tallys of how many cases are at each hp in that range
    tally[u2hp] = 1  # set initial hp (might not be 99 ig)
    dead = 0
    dead_old = 0
    ko_cum = 0
    repair = 0

    for i, a in enumerate(attacks):
        if i + 1 in heals:
            if not heals[i + 1][-1].isdigit():
                heals[i + 1] = heals[i + 1] + '1'  # append a 1 so the for loop doesn't get confused
            for _ in range(int(heals[i + 1][-1])):  # only the last digit matters bcus 9 heals with bboat is 1 to 10 hp.
                match heals[i + 1][:-1]:  # ignore last character bcus it is a number
                    case 'bboat':
                        print('healing (bboat) + 1hp')
                        repair += 10
                    case 'property':
                        print('healing (property) +2hp')
                        repair += 20
                    case _:
                        raise ValueError('invalid heal type given?')
        else:
            repair = 0

        print(f'attacker {i + 1}: {int(1 + a[2] / 10)}hp {a[1] + 100} attack {a[0]}')

        if repair > 0:
            if repair > 99:  # edge cases when too much healing is inputted
                repair = 99
            tally_old = np.zeros_like(plot_hp)
            for hp in range(100):
                if hp + repair >= 99:  # cap at 99
                    #todo 2025/05/02 change repair to always do XX to YX where Y = X + 1. 10hp *no* special treatement
                    tally_old[99] += tally[hp]
                else:
                    tally_old[hp + repair] += tally[hp]
            repair = 0
        else:
            tally_old = tally
        tally = np.zeros_like(tally_old)  # reset before calcs

        base = base_damage(a[0], u2t, '')  # base damage lookup
        if base == 0:
            base = base_damage(a[0], u2t, 'AMMO')  # secondary base damage lookup
            if base == 0:
                raise Exception(f"{a[0]} can't do damage to {u2t}")

        for j in range(10):  # generate damage spread for all 10 visible defender health
            # hp =  j * 10 + 5 # 5, 15, ... 95 with 10 total
            if np.sum(tally_old[(j * 10):((j * 10) + 10)]) == 0:  # if the 10 tallys in this visible hp add to 0
                continue  # saves some time.
            dmg_list = all_damage(base, a[1] + 100, a[2], u2Dv[i] + 100, u2Dtr[i], j * 10 + 9, gl[i], bl[i])
            # plt.plot(np.unique(dmg_list, return_counts=True)[0], np.unique(dmg_list, return_counts=True)[1])
            # plt.show()
            for k in range(10):  # apply damage to every defender hp
                hp_old = (j * 10) + k
                if tally_old[hp_old] == 0:  # if this tally doesn't have any cases
                    continue  # saves some more time.
                for dmg in dmg_list:
                    hp = hp_old - int(dmg)
                    if hp >= 0:
                        tally[hp] += tally_old[hp_old]
                    else:
                        dead += tally_old[hp_old]

        if i + 1 in known_hp_dict:
            set_hp = known_hp_dict[i + 1]
            removed = 0
            for j in range(10):
                visible_hp_sum = np.sum(tally[(j * 10):((j * 10) + 10)])
                if set_hp == j + 1:
                    if visible_hp_sum == 0:
                        print(f'known hp after attack {i + 1} of {set_hp}hp is not possible.')
                        quit()
                else:
                    removed += visible_hp_sum
                    tally[(j * 10):((j * 10) + 10)] = 0

            if removed > 0:
                print(f'known hp after attack {i + 1}: {set_hp}hp so culling '
                      f'{100 * removed / (removed + np.sum(tally)):.3g}%')
            if dead != 0:
                print('resetting cumulative KO to 0')
                dead = 0
                dead_old = 0

        dead_this = dead - dead_old
        dead_old = dead
        ko = dead_this / (dead_this + np.sum(tally))
        ko_cum = ko_cum + (1 - ko_cum) * ko

        # all done for this attacker! message and plot to follow, then next attacker
        if np.sum(tally) == 0:
            print(f'garantees {i + 1}HKO')
            if i == 0:
                quit()  # don't wanna plot if 1 attacker garantees 1HKO
            break
        if dead > 0:
            print(f'max possible health after attack: {np.amax(plot_hp[np.argwhere(tally > 0)]):.2g}')
            print(f'KO: {100 * ko:.10g}%')
            if dead_this != dead:
                print(f'cumulative {i + 1}HKO: {100 * ko_cum:.10g}%')
            # print(f'number of alive cases: {np.sum(tally):.4e}')  # kinda useless info for wide luck values
        else:
            print(f'min possible health after attack: {np.amin(plot_hp[np.argwhere(tally > 0)]):.2g}')
        plt.plot(plot_hp[np.nonzero(tally)], 100 * tally[np.nonzero(tally)] / np.sum(tally), '.',
                 label=f'{i + 1}: {int(1 + a[2] / 10)}hp {a[1]} {a[0]}')

    plt.xlabel('hp (-1 = dead)')
    plt.ylabel('% of results')
    plt.xlim(left=0, right=99)
    plt.xticks(np.arange(0, 99 + 1, 10))
    plt.ylim(bottom=0)
    # plt.ylim(top=30)
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
    # u2Dv = [10, 10, 20, 20]
    u2Dtr = 3
    # u2Dtr = [3, 4, 0, 1, 1]
    u2hp = int(99)  # 99 is full, 0 is alive, -1 is dead. This way hp = the 10s didget + 1, no confusion.
    heals = {-3: 'bboat', -2: 'property1'}  # heals *before* attacker number x. multiple e.g. bboat2 to 9
    return u2t, u2Dv, u2Dtr, u2hp, heals  # u2t = str, u2hp = int(0-99), u2Dv & u2Dtr = int OR list of int, heals = dict


def luck():
    # good_luck=10, bad_luck=0  # default 0 to 9
    # good_luck=10, bad_luck=10  # sonja default -9 to +9
    # good_luck=25, bad_luck=10  # flak default -9 to +24
    # good_luck=30, bad_luck=15  # jugger default -14 to +29
    # good_luck = [10, 40, 40, 40]  # rachel activates COP after first attack so gd luck goes from 9 to 39
    good_luck = 10
    bad_luck = 0
    return good_luck, bad_luck


def known_hp():
    # hp is known *after* attack n. for example {1: 5} means after attacker 1, hp was set to 5
    # this removes all results that don't align to this hp and resets the cumulative KO to only count attack 2 onward
    return {-1: 6, -2: 5, -3: 1}


def attackers():  # don't do more than ~16 attacks with normal luck if most stay alive. numbers get big.
    return [
        ['tank', 10, 99],
        ['inf', 10, 69],
        # ['bcopter', 10, 99],
        # ['tank', 30, 99],
        # ['inf', 30, 99],
        # ['med', 30, 99],
        # ['inf', 20, 99],
        # ['tank', 20, 99],
        # ['inf', 20, 99],
        # ['inf', 10, 49],
        # ['inf', 0, 99],
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

    # wallbreak that could have been done to me but my opponent resigned instead.
    # defender is my vb inf on city, heal 2 between recon and first inf attack.
    # https://awbw.amarriner.com/game.php?games_id=1381781&ndx=16
    # SCRATCH THAT im braindeath. the 2hp couldn't reach so it was unbreakable but needed calc to prove it
    # (best case scenario for a LL wall :D waste time AND be inpenetrable or bait them in with it looking breakable-ish)
    # ['recon', 10, 99],
    # ['inf', 10, 39],
    # ['inf', 10, 19],
    # ['tank', 10, 69],
