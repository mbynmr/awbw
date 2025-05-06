import numpy as np
import matplotlib.pyplot as plt
from bs4 import BeautifulSoup
import requests



"""
run plot_elo() on a text file
"""


def plot_elo():
    league = 'live+league'
    # league = 'global+league'
    rules = 'std'
    # rules = 'hf'
    # rules = 'fog'
    name = 'ncghost12'  # 'wealthytuna'

    s = f"{league}+{rules}+{name}"
    scrape(s)
    # save first, then go back and re-order based on game order :D
    # you can still probably confuse the ordering by finishing another game while the first is ongoing
    # will happen quite often in GL but not as much in LL. gna make a fix for this later.

    table = np.loadtxt(s + '.txt', delimiter='; ')

    for row in table:
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
        if row[6] == name:
            player = 1
        elif row[9] == name:
            player = 2
        else:
            print(row)
            raise Exception("player isn't p2 or p2?")
        if row[5] == 'P' + str(player):
            win = True

    # plt.plot()
    # plt.show()


def scrape(search):
    s = "http://awbw.mooo.com/searchReplays.php?q=" + search  # &spoiler=on
    page = requests.get(s)
    page.raise_for_status()

    page = BeautifulSoup(page.content, features="html.parser")  # todo check parser

    resultbox = str(page.find("div", class_="resultBox").next.next)
    offsets = [1]
    # todo rewrite with for in 1 line: offsets = [(e * 200) + 1 for e in range(int(int(resultbox.split(' ')[0]) / 200))]
    # if resultbox.split(' ')[1] == 'total':
    # 100: 1+200<=100 FALSE
    # 250: 1+200<=250 TRUE append; 201+200<=250 FALSE
    # 200: 1+200<=200 FALSE
    # 201: 1+200<=201 TRUE append; 201+200<=201 FALSE
    while offsets[-1] + 200 <= int(resultbox.split(' ')[0]):
        offsets.append(offsets[-1] + 200)
    # print(offsets)  # todo remove this

    with open(f"outputs/{league}+{rules}+{name}.txt", "w") as file:
        for offset in offsets:
            if offset != 1:
                s = f"http://awbw.mooo.com/search?q={league}+{rules}+{name}&offset={offset}"
                # http://awbw.mooo.com/search?q=ncghost12&offset=201
                # http://awbw.mooo.com/searchReplays.php?q=ncghost12
                page = requests.get(s)
                page.raise_for_status()
                page = BeautifulSoup(page.content, features="html.parser")

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
                    # if item in ['list of text entry items looking for', {'class': ['playerColumn']}]:
                    #     text = item.next
                    #     s = ''
                    #     while s == '':
                    #         try:
                    #             s = text
                    #         except Exception as e:  # update this to be the right exception
                    #             print(e)
                    #             text = text.next
                    #             continue
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

                game_ID = replay_link.split('.zip')[0].split('/')[1]
                if game_name[0:13] == 'Live League -':
                    tier = int(game_name[::-1].split(' ,')[1][0])
                    # Live League - mapname - (TX, rules)
                elif game_name[0:3] == 'GL ':
                    tier = int(game_name.split('[')[1][1])
                    # GL rules [TX]: P1 vs P2
                else:
                    tier = '?'  # unknown tier?
                p1_name = p1[::-1].split('(')[1][::-1]
                p1_rating = int(p1[::-1].split('(')[0][::-1][:-1])
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

