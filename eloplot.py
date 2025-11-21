import time

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy.ndimage import gaussian_filter
from bs4 import BeautifulSoup
import requests
import os.path
import datetime as dt
from tqdm import tqdm
import time
from selenium import webdriver
import pandas as pd
import itertools as iter

from fitting import fit
from AIsortinglol import sort_games_by_actual_order

"""
run plotter() and freely change variables
"""


def plotter():

    # what do u wanna plot?
    plot_option = 'elo'  # elo on game number
    # plot_option = 'date,elo'  # elo on date
    plot_oppelo = 1  # 0/False, 1/True
    plot_fit = 0  # 0 for False, 1+ for polynomial fit order
    # plot_option = 'co_pick,winrate'  # winrate on co picked
    # plot_option = 'co_against,winrate'  # winrate on co against
    # plot_option = 'co_mirror,winrate'  # winrate on co (mirror)
    # plot_option = 'tier,winrate'  # winrate on tier
    # plot_option = 'days,winrate'  # winrate on days of game
    plot_option = 'elo,donated'  # winrate on days of game
    # plot_option = 'date,days'  # days of game on date  # todo
    # plot_option = 'days'  # days of game on game number  # todo
    # plot_option = 'map,co'  # map!!  # todo
    # plot_option = 'map,p1/p2 on date'  # map!!  # todo
    # plot_option = 'map,days'  # map!!  # todo
    gauss_filter = False  # 0/False, 1/True

    # for winrate plots, discards ALL games that don't have BOTH players ending >= this elo
    min_elo = None
    # min_elo = 700
    # min_elo = 1100

    league = ''  # all games
    # league = 'live+queue'
    league = 'live+league'
    league = 'global+league'

    rules = ['']  # all
    rules = ['std']  # ['std', 'hf', 'fog']
    names = ['ncghost12']
    # ['WealthyTuna', 'new1234', 'hunch', 'Po1and', 'Po2and', 'BongoBanjo']
    # ['Grimm Guy', 'Grimm Girl', 'J.Yossarian']
    # ['High Funds High Fun', 'Po1and', 'Po2and', 'new1234', 'WealthyTuna', 'Spidy400']
    # ['ncghost12', 'new1234', 'Heuristic']
    # ['Voice of Akasha', 'Grimm Guy', 'tesla246']
    # ['new1234', 'fluhfie', 'Spidy400']
    # ['Deejus_', 'GetGood', 'AdvanceNoob', 'hapahauli', 'fluhfie']

    plot_elo(plot_option, league, rules, names, min_elo, plot_oppelo, plot_fit, gauss_filter)


