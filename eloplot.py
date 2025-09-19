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

from fitting import fit

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
    plot_option = 'tier,winrate'  # winrate on tier
    # plot_option = 'days,winrate'  # winrate on days of game
    # plot_option = 'date,days'  # days of game on date  # todo
    # plot_option = 'days'  # days of game on game number  # todo
    # plot_option = 'map,co'  # map!!  # todo
    # plot_option = 'map,p1/p2 on date'  # map!!  # todo
    # plot_option = 'map,days'  # map!!  # todo
    gauss_filter = False  # 0/False, 1/True

    # for winrate plots, discards ALL games that don't have BOTH players ending >= this elo
    min_elo = 700
    # min_elo = 1100

    league = 'live+league'
    # league = 'global+league'
    # league = ''  # neither

    rules = ['std'] # ['std', 'hf', 'fog']
    names = ['J.Yossarian', 'new1234', 'ncghost12']
    # ['WealthyTuna', 'new1234', 'hunch', 'Po1and', 'Po2and']
    # ['Grimm Guy', 'Grimm Girl', 'J.Yossarian']
    # ['High Funds High Fun', 'Po1and', 'Po2and', 'new1234', 'WealthyTuna', 'Spidy400']
    # ['ncghost12', 'new1234', 'Heuristic']
    # ['Voice of Akasha', 'Grimm Guy', 'tesla246']
    # ['new1234', 'fluhfie', 'Spidy400']
    # ['Deejus_', 'GetGood', 'AdvanceNoob', 'hapahauli', 'fluhfie']

    plot_elo(plot_option, league, rules, names, min_elo, plot_oppelo, plot_fit, gauss_filter)


def plotter_alt():
    # what do u wanna plot?
    plot_option = 'elo'  # elo on game number
    league = 'live+league'
    # league = 'global+league'
    # league = 'global+league+all+time'

    rules = ['std', 'hf', 'fog']  # ['std', 'hf', 'fog']

    fig, ax = plt.subplots(1)
    fig.autofmt_xdate()  # format the x-axis for squeezing in longer tick labels

    for ruleset in rules:
        match league:
            case 'live+league':
                s = f'https://awbw.amarriner.com/live_league_standings.php?mode={ruleset}&sort=elo'
                page = page_getter(s)
            case 'global+league':
                s = f'https://awbw.amarriner.com/newleague_standings.php?type={ruleset}&time=curr'
                page = page_getter(s)
            case 'global+league+all+time':
                s = f'https://awbw.amarriner.com/newleague_standings.php?type={ruleset}&time=all'
                page = page_getter(s)
            case _:
                raise Exception(f'"{ruleset}" was not a match for any actual ruleset (std, hf, fog)')

        page.find("table").find_all('tr')[4]

        test = 1
        test = 2
        resultbox = str(page.find("div", class_="resultBox").next.next)
        # ax.plot([800, *elo[::-1]], '-', label=label)
    plt.show()



def plot_elo(plot_option, league, rulesiter, nameiter, min_elo, plot_oppelo, plot_fit, gauss_filter):

    # figure stuff
    fig, ax = plt.subplots(1)
    if plot_option in ['date,elo', 'co_pick,winrate', 'co_against,winrate', 'date,days']:
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
            elo, date, oppelo, days, result, co_pick, co_against, tier = extract_elo(s.replace('"', ''))

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
                    if oppelo[i] < min_elo or elo[i] < min_elo:  # todo
                        continue
                    if result[i] == 1:
                        wins[i] = e
                        winc[categories.index(e)] += 1
                    elif result[i] == -1:
                        loses[i] = e
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
                print(f'{label}: {winsum / sum(winc):.1f} {losesum / sum(losec):.1f} & weight: {winweight:.1f} {loseweight:.1f}')
                print(f'{np.array(winc) + np.array(losec)}')  # days

                if plot_option == 'days,winrate':
                    plt.xlim([0, int(np.amax(days))])
                    if gauss_filter and plot_option == 'days,winrate':  # blur
                        sigma = 0.5
                        winc = gaussian_filter(winc, sigma=sigma, mode='nearest')
                        losec = gaussian_filter(losec, sigma=sigma, mode='nearest')
                    # else:  # plot line
                    #     ax.plot(categories, (winc / (winc + losec)) * 100, '-')

                ax.scatter(categories, (winc / (winc + losec)) * 100,
                           s=10 * 100 * (winc + losec) / np.sum(winc + losec),
                           label=label + ', ' + str(int(np.sum(winc + losec))))
                ax.scatter(x=categories, y=50 * np.ones(len(categories)), marker='.', c='k')
                plt.ylim([0, 100])
                # plt.grid(visible=True)
                plt.yticks(np.arange(11) * 10)  # np.linspace(start=0, stop=100, endpoint=True, num=11)
            # min_elo = 900

    # plt.ylim([40, 100])
    plt.legend()
    plt.tight_layout()
    plt.grid()
    plt.show()


