import time

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from bs4 import BeautifulSoup
import requests
import os.path
import datetime as dt

"""
run plot_elo() and freely change league/rules/name
"""


def plot_elo():
    league = 'live+league'
    # league = 'global+league'
    plot_option = 'elo'
    plot_option = 'date,elo'
    # plot_option = 'co_pick,winrate'
    plot_option = 'co_against,winrate'
    plot_option = 'tier,winrate'

    fig, ax = plt.subplots(1)
    if plot_option == 'date,elo' or plot_option == 'co_pick,winrate' or plot_option == 'co_against,winrate':
        fig.autofmt_xdate()  # format the x-axis for squeezing in longer tick labels
    # ['std', 'hf', 'fog']:
    for rules in ['std']:

        # ['High Funds High Fun', 'Po1and', 'Po2and', 'new1234', 'WealthyTuna', 'Spidy400']:
        # ['ncghost12', 'new1234', 'Heuristic']:
        for name in ['Po1and', 'Po2and']:

            # search/save string
            s = f"{league}+{rules}+{name}"

            if not os.path.isfile('outputs/' + s + '.txt'):  # does the local file already exist?
                print(f'scraping for {s}')
                scrape(s)  # scrapes the mooo site for the search, saves to file

            elo, date, oppelo, date, result, co_pick, co_against, tier = extract_elo(s)  # extracts stuff from file

            # plot :>
            match plot_option:
                case 'elo':
                    ax.plot(elo[::-1], '-', label=name)
                    # ax.plot(oppelo[::-1], '.', label='oppelo')
                case 'date,elo':
                    datex = [dt.datetime.strptime(d, '%Y-%m-%d').date() for d in date]
                    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
                    ax.plot(datex, elo, '-', label=name)
                case 'co_pick,winrate':
                    categories = co_list_maker(rules)
                    entries = co_pick
                case 'co_against,winrate':
                    categories = co_list_maker(rules)
                    entries = co_against
                case 'tier,winrate':
                    categories = ['4', '3', '2', '1', '0', '?']  # tiers
                    entries = tier
            if plot_option.split(',')[-1] == 'winrate':  # figure out winrate in % for categories
                winc = np.zeros(len(categories))
                losec = np.zeros(len(categories))
                for i, e in enumerate(entries):
                    if result[i] == 1:
                        winc[categories.index(e)] += 1
                    elif result[i] == -1:
                        losec[categories.index(e)] += 1
                    else:
                        # game was drawn case, wanna plot it?
                        pass
                ax.plot(categories, (winc / (winc + losec)) * 100, 'o', label=name)
                plt.ylim([0, 100])

    plt.legend()
    plt.tight_layout()
    plt.show()


def extract_elo(s):
    table = np.loadtxt('outputs/' + s + '.txt', delimiter=';', dtype=str)

    elo = np.zeros(table.shape[0])
    oppelo = np.zeros(table.shape[0])
    result = np.zeros(table.shape[0])
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
        if row[6][1:-1] == s.split('+')[-1]:
            player = 1
        elif row[9][1:-1] == s.split('+')[-1]:
            player = 2
        else:
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
    return elo, date, oppelo, date, result, co_pick, co_against, tier


def scrape(search):
    s = "http://awbw.mooo.com/searchReplays.php?q=" + search  # &spoiler=on
    page = page_getter(s)
    resultbox = str(page.find("div", class_="resultBox").next.next)

    # offsets = [1]
    # while offsets[-1] + 200 <= int(resultbox.split(' ')[0]):
    #     offsets.append(offsets[-1] + 200)
    offsets = [(e * 200) + 1 for e in range(int(np.ceil(int(resultbox.split(' ')[0]) / 200)))]

    with open(f"outputs/{search}.txt", "w") as file:
        for offset in offsets:
            if offset != 1:
                s = f"http://awbw.mooo.com/search?q={search}&offset={offset}"
                # http://awbw.mooo.com/search?q=ncghost12&offset=201
                # http://awbw.mooo.com/searchReplays.php?q=ncghost12
                time.sleep(2)  # slows down searches on the mooo site so it doesn't get angi at me :>
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
                    if 4 <= i <= 7:
                        match i:
                            case 4:
                                p1_co = str(item.attrs['data-sort'])
                            case 6:
                                p2_co = str(item.attrs['data-sort'])
                            case 5:
                                p1 = str(item.next.next)
                            case 7:
                                p2 = str(item.next.next)
                    else:
                        match item['class'][0]:
                            case 'downloadColumn':  # 0
                                replay_link = str(item.next.attrs['href'])
                            case 'nC':  # 1
                                game_name = str(item.next.next)
                            case 'mC':  # 2
                                map_name = str(item.next.next)
                            case 'dC':  # 8
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
                    tier = int(game_name.split('[')[1][1])
                    # GL rules [TX]: P1 vs P2
                else:
                    tier = '?'  # unknown tier?

                # saving stuff
                # game_ID; date; map_name; tier; days; winner (1/2/d); name1; rating1; co1; name2; rating2; co2
                a = f"{game_ID}; {date}; {map_name}; T{tier}; {days}; {w if w == 'd' else 'P' + str(w)}"
                p1a = f"{p1[::-1].split('(')[1][::-1]}; {int(p1[::-1].split('(')[0][::-1][:-1])}; {p1_co}"
                p2a = f"{p2[::-1].split('(')[1][::-1]}; {int(p2[::-1].split('(')[0][::-1][:-1])}; {p2_co}"
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
                'javier', 'kindle', 'rachel', 'sasha',
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