def plotter_standings():
    # what do u wanna plot?
    plot_option = 'elo'  # y-axis account count, x-axis elo
    plot_option = 'gamecount,elo'  # y-axis game count, x-axis elo
    plot_option = 'gamecount,elo,heatmap'  # y-axis game count, x-axis elo
    # plot_option = 'gamewins,elo'  # y-axis wins, x-axis elo
    # plot_option = 'gamelosses,elo'  # y-axis losses, x-axis elo
    plot_option = 'win%,elo'  # y-axis win%, x-axis elo
    # plot_option = 'win%,elo,heatmap'  # y-axis win%, x-axis elo
    league = 'live+league'
    league = 'global+league'
    # league = 'global+league+all+time'

    read_from_pickle = 'global+league 1759486072.0850606.pkl'
    read_from_pickle = ''

    min_games = 5  # todo
    # min_games = 1

    rules = ['std']  # ['std', 'fog', 'hf']

    fig, ax = plt.subplots(1)
    fig.autofmt_xdate()  # format the x-axis for squeezing in longer tick labels

    match league:
        case 'live+league':
            s = f'https://awbw.amarriner.com/live_league_standings.php'
            # s = f'https://awbw.amarriner.com/live_league_standings.php?mode=std&sort=elo'
        case 'global+league':
            s = f'https://awbw.amarriner.com/newleague_standings.php?time=curr'
            # s = f'https://awbw.amarriner.com/newleague_standings.php?time=curr&sort=std'
        case 'global+league+all+time':
            s = f'https://awbw.amarriner.com/newleague_standings.php?time=all'
            # s = f'https://awbw.amarriner.com/newleague_standings.php?time=all&sort=std'
        case _:
            raise Exception(f'"{league}" was not a match for any actual league')

    if read_from_pickle == '':
        df = write_to_pickle(s, league)
    else:
        df = pd.read_pickle(f'outputs/data/{read_from_pickle}')

    for ruleset in rules:
        sorted_df = df.sort_values(by=[ruleset])
        # (data={'name': name, 'w': w, 'l': l, 'd': d, 'std': std, 'fog': fog, 'hf': hf})

        excluded_mins = np.where((sorted_df.get('w') + sorted_df.get('l') + sorted_df.get('d')) >= min_games,
                                 sorted_df.get(ruleset), np.nan)
        if league != 'live+league':  # GL
            excluded_mins = np.where(excluded_mins == 800, np.nan, excluded_mins)
        else:  # LL
            pass

    match plot_option:
        case 'elo':
            ax.hist(excluded_mins, bins=int(np.ceil(np.nanmax(excluded_mins) - 700) / 20), label=ruleset)
            ax_percent = ax.twinx()
            ax_percent.plot(excluded_mins, 100 * np.nancumsum(excluded_mins) / np.nansum(excluded_mins), label=ruleset)
            ax.set_ylabel('density/count')
        case 'gamecount,elo,heatmap':
            heatmap, xedges, yedges = np.histogram2d(
                excluded_mins, sorted_df.get('w') + sorted_df.get('l') + sorted_df.get('d'), bins=30)
            extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]

            heatmap = np.log(heatmap)
            plt.clf()
            plt.imshow(heatmap.T, extent=extent, origin='lower')
            plt.show()
            quit()  # todo
        case 'gamecount,elo':
            ax.plot(excluded_mins, sorted_df.get('w') + sorted_df.get('l') + sorted_df.get('d'), '.', label=ruleset)
            theory = calc_theory()
            ax.plot(theory, np.arange(len(theory)), 'k.')
            # ax.set_yscale('log')
            ax.set_ylabel('game count')
        case 'gamewins,elo':
            ax.plot(excluded_mins, sorted_df.get('w'), '.', label=ruleset)
            theory = calc_theory()
            ax.plot(theory, np.arange(len(theory)), 'k.')
            ax.set_yscale('log')
            ax.set_ylabel('wins')
        case 'gamelosses,elo':
            ax.plot(excluded_mins, sorted_df.get('l'), '.', label=ruleset)
            # ax.set_yscale('log')
            ax.set_ylabel('losses')
        case 'win%,elo':
            ax.plot(
                excluded_mins, 100 * sorted_df.get('w') / (sorted_df.get('w') + sorted_df.get('l')), '.', label=ruleset)
            # ax.hist(excluded_mins, bins=int(np.ceil(np.nanmax(excluded_mins) - 700) / 20), label=ruleset)
            ax.plot(excluded_mins, 100 * np.nancumsum(excluded_mins) / np.nansum(excluded_mins))
            ax.set_ylabel('win%')
        case 'win%,elo,heatmap':
            heatmap, xedges, yedges = np.histogram2d(
                excluded_mins, 100 * sorted_df.get('w') / (sorted_df.get('w') + sorted_df.get('l')), bins=30,
                range=[[np.nanmin(excluded_mins), np.nanmax(excluded_mins)], [0, 100]])
            extent = [xedges[0], xedges[-1], yedges[0], yedges[-1]]
            # heatmap = np.log(heatmap)
            plt.clf()
            plt.imshow(heatmap.T, extent=extent, origin='lower')
            plt.show()
            plt.imsave(f'outputs/pics/{league}.png', heatmap.T)
            quit()  # todo

    ax.set_xlabel('elo')
    plt.xticks(np.linspace(start=700, stop=1600, num=10))
    # ax.set_ylim([0, 200])
    plt.legend()
    plt.tight_layout()
    plt.show()


def calc_theory():
    elo = [np.round(800, decimals=2)]
    i = 0
    k = 50
    while elo[-1] < 1600:
        if i == 30:
            k = 30
        elo.append(elo[-1] + np.round(k * (1 - (1 / (1 + 10 ** abs(300 / 400)))), decimals=2))
    return np.asarray(elo[:-1])


def write_to_pickle(s, league):
    placement = []
    name = []
    w = []
    l = []
    d = []
    std = []
    fog = []
    hf = []
    for i, row in enumerate(page_getter_slow(s).find("table").find_all('tr')):
        if i < 4:  # header rows, don't care.
            continue
        items = row.find_all('td')
        if len(items) < 5:  # if i == 104:
            continue
        if league != 'live+league':  # if not live league
            placement.append(int(str(items[0].next)[:-1]))
            name.append(str(items[1].next.next))
            # "rating" overall GL oof
            w.append(int(items[3].next))
            l.append(int(items[4].next))
            d.append(int(items[5].next))
            if items[6].next == ' - ':
                std.append(np.nan)
            else:
                std.append(float(items[6].next))
            if items[7].next == ' - ':
                fog.append(np.nan)
            else:
                fog.append(float(items[7].next))
            if items[8].next == ' - ':
                hf.append(np.nan)
            else:
                hf.append(float(items[8].next))
        else:  # if live league
            placement.append(int(str(items[0].next)[:-2]))
            name.append(str(items[1].next.next)[1:-1])
            w.append(int(items[2].next.next))
            l.append(int(items[3].next.next))
            d.append(int(items[4].next.next))
            if items[5].next.next == ' - ':
                std.append(np.nan)
            else:
                std.append(float(items[5].next.next))
            if items[6].next.next == ' - ':
                fog.append(np.nan)
            else:
                fog.append(float(items[6].next.next))
            if items[7].next.next == ' - ':
                hf.append(np.nan)
            else:
                hf.append(float(items[7].next.next))
    df = pd.DataFrame(data={'name': name, 'w': w, 'l': l, 'd': d,
                            'std': std, 'fog': fog, 'hf': hf})
    df.to_pickle(f'outputs/data/{league} {time.time()}.pkl')  # where to save it, usually as a .pkl
    # df = pd.read_pickle(f'outputs/data/{league} {time.time()}.pkl')
    return df