# def silly func
# all the GL CO pick data from all the profiles and plot aggro CO pick% vs rating
def silly_func():
    # x-axis: CO
    # y-axis: rating after game
    high_elo_cutoff = {'STD': 1300, 'FOG': 1300, 'HF': 1150}
    mapp = "Caustic Finale"

    # figure stuff
    fig, ax = plt.subplots(1)
    fig.autofmt_xdate()  # format the x-axis for squeezing in longer tick labels

    for rules in ['STD']:  # ['STD', 'FOG', 'HF']
        # http://awbw.mooo.com/search?q=GL+STD+after+2025-05-18+rating%3E1000
        # s = f'GL+{rules}+after+2025-01-01+rating%3E{high_elo_cutoff[rules]}'
        s = f'GL+{rules}+{mapp}+rating%3E{high_elo_cutoff[rules]}'
        # s = f'GL+{rules}+rating%3E{high_elo_cutoff[rules]}'

        if not os.path.isfile('outputs/' + 'sillysearch' + rules + '.txt'):  # does the local file already exist?
            scrape_silly(s, rules)

        # analysis
        categories = co_list_maker('agro')
        days, winner, ratingw, ratingl, cow, col = retrieve_silly(rules)

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


def scrape_silly(search, rules):
    s = "http://awbw.mooo.com/searchReplays.php?q=" + search  # &spoiler=on
    page = page_getter(s)
    resultbox = str(page.find("div", class_="resultBox").next.next)

    # offsets = [1]
    # while offsets[-1] + 200 <= int(resultbox.split(' ')[0]):
    #     offsets.append(offsets[-1] + 200)
    try:
        offsets = [(e * 200) + 1 for e in range(int(np.ceil(int(resultbox.split(' ')[0]) / 200)))]
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


def retrieve_silly(rules):
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

    elo = np.zeros(table.shape[0])
    oppelo = np.zeros(table.shape[0])
    result = np.zeros(table.shape[0])
    days = np.zeros(table.shape[0])
    tier = [None] * table.shape[0]
    date = [None] * table.shape[0]
    co_pick = [None] * table.shape[0]
    co_against = [None] * table.shape[0]
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
    return elo, date, oppelo, days, result, co_pick, co_against, tier


def redo_sort(elo, date, oppelo, days, result, co_pick, co_against, tier, s):
    # if s.split('+')[-1] == 'noname':  # todo?
    #     return elo, date, oppelo, days, result, co_pick, co_against, tier
    for i, e in enumerate(elo):
        if i == 0:
            continue
        if result[i] == 1:
            elodiff = 1  # win
        elif result[i] == -1:
            elodiff = 1  # loss
        print(f'{elodiff} vs {e - elo[i - 1]}')
        a = calc_elo_exchanged(elo, oppelo, result)  # wrong inputs ik
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
        offsets = [(e * 200) + 1 for e in range(int(np.ceil(int(resultbox.split(' ')[0]) / 200)))]
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
                            case 7:
                                p2_co = str(item.attrs['data-sort'])
                            case 5:
                                p1 = str(item.next.next)
                            case 6:
                                p1r = int(item.next)
                            case 8:
                                p2 = str(item.next.next)
                            case 9:
                                p2r = int(item.next)
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
                            case 'mapIColumn':
                                pass
                            case _:
                                print(f"unexpected item {item}")

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