def plotter_topn(top=5):
    df = pd.read_pickle('live+league 1759138006.0349133.pkl')
    # (data={'name': name, 'w': w, 'l': l, 'd': d, 'std': std, 'fog': fog, 'hf': hf})
    rules = ['std']  # ['std', 'fog', 'hf']

    for ruleset in rules:
        df.sort_values(by=[ruleset])
        dfr = df[:top]  # todo topn like top5? top10?
        namelist = dfr.get('name')
        with open(f'outputs/top{int(top)}.txt') as bigtopfile:
            for name in namelist:
                s = f'live+league+{rules}+"{name}"'

                # grab info
                if not os.path.isfile('outputs/' + s.replace('"', '') + '.txt'):  # does the local file already exist?
                    print(f'scraping for {s}')
                    scrape(s)  # scrapes the mooo site for the search, saves to file
                    time.sleep(1)

                # extracts stuff from file
                # print('plotting ' + s.replace('"', ''))
                elo, date, oppelo, days, result, co_pick, co_against, tier = extract_elo()
                fileee = np.loadtxt('outputs/' + s.replace('"', '') + '.txt', delimiter=';', dtype=str)
                for line in fileee:
                    if line[6] in namelist:
                        if line[9] in namelist:
                            bigtopfile.write(line)
                    # 1477950; 2025-07-26; Tokyo Rush Hour; T4; 21; P2; fluhfie; 1255; jess; Po1and; 1422; adder


def plot_elo(plot_option, league, rulesiter, nameiter, min_elo, plot_oppelo, plot_fit, gauss_filter):

    # figure stuff
    fig, ax = plt.subplots(1)
    if plot_option in ['date,elo', 'co_pick,winrate', 'co_against,winrate', 'co_mirror,winrate', 'date,days']:
        fig.autofmt_xdate()  # format the x-axis for squeezing in longer tick labels

    for rules in rulesiter:
        for name in nameiter:
            # search/save string
            s = f'{league}+{rules}+"{name}"'

            # plot label
            label = ('' if len(rulesiter) == 1 else (rules + ' ')) + ('' if len(nameiter) == 1 else name)

            # grab info
            if not os.path.isfile('outputs/' + s.replace('"', '') + '.txt'):  # does the local file already exist?
                print(f'scraping for {s}')
                scrape(s)  # scrapes the mooo site for the search, saves to file
                time.sleep(1)

            # extracts stuff from file
            # print('plotting ' + s.replace('"', ''))

            plot_options(ax, plot_option, label, rules, plot_oppelo, plot_fit, min_elo, gauss_filter,
                         *extract_elo(s.replace('"', '')))

    # plt.ylim([40, 100])
    plt.legend()
    # plt.legend(loc='lower center')
    plt.tight_layout()
    plt.grid()
    plt.show()


def plot_options(ax, plot_option, label, rules, plot_oppelo, plot_fit, min_elo, gauss_filter,
                 elo, date, oppelo, days, result, co_pick, co_against, tier, oppname):
    elo, date, oppelo, days, result, co_pick, co_against, tier = redo_sort(
        elo, date, oppelo, days, result, co_pick, co_against, tier)

    # "calibrated" elo delta in case it is needed
    delta = elo[::-1] - np.array([800, *elo[:0:-1]])
    if len(delta) > 30:
        delta[:31] = delta[:31] * 3 / 5
    else:
        delta = delta * 3 / 5

    # plot :>
    match plot_option:
        case 'elo':
            ax.plot([800, *elo[::-1]], '-', label=label)
            if plot_oppelo:
                s = np.insert((1 / 43) * delta ** 2, 0, 1)
                ax.scatter(range(len(oppelo) + 1),
                           np.insert(np.where(result == 1, oppelo, np.nan)[::-1], 0, np.nan), color='g', s=s)
                ax.scatter(range(len(oppelo) + 1),
                           np.insert(np.where(result == -1, oppelo, np.nan)[::-1], 0, np.nan), color='r', s=s)
                ax.scatter(range(len(oppelo) + 1),
                           np.insert(np.where(result == 0, oppelo, np.nan)[::-1], 0, np.nan), color='b',
                           s=np.insert(np.abs((elo - oppelo))[::-1] / 10, 0, 1))
            if plot_fit != 0:
                x = range(len([800, *elo[::-1]]))
                y, v = fit(x, [800, *elo[::-1]], int(plot_fit))
                print([f'{e:.3g}' for e in v])
                ax.plot(x, y, 'k--', alpha=0.5)
            # ax.set_ylim(bottom=700)
            plt.xlabel('game number')
            plt.ylabel('elo')
        case 'date,elo':
            datex = [dt.datetime.strptime(d, '%Y-%m-%d').date() for d in date]
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax.plot(datex, elo, '-', label=label)
            ax.plot(datex[-1], 800, 'ko')
            if plot_oppelo:
                s = np.array((1 / 43) * delta ** 2)
                # ax.scatter(datex, oppelo, label='opp ' + label, s=s[::-1])
                ax.scatter(datex,
                           np.where(result == 1, oppelo, np.nan), color='g', s=s)
                ax.scatter(datex,
                           np.where(result == -1, oppelo, np.nan), color='r', s=s)
                ax.scatter(datex,
                           np.where(result == 0, oppelo, np.nan), color='b',
                           s=np.abs((elo - oppelo)) / 10)
            ax.set_ylim(bottom=700)
            plt.xlabel('date')
            plt.ylabel('elo')
        case 'co_pick,winrate':
            categories = co_list_maker(rules)
            entries = co_pick
            plt.xlabel('CO pick')
        case 'co_against,winrate':
            categories = co_list_maker(rules)
            entries = co_against
            plt.xlabel('opponent CO')
        case 'co_mirror,winrate':
            categories = co_list_maker(rules)
            entries = co_pick
            plt.xlabel('CO mirror')
        case 'tier,winrate':
            categories = ['4', '3', '2', '1', '0', '?']  # tiers
            entries = tier
            plt.xlabel('tier')
        case 'days,winrate':
            categories = range(int(np.amax(days) + 1))
            entries = days
            plt.xlabel('days at game end')
        case 'days':
            s = (10 / 43) * delta ** 2
            ax.scatter(range(len(days)), np.where(result == 1, days, np.nan)[::-1], color='g', s=s)
            ax.scatter(range(len(days)), np.where(result == -1, days, np.nan)[::-1], color='r', s=s)
            ax.scatter(range(len(days)), np.where(result == 0, days, np.nan)[::-1], color='b',
                       s=(elo - oppelo)[::-1] ** 2 / 500)
        case 'elo,donated':
            # open a game, is it a new player?
            # if new, add to list, add elo
            # if existing, add elo
            # save to txt.
            elodic = {}
            elo = elo[::-1]
            for i, opponent in enumerate(oppname[::-1]):
                # print(elodic)
                if i == 0:
                    elodic.update({opponent: int(elo[i] - 800)})
                    continue
                if opponent in elodic:
                    elodic[opponent] = elodic[opponent] + int(elo[i] - elo[i - 1])
                else:
                    elodic.update({opponent: int(elo[i] - elo[i - 1])})
            # np.savetxt('outputs/donos.txt', elodic)

            elodic = dict(sorted(elodic.items(), key=lambda item: item[1]))
            with open('outputs/donos.txt', 'w') as file:
                for k, v in elodic.items():
                   file.write(str(v) + ':\t' + str(k) + '\n')
        case 'date,days':
            datex = [dt.datetime.strptime(d, '%Y-%m-%d').date() for d in date[::-1]]
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            wind = np.ones(len(days)) * np.nan
            losed = np.ones(len(days)) * np.nan
            drawd = np.ones(len(days)) * np.nan
            for i, d in enumerate(days[::-1]):
                if result[i] == 1:
                    wind[i] = d
                elif result[i] == -1:
                    losed[i] = d
                else:
                    drawd[i] = d
            resultingelochange = elo[::-1] - np.asarray([800, *elo[:0:-1]])
            if len(resultingelochange) > 30:
                # todo check fencepost problem around elo number 30.
                resultingelochange[:31] = resultingelochange[:31] * 30 / 50  # first 30 games are wacky elo
            else:
                resultingelochange = resultingelochange * 30 / 50
            # resultingelochange = resultingelochange + 42.5  # 42.45102214 maximum elo change with +/-300 elo
            # if np.any(resultingelochange < 0):  # edge case where +/-300 was exceeded. global league ig?
            #     resultingelochange = resultingelochange + np.amin(resultingelochange)
            ax.scatter(datex, wind, 'g', alpha=0.5, s=100 * resultingelochange)
            ax.scatter(datex, losed, 'r', alpha=0.5, s=-100 * resultingelochange)
            ax.scatter(datex, drawd, 'k', alpha=0.5, s=10 * np.abs(elo - oppelo))

    # plot winrate plots (teeni bit of calcs to do)
    if plot_option.split(',')[-1] == 'winrate':  # figure out winrate in % for categories
        plt.ylabel('win%')
        winc = np.zeros(len(categories))
        losec = np.zeros(len(categories))
        wins = np.ones(len(entries)) * 0
        loses = np.ones(len(entries)) * 0
        for i, e in enumerate(entries):
            if min_elo is not None:
                if oppelo[i] < min_elo or elo[i] < min_elo:  # if either player is below the minimum elo required
                    # if oppelo[i] < min_elo:  # if opponent is below the minimum elo required
                    continue  # skip this game
            if plot_option == 'co_mirror,winrate' and co_pick[i] != co_against[i]:
                continue  # we only want mirrors and this entry is not
            if result[i] == 1:
                # wins[i] = e
                winc[categories.index(e)] += 1
            elif result[i] == -1:
                # loses[i] = e
                losec[categories.index(e)] += 1
            else:
                # game was drawn case, wanna plot it?
                pass

        elodiffslinear = (300 - np.abs(oppelo - elo)) / 300
        elodiffslinear = np.where(elodiffslinear > 0, elodiffslinear, 0)  # remove all bigger than 300 range
        try:
            winweight = np.average(wins, weights=np.where(wins != 0, elodiffslinear, 0))
        except ZeroDivisionError:
            winweight = np.nan
        try:
            loseweight = np.average(loses, weights=np.where(loses != 0, elodiffslinear, 0))
        except ZeroDivisionError:
            loseweight = np.nan

        winsum = 0
        for i, e in enumerate(winc):
            winsum += i * e
        losesum = 0
        for i, e in enumerate(losec):
            losesum += i * e
        print(
            f'{label}: {winsum / sum(winc):.1f} {losesum / sum(losec):.1f} & weight: {winweight:.1f} {loseweight:.1f}')
        print(f'{np.array(winc) + np.array(losec)}')  # sum

        if plot_option == 'days,winrate':
            plt.xlim([0, int(np.amax(days))])
            if gauss_filter and plot_option == 'days,winrate':  # blur
                sigma = 0.5
                winc = gaussian_filter(winc, sigma=sigma, mode='nearest')
                losec = gaussian_filter(losec, sigma=sigma, mode='nearest')
            # else:  # plot line
            #     ax.plot(categories, (winc / (winc + losec)) * 100, '-')

        # winc = np.where(winc + losec < 5, 0, winc)
        # losec = np.where(winc + losec < 5, 0, losec)
        ax.scatter(categories, (winc / (winc + losec)) * 100,
                   s=10 * 100 * (winc + losec) / np.sum(winc + losec),
                   label=label + ', ' + str(int(np.sum(winc + losec))))
        ax.scatter(x=categories, y=50 * np.ones(len(categories)), marker='.', c='k')
        with open(f'outputs/test for {label}.txt', 'w') as file:
            file.write(f'CO\t\twins\tlosses\ttotal\twin%\n')
            for i in range(len(categories)):
                if len(f'{categories[i]}') < 4:
                    file.write(f'{categories[i]} \t{int(winc[i])}\t\t{int(losec[i])}\t\t'
                               f'{int(winc[i] + losec[i])}\t\t{100 * (winc[i] / (winc[i] + losec[i])):.4g}\n')
                else:
                    file.write(f'{categories[i]}\t{int(winc[i])}\t\t{int(losec[i])}\t\t'
                               f'{int(winc[i] + losec[i])}\t\t{100 * (winc[i] / (winc[i] + losec[i])):.4g}\n')
        plt.ylim([0, 100])
        # plt.grid(visible=True)
        plt.yticks(np.arange(11) * 10)  # np.linspace(start=0, stop=100, endpoint=True, num=11)
        # min_elo = 900


# def silly func
# all the GL CO pick data from all the profiles and plot aggro CO pick% vs rating
def map_co_stats():
    # x-axis: CO
    # y-axis: rating after game
    high_elo_cutoff = {'STD': 1300, 'FOG': 1300, 'HF': 1150}
    high_elo_cutoff = None
    mapp = "Caustic Finale"

    # figure stuff
    fig, ax = plt.subplots(1)
    fig.autofmt_xdate()  # format the x-axis for squeezing in longer tick labels

    for rules in ['STD']:  # ['STD', 'FOG', 'HF']
        # http://awbw.mooo.com/search?q=GL+STD+after+2025-05-18+rating%3E1000
        if high_elo_cutoff is not None:
            # s = f'GL+{rules}+after+2025-01-01+rating%3E{high_elo_cutoff[rules]}'
            s = f'GL+{rules}+{mapp}+rating%3E{high_elo_cutoff[rules]}'
            # s = f'GL+{rules}+rating%3E{high_elo_cutoff[rules]}'
        else:
            s = f'{rules}+{mapp}'

        if not os.path.isfile('outputs/' + 'map_search_' + rules + '.txt'):  # does the local file already exist?
            scrape_map(s, rules)

        # analysis
        categories = co_list_maker('std')
        days, winner, ratingw, ratingl, cow, col = retrieve_map(rules)

        # removers!
        removers = np.argwhere(days == 0)
        days[removers] = np.nan
        winner[removers] = np.nan
        ratingw[removers] = np.nan
        ratingl[removers] = np.nan
        # cow[removers] = np.nan
        # col[removers] = np.nan

        # plotting
        casee = 'co,win'  # co,win
        match casee:
            case 'co,rating':
                # plot of CO on x, rating on y
                avg_rating = 1
                for i, co in enumerate(categories):
                    avg_rating += i  # todo
                ax.scatter(categories, avg_rating,
                           s=10 * 100 * (winc + losec) / np.sum(winc + losec),
                           label=rules + ', ' + str(int(np.sum(winc + losec))), alpha=0.7)
            case 'co,win':
                # plot of CO on x, win% on y
                winc = np.zeros(len(categories))
                losec = np.zeros(len(categories))
                for i, co in enumerate(categories):
                    m = 0
                    for e in cow:
                        if e == co:
                            m += 1
                    n = 0
                    for e in col:
                        if e == co:
                            n += 1
                    winc[i] = m
                    losec[i] = n
                    # winc[i] = len(np.argwhere(cow == co))
                    # losec[i] = len(np.argwhere(col == co))

                ax.scatter(categories, (winc / (winc + losec)) * 100,
                           s=10 * 100 * (winc + losec) / np.sum(winc + losec),
                           label=rules + ', ' + str(int(np.sum(winc + losec))), alpha=0.7)
                plt.ylim([0, 100])
    plt.legend()
    plt.tight_layout()
    plt.grid()
    plt.show()


def scrape_map(search, rules):
    s = "http://awbw.mooo.com/searchReplays.php?q=" + search  # &spoiler=on
    page = page_getter(s)
    resultbox = str(page.find("div", class_="resultBox").next.next)

    # offsets = [1]
    # while offsets[-1] + 200 <= int(resultbox.split(' ')[0]):
    #     offsets.append(offsets[-1] + 200)
    try:
        offsets = [(e * 500) + 1 for e in range(int(np.ceil(int(resultbox.split(' ')[0]) / 500)))]
    except ValueError as e:  # ValueError: invalid literal for int() with base 10: 'No'
        print(f"search {search} had no results")
        print(e)
        quit()

    with open('outputs/' + 'sillysearch' + rules + '.txt', "w") as file:
        for offset in tqdm(offsets):
            if offset != 1:
                s = f"http://awbw.mooo.com/search?q={search}&offset={offset}"
                # http://awbw.mooo.com/search?q=live+league+std+"ncghost12"&offset={offset}
                # http://awbw.mooo.com/search?q=ncghost12&offset=201
                # http://awbw.mooo.com/searchReplays.php?q=ncghost12
                time.sleep(1)  # slows down searches on the mooo site so it doesn't get angi at me :>
                page = page_getter(s)

            table = page.find("div", class_="tableWrapper").find("table", class_="sortable").find("tbody")
            for row in table.find_all('tr'):
                items = row.find_all('td')
                p1win = False
                p2win = False
                if len(items[5].attrs['class']) == 2:  # as the alternative to 'playerColumn'
                    p2win = True
                elif len(items[7].attrs['class']) == 2:
                    p1win = True
                w = 1 if p1win else (2 if p2win else 0)
                for i, item in enumerate(items):
                    if 4 <= i <= 8:
                        match i:
                            case 4:
                                p1_co = str(item.attrs['data-sort'])
                            case 6:
                                p2_co = str(item.attrs['data-sort'])
                            case 5:
                                p1 = str(item.next.next)
                            case 7:
                                p2 = str(item.next.next)
                            case 8:
                                days = int(item.next)

                # saving stuff
                # days, winner 1/2/d, rating1, co1, rating2, co2
                a = (f"{days};{w};"
                     f"{int(p1[::-1].split('(')[0][::-1][:-1])};{p1_co};"
                     f"{int(p2[::-1].split('(')[0][::-1][:-1])};{p2_co}")
                file.write(a + "\n")


def retrieve_map(rules):
    table = np.loadtxt('outputs/' + 'sillysearch' + rules + '.txt', delimiter=';', dtype=str)

    days = np.zeros(table.shape[0])
    winner = np.zeros(table.shape[0])
    ratingw = np.zeros(table.shape[0])
    ratingl = np.zeros(table.shape[0])
    cow = [None] * table.shape[0]
    col = [None] * table.shape[0]
    for i, row in enumerate(table):
        # days, winner 1/2/d, rating1, co1, rating2, co2
        w = int(row[1])
        if w == 0:  # remove draws completely
            continue
        if row[3] == row[5]:
            continue  # removes mirrors completely
        winner[i] = w
        days[i] = int(row[0])

        ratings = [0, row[2], row[4]]
        cos = [0, row[3], row[5]]
        ratingw[i] = int(ratings[w])
        ratingl[i] = int(ratings[-w])
        cow[i] = cos[w]
        col[i] = cos[-w]

    return days, winner, ratingw, ratingl, cow, col


def extract_elo(s):
    table = np.loadtxt('outputs/' + s + '.txt', delimiter=';', dtype=str)
    if len(table.shape) != 2:
        print(f"only 1 result: {table}")
        quit()

    elo = np.zeros(table.shape[0])
    oppelo = np.zeros(table.shape[0])
    result = np.zeros(table.shape[0])
    days = np.zeros(table.shape[0])
    tier = [None] * table.shape[0]
    date = [None] * table.shape[0]
    co_pick = [None] * table.shape[0]
    co_against = [None] * table.shape[0]
    oppname = [None] * table.shape[0]
    for i, row in enumerate(table):
        # 1421286; 2025-05-06; Roll For Initiative; T2; 15; P1; ncghost12 ; 1016; eagle; ImSpartacus811 ; 779; kindle
        # 0: gameID
        # 1: date
        # 2: map
        # 3: TX
        # 4: days
        # 5: Pwin
        # 6: p1name
        # 7: p1elo
        # 8: p1co
        # 9: p2name
        # 10: p2elo
        # 11: p2co
        if row[6][1:] == s.split('+')[-1]:
            player = 1
        elif row[9][1:] == s.split('+')[-1]:
            player = 2
        else:
            print(row[6][1:-1])
            print(row[9][1:-1])
            print(s.split('+')[-1])
            print(row)
            raise Exception("name isn't p2 or p2? huhhh")

        if row[5][1:] == 'P' + str(player):
            result[i] = 1
        elif row[5][1:] == 'd':
            result[i] = 0
        else:
            result[i] = -1
        elo[i] = int(row[4 + (3 * player)])
        oppelo[i] = int(row[4 + (3 * (2 if player == 1 else 1))])
        date[i] = row[1][1:]
        co_pick[i] = row[5 + (3 * player)][1:]
        co_against[i] = row[5 + (3 * (2 if player == 1 else 1))][1:]
        tier[i] = row[3][2:]
        days[i] = int(row[4])
        oppname[i] = str(row[3 + (3 * (2 if player == 1 else 1))])[1:]
    return elo, date, oppelo, days, result, co_pick, co_against, tier, oppname


def redo_sort(elo, date, oppelo, days, result, co_pick, co_against, tier):
    # checks every permutation of games and finds the one that matches the real elo seen the closest. rounding hurts!
    # order = np.arange(len(elo))
    # i = 0
    # for perm in tqdm(iter.permutations(order)):
    #     elop = elo[order]
    #     oppelop = oppelo[order]
    #     resultp = result[order]
    #     elochecks = [800]  # todo gna break if i put a date cutoff.
    #     k = 50
    #     for j in len(order):
    #         if j == 30:
    #             k = 30
    #         elochecks.append(elochecks[-1] + exchange)
    #     if np.all(difs <= 1):
    #         break
    #     i += 1
    # final_order = order

    # # if s.split('+')[-1] == 'noname':  # todo
    # #     return elo, date, oppelo, days, result, co_pick, co_against, tier
    # for i, e in enumerate(elo):
    #     if i == 0:
    #         continue
    #     if result[i] == 1:
    #         elodiff = 1  # win
    #     elif result[i] == -1:
    #         elodiff = 1  # loss
    #     print(f'{elodiff} vs {e - elo[i - 1]}')
    #     a = calc_elo_exchanged(elo, oppelo, result)  # wrong inputs ik

    scrambled_games = []
    for i in range(len(elo)):
        if result[i] == 1:
            res = 1
        elif result[i] == -1:
            res = 0
        else:
            res = 0.5
        scrambled_games.append((int(elo[i]), int(oppelo[i]), res))  # (elo, oppelo, result)
    ordered, indexes = sort_games_by_actual_order(scrambled_games[::-1], elo_floor=700, tol=5)

    elo = elo[indexes]
    date = date[indexes]
    oppelo = oppelo[indexes]
    days = days[indexes]
    result = result[indexes]
    co_pick = co_pick[indexes]
    co_against = co_against[indexes]
    tier = tier[indexes]
    return elo, date, oppelo, days, result, co_pick, co_against, tier


def calc_elo_exchanged(elo1, elo2, win, morethan30=True):
    # calculates the player's (elo1) before a win, given elo after.
    # inverted order to make sense of how to build it up
    # elo1 = elo0 + exchange
    # exchange = k * (1-frac)  # or opposite way round


    k = 30  # 50 below 30 games played
    searching = True
    elo0 = 0
    while searching:
        frac = 1 / (1 + 10 ** (np.abs(elo1 - elo2) / 400))
        if win:
            exchange = k * frac
        else:
            exchange = k * (1 - frac)

        if elo1 <= elo0 + exchange <= elo1:
            searching = False
        elif elo0 > 1e4:
            return False  # this will get caught higher up
        else:
            elo0 += 1

    # elonew = elo1 + higherwin  # example
    # if win:
    #     return higherwin
    # return lowerwin
    return None


def scrape(search):
    s = "http://awbw.mooo.com/searchReplays.php?q=" + search  # &spoiler=on
    page = page_getter(s)
    resultbox = str(page.find("div", class_="resultBox").next.next)

    # offsets = [1]
    # while offsets[-1] + 200 <= int(resultbox.split(' ')[0]):
    #     offsets.append(offsets[-1] + 200)
    try:
        offsets = [(e * 500) + 1 for e in range(int(np.ceil(int(resultbox.split(' ')[0]) / 500)))]
    except ValueError as e:  # ValueError: invalid literal for int() with base 10: 'No'
        print(f"search {search} had no results")
        print(e)
        quit()
        # with open('outputs/' + search.replace('"', '') + '.txt', "w") as file:
        #     file.write(f"1; 2000-01-01; mapname; T?; 0; d; {search.split('+')[3:]} ; 0; andy; ****; 0; andy")
        #     # silly. but it'll b ok?
        #     return

    with open('outputs/' + search.replace('"', '') + '.txt', "w") as file:
        for offset in offsets:
            if offset != 1:
                s = f"http://awbw.mooo.com/search?q={search}&offset={offset}"
                # http://awbw.mooo.com/search?q=live+league+std+"ncghost12"&offset={offset}
                # http://awbw.mooo.com/search?q=ncghost12&offset=201
                # http://awbw.mooo.com/searchReplays.php?q=ncghost12
                time.sleep(1)  # slows down searches on the mooo site so it doesn't get angi at me :>
                page = page_getter(s)

            table = page.find("div", class_="tableWrapper").find("table", class_="sortable").find("tbody")
            for row in table.find_all('tr'):
                tag = False
                # the following has p1 win and p2 lose:
                # downloadColumn - "replay/1421134.zip" means "awbw.mooo.com/" + that
                # nC (name)
                # mapIColumn (map image)
                # mC (map name)
                # coColumn
                # playerColumn
                # coColumn loser
                # playerColumn loser
                # dC (days)
                # dtC (date)
                items = row.find_all('td')
                p1win = False
                p2win = False
                if len(items[5].attrs['class']) == 2:  # as the alternative to 'playerColumn'
                    p2win = True
                elif len(items[7].attrs['class']) == 2:
                    p1win = True
                w = 1 if p1win else (2 if p2win else 'd')
                for i, item in enumerate(items):
                    if 4 <= i <= 9:
                        match i:
                            case 4:
                                p1_co = str(item.attrs['data-sort'])
                                if p1_co[0] == '_':
                                    tag = True
                                    break
                            case 7:
                                p2_co = str(item.attrs['data-sort'])
                                if p2_co[0] == '_':
                                    tag = True
                                    break
                            case 5:
                                p1 = str(item.next.next)
                            case 6:
                                try:
                                    p1r = int(item.next)
                                except TypeError:
                                    p1r = int(0)
                            case 8:
                                p2 = str(item.next.next)
                            case 9:
                                try:
                                    p2r = int(item.next)
                                except TypeError:
                                    p2r = int(0)
                    else:
                        match item['class'][0]:
                            case 'dC':  # 0
                                try:
                                    replay_link = str(item.next.attrs['href'])
                                except KeyError:
                                    replay_link = 'moo/0.zip'
                            case 'nC':  # 1
                                game_name = str(item.next.next)
                            case 'mC':  # 2
                                map_name = str(item.next.next)
                            case 'daC':  # 8
                                days = int(item.next)
                            case 'dtC':  # 9
                                date = str(item.next)
                            case 'mapIC':
                                pass
                            case _:
                                print(f"unexpected item {item}")

                if tag:
                    continue
                # fully scraped this line, now formatting stuff
                game_ID = replay_link.split('.zip')[0].split('/')[1]
                if game_name[0:13] == 'Live League -':
                    tier = int(game_name[::-1].split(' ,')[1][0])
                    # Live League - mapname - (TX, rules)
                elif game_name[0:3] == 'GL ':
                    try:
                        tier = int(game_name.split('[')[1][1])
                    except ValueError as e:
                        print(e)  # todo wtf? StarFlash250 breaks this January 2024 GL, idk what happen.
                    # GL rules [TX]: P1 vs P2
                else:
                    tier = '?'  # unknown tier?

                # saving stuff
                # game_ID; date; map_name; tier; days; winner (1/2/d); name1; rating1; co1; name2; rating2; co2
                a = f"{game_ID}; {date}; {map_name}; T{tier}; {days}; {w if w == 'd' else 'P' + str(w)}"
                p1a = f"{p1}; {int(p1r)}; {p1_co}"
                p2a = f"{p2}; {int(p2r)}; {p2_co}"
                g = a + "; " + p1a + "; " + p2a + "\n"
                while True:
                    try:
                        file.write(g)
                        break
                    except UnicodeEncodeError as e:
                        g = g[:e.args[2]] + '*' + g[e.args[2] + 1:]

    # save first, then go back and re-order based on game order :D
    # you can still probably confuse the ordering by finishing another game while the first is ongoing
    # will happen quite often in GL but not as much in LL. gna make a fix for this later. maybee


def co_list_maker(rules):
    # returns a list of all COs ordered from T4-...-T1-T0-T? given the ruleset inputted
    match rules:
        case 'std':
            return [
                'adder', 'grimm', 'jake', 'jess', 'koal', 'sonja',
                'andy', 'drake', 'lash', 'rachel',
                'eagle', 'kindle', 'max', 'olaf', 'sami', 'hawke', 'javier', 'sasha', 'vonbolt',
                'colin', 'grit', 'hachi', 'kanbei', 'sensei', 'sturm',
                'flak', 'jugger', 'nell'
            ]
        case 'fog':
            return [
                'adder', 'grimm', 'jake', 'jess', 'koal',
                'andy', 'drake', 'kindle', 'lash', 'rachel', 'sami', 'sonja',
                'eagle', 'max', 'olaf',
                'grit', 'hawke', 'javier', 'sasha', 'vonbolt',
                'colin', 'hachi', 'kanbei', 'sensei', 'sturm',
                'flak', 'jugger', 'nell'
            ]
        case 'hf':
            return [
                'adder', 'grimm', 'jake', 'jess', 'koal', 'sami', 'sonja',
                'javier', 'kindle', 'rachel', 'sasha', 'lash',
                'andy', 'drake', 'grit', 'max', 'sturm', 'vonbolt',
                'eagle', 'hawke', 'olaf', 'sensei',
                'colin', 'hachi', 'kanbei',
                'flak', 'jugger', 'nell'
            ]
        case _:  # alphabetical by army, as on the site. redundant hopefully
            return [
                'andy', 'hachi', 'jake', 'max', 'nell', 'rachel', 'sami', 'colin', 'grit', 'olaf',
                'sasha', 'drake', 'eagle', 'javier', 'jess', 'grimm', 'kanbei', 'sensei', 'sonja',
                'adder', 'flak', 'hawke', 'jugger', 'kindle', 'koal', 'lash', 'sturm', 'vonbolt'
            ]


def page_getter(url):
    page = requests.get(url)
    page.raise_for_status()
    return BeautifulSoup(page.content, features="html.parser")  # todo check parser


def page_getter_slow(url):
    # https://stackoverflow.com/a/45892965
    browser = webdriver.Chrome()

    browser.get(url)
    time.sleep(5)
    soup = BeautifulSoup(browser.page_source, features="html.parser")

    # print(len(soup.find_all("table")))
    # print(soup.find("table", {"id": "expanded_standings"}))

    browser.close()
    browser.quit()
    return soup
