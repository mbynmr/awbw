import numpy as np
# import matplotlib.pyplot as plt
# from tqdm import tqdm


def load_map(path='maps/Last Vigil.txt'):
    print('loading map...')
    print(f'map path: {path}')
    ids = np.loadtxt(path, delimiter=',', dtype=int)
    ownedby = np.zeros_like(ids)
    stars = np.zeros_like(ids)
    access = np.zeros_like(ids)
    production = np.zeros_like(ids)
    repair = np.zeros_like(ids)
    special = np.zeros_like(ids)
    for i in range(ids.shape[0]):
        for j in range(ids.shape[1]):
            ownedby[i, j], stars[i, j], repair[i, j], production[i, j], access[i, j], special[i, j] = \
                convert_id_to_details(ids[i, j])
    # in awbw across is the first coordinate like (x, y) starting top left corner. this does not match, b careful!
    return ownedby, stars, repair, production, access, special


def convert_id_to_details(idn):
    TS_terrainIdToName = {
        "1": "plain", "2": "mountain", "3": "wood", "4": "hriver", "5": "vriver", "6": "criver", "7": "esriver",
        "8": "swriver", "9": "wnriver", "10": "neriver", "11": "eswriver", "12": "swnriver", "13": "wneriver",
        "14": "nesriver", "15": "hroad", "16": "vroad", "17": "croad", "18": "esroad", "19": "swroad", "20": "wnroad",
        "21": "neroad", "22": "eswroad", "23": "swnroad", "24": "wneroad", "25": "nesroad", "26": "hbridge",
        "27": "vbridge", "29": "hshoal", "30": "hshoaln", "31": "vshoal", "32": "vshoale", "33": "reef",
        "34": "neutralcity", "35": "neutralbase", "36": "neutralairport", "37": "neutralport", "38": "orangestarcity",
        "39": "orangestarbase", "40": "orangestarairport", "41": "orangestarport", "42": "orangestarhq",
        "43": "bluemooncity", "44": "bluemoonbase", "45": "bluemoonairport", "46": "bluemoonport", "47": "bluemoonhq",
        "48": "greenearthcity", "49": "greenearthbase", "50": "greenearthairport", "51": "greenearthport",
        "52": "greenearthhq", "53": "yellowcometcity", "54": "yellowcometbase", "55": "yellowcometairport",
        "56": "yellowcometport", "57": "yellowcomethq", "81": "redfirecity", "82": "redfirebase",
        "83": "redfireairport", "84": "redfireport", "85": "redfirehq", "86": "greyskycity", "87": "greyskybase",
        "88": "greyskyairport", "89": "greyskyport", "90": "greyskyhq", "91": "blackholecity", "92": "blackholebase",
        "93": "blackholeairport", "94": "blackholeport", "95": "blackholehq", "96": "browndesertcity",
        "97": "browndesertbase", "98": "browndesertairport", "99": "browndesertport", "100": "browndeserthq",
        "101": "vpipe", "102": "hpipe", "103": "nepipe", "104": "espipe", "105": "swpipe", "106": "wnpipe",
        "107": "npipeend", "108": "epipeend", "109": "spipeend", "110": "wpipeend", "111": "missilesilo",
        "112": "missilesiloempty", "113": "hpipeseam", "114": "vpipeseam", "115": "hpiperubble", "116": "vpiperubble",
        "117": "amberblazeairport", "118": "amberblazebase", "119": "amberblazecity", "120": "amberblazehq",
        "121": "amberblazeport", "122": "jadesunairport", "123": "jadesunbase", "124": "jadesuncity",
        "125": "jadesunhq", "126": "jadesunport", "127": "amberblazecomtower", "128": "blackholecomtower",
        "129": "bluemooncomtower", "130": "browndesertcomtower", "131": "greenearthcomtower", "132": "jadesuncomtower",
        "133": "neutralcomtower", "134": "orangestarcomtower", "135": "redfirecomtower", "136": "yellowcometcomtower",
        "137": "greyskycomtower", "138": "amberblazelab", "139": "blackholelab", "140": "bluemoonlab",
        "141": "browndesertlab", "142": "greenearthlab", "143": "greyskylab", "144": "jadesunlab", "145": "neutrallab",
        "146": "orangestarlab", "147": "redfirelab", "148": "yellowcometlab", "149": "cobalticeairport",
        "150": "cobalticebase", "151": "cobalticecity", "152": "cobalticecomtower", "153": "cobalticehq",
        "154": "cobalticelab", "155": "cobalticeport", "156": "pinkcosmosairport", "157": "pinkcosmosbase",
        "158": "pinkcosmoscity", "159": "pinkcosmoscomtower", "160": "pinkcosmoshq", "161": "pinkcosmoslab",
        "162": "pinkcosmosport", "163": "tealgalaxyairport", "164": "tealgalaxybase", "165": "tealgalaxycity",
        "166": "tealgalaxycomtower", "167": "tealgalaxyhq", "168": "tealgalaxylab", "169": "tealgalaxyport",
        "170": "purplelightningairport", "171": "purplelightningbase", "172": "purplelightningcity",
        "173": "purplelightningcomtower", "174": "purplelightninghq", "175": "purplelightninglab",
        "176": "purplelightningport", "181": "acidrainairport", "182": "acidrainbase", "183": "acidraincity",
        "184": "acidraincomtower", "185": "acidrainhq", "186": "acidrainlab", "187": "acidrainport",
        "188": "whitenovaairport", "189": "whitenovabase", "190": "whitenovacity", "191": "whitenovacomtower",
        "192": "whitenovahq", "193": "whitenovalab", "194": "whitenovaport", "195": "teleporter",
        "196": "azureasteroidairport", "197": "azureasteroidbase", "198": "azureasteroidcity",
        "199": "azureasteroidcomtower", "200": "azureasteroidhq", "201": "azureasteroidlab", "202": "azureasteroidport",
        "203": "noireclipseairport", "204": "noireclipsebase", "205": "noireclipsecity", "206": "noireclipsecomtower",
        "207": "noireclipsehq", "208": "noireclipselab", "209": "noireclipseport"
    }

    armies = [
        'neutral', 'amberblaze', 'blackhole', 'bluemoon', 'browndesert', 'greenearth', 'jadesun', 'orangestar',
        'redfire', 'yellowcomet', 'greysky', 'cobaltice', 'pinkcosmos', 'tealgalaxy', 'purplelightning',
        'acidrain', 'whitenova', 'azureasteroid', 'noireclipse'
    ]
    s = TS_terrainIdToName[str(idn)]
    owned_by = 0
    for i, e in enumerate(armies):
        if e in s:
            owned_by = i
            s = s.removeprefix(e)
            break

    # repair - 0: none, 1: ground, 2: sea, 3: air
    # production - 0: none, 1: base, 2: port, 3: airport
    # access - 0: road, 1: plain, 2: wood, 3: river, 4: shoal, 5: sea, 6: pipe, 7: port, 8: base, 9: mountain
    # special - 0: misc, 1: pipeseam, 2: missile, 3: road, 4: plain, 5: urban
    terrain_details = [
        # [stars, repair, production, access, special]
        [0, 0, 0, 0, 3],  # road
        [0, 0, 0, 4, 0],  # shoal
        [0, 0, 0, 0, 0],  # bridge
        [0, 0, 0, 0, 0],  # river
        [0, 0, 0, 0, 0],  # piperubble
        [0, 0, 0, 6, 1],  # pipeseam
        [0, 0, 0, 6, 0],  # pipe
        [0, 0, 0, 5, 0],  # sea
        [1, 0, 0, 5, 0],  # reef
        [1, 0, 0, 1, 4],  # plain
        [2, 0, 0, 2, 0],  # wood
        [3, 0, 0, 0, 0],  # siloempty
        [3, 0, 0, 0, 2],  # silo
        [3, 1, 1, 8, 5],  # base
        [3, 3, 3, 0, 5],  # airport
        [3, 2, 2, 7, 5],  # port
        [3, 1, 0, 0, 5],  # city
        [3, 0, 0, 0, 5],  # comtower
        [3, 0, 0, 0, 5],  # lab
        [4, 0, 0, 9, 0],  # mountain
        [4, 1, 0, 0, 5]  # hq
    ]
    all_terrain = [
        'road', 'shoal', 'bridge', 'river', 'piperubble', 'pipeseam', 'pipe', 'sea',  # others before plain pipe
        'reef', 'plain',
        'wood',
        'siloempty', 'silo', 'base', 'airport', 'port', 'city', 'comtower', 'lab',
        'mountain', 'hq'
    ]
    for i, e in enumerate(all_terrain):
        if e in s:
            return owned_by, *terrain_details[i]  # exit asap :>
    raise ValueError(f"couldn't find terrain with id number {idn}")


def convert_id_to_details_old(idn):
    TS_terrainIdToName = {
        "1": "plain", "2": "mountain", "3": "wood", "4": "hriver", "5": "vriver", "6": "criver", "7": "esriver",
        "8": "swriver", "9": "wnriver", "10": "neriver", "11": "eswriver", "12": "swnriver", "13": "wneriver",
        "14": "nesriver", "15": "hroad", "16": "vroad", "17": "croad", "18": "esroad", "19": "swroad", "20": "wnroad",
        "21": "neroad", "22": "eswroad", "23": "swnroad", "24": "wneroad", "25": "nesroad", "26": "hbridge",
        "27": "vbridge", "29": "hshoal", "30": "hshoaln", "31": "vshoal", "32": "vshoale", "33": "reef",
        "34": "neutralcity", "35": "neutralbase", "36": "neutralairport", "37": "neutralport", "38": "orangestarcity",
        "39": "orangestarbase", "40": "orangestarairport", "41": "orangestarport", "42": "orangestarhq",
        "43": "bluemooncity", "44": "bluemoonbase", "45": "bluemoonairport", "46": "bluemoonport", "47": "bluemoonhq",
        "48": "greenearthcity", "49": "greenearthbase", "50": "greenearthairport", "51": "greenearthport",
        "52": "greenearthhq", "53": "yellowcometcity", "54": "yellowcometbase", "55": "yellowcometairport",
        "56": "yellowcometport", "57": "yellowcomethq", "81": "redfirecity", "82": "redfirebase",
        "83": "redfireairport", "84": "redfireport", "85": "redfirehq", "86": "greyskycity", "87": "greyskybase",
        "88": "greyskyairport", "89": "greyskyport", "90": "greyskyhq", "91": "blackholecity", "92": "blackholebase",
        "93": "blackholeairport", "94": "blackholeport", "95": "blackholehq", "96": "browndesertcity",
        "97": "browndesertbase", "98": "browndesertairport", "99": "browndesertport", "100": "browndeserthq",
        "101": "vpipe", "102": "hpipe", "103": "nepipe", "104": "espipe", "105": "swpipe", "106": "wnpipe",
        "107": "npipeend", "108": "epipeend", "109": "spipeend", "110": "wpipeend", "111": "missilesilo",
        "112": "missilesiloempty", "113": "hpipeseam", "114": "vpipeseam", "115": "hpiperubble", "116": "vpiperubble",
        "117": "amberblazeairport", "118": "amberblazebase", "119": "amberblazecity", "120": "amberblazehq",
        "121": "amberblazeport", "122": "jadesunairport", "123": "jadesunbase", "124": "jadesuncity",
        "125": "jadesunhq", "126": "jadesunport", "127": "amberblazecomtower", "128": "blackholecomtower",
        "129": "bluemooncomtower", "130": "browndesertcomtower", "131": "greenearthcomtower", "132": "jadesuncomtower",
        "133": "neutralcomtower", "134": "orangestarcomtower", "135": "redfirecomtower", "136": "yellowcometcomtower",
        "137": "greyskycomtower", "138": "amberblazelab", "139": "blackholelab", "140": "bluemoonlab",
        "141": "browndesertlab", "142": "greenearthlab", "143": "greyskylab", "144": "jadesunlab", "145": "neutrallab",
        "146": "orangestarlab", "147": "redfirelab", "148": "yellowcometlab", "149": "cobalticeairport",
        "150": "cobalticebase", "151": "cobalticecity", "152": "cobalticecomtower", "153": "cobalticehq",
        "154": "cobalticelab", "155": "cobalticeport", "156": "pinkcosmosairport", "157": "pinkcosmosbase",
        "158": "pinkcosmoscity", "159": "pinkcosmoscomtower", "160": "pinkcosmoshq", "161": "pinkcosmoslab",
        "162": "pinkcosmosport", "163": "tealgalaxyairport", "164": "tealgalaxybase", "165": "tealgalaxycity",
        "166": "tealgalaxycomtower", "167": "tealgalaxyhq", "168": "tealgalaxylab", "169": "tealgalaxyport",
        "170": "purplelightningairport", "171": "purplelightningbase", "172": "purplelightningcity",
        "173": "purplelightningcomtower", "174": "purplelightninghq", "175": "purplelightninglab",
        "176": "purplelightningport", "181": "acidrainairport", "182": "acidrainbase", "183": "acidraincity",
        "184": "acidraincomtower", "185": "acidrainhq", "186": "acidrainlab", "187": "acidrainport",
        "188": "whitenovaairport", "189": "whitenovabase", "190": "whitenovacity", "191": "whitenovacomtower",
        "192": "whitenovahq", "193": "whitenovalab", "194": "whitenovaport", "195": "teleporter",
        "196": "azureasteroidairport", "197": "azureasteroidbase", "198": "azureasteroidcity",
        "199": "azureasteroidcomtower", "200": "azureasteroidhq", "201": "azureasteroidlab", "202": "azureasteroidport",
        "203": "noireclipseairport", "204": "noireclipsebase", "205": "noireclipsecity", "206": "noireclipsecomtower",
        "207": "noireclipsehq", "208": "noireclipselab", "209": "noireclipseport"
    }
    armies = [
        'neutral', 'amberblaze', 'blackhole', 'bluemoon', 'browndesert', 'greenearth', 'jadesun', 'orangestar',
        'redfire', 'yellowcomet', 'greysky', 'cobaltice', 'pinkcosmos', 'tealgalaxy', 'purplelightning',
        'acidrain', 'whitenova', 'azureasteroid', 'noireclipse'
    ]
    terrain = {
        'road': 0, 'shoal': 0, 'bridge': 0, 'river': 0, 'pipe': 0, 'sea': 0,
        'reef': 1, 'plain': 1,
        'wood': 2,
        'building': 3, 'silo': 3,
        'mountain': 4, 'hq': 4
    }
    produce = {
        'base': 1, 'port': 2, 'airport': 3  # airport after port so it overwrites it. doesn't check the whole string!
    }
    repairing = {
        'city': 1, 'base': 1, 'hq': 1, 'port': 2, 'airport': 3
    }
    owners = {
        'neutral': 0, #todo
    }
    access = {
        'road': 0, 'shoal': 4, 'bridge': 0, 'river': 3, 'pipe': 6, 'piperubble': 0, 'sea': 5,  # rubble after pipe
        'reef': 5, 'plain': 1,
        'wood': 2,
        'building': 0, 'silo': 0,
        'mountain': 3, 'hq': 0
    }  # 0: road, 1: plain, 2: wood, 3: river, 4: shoal, 5: sea, 6: pipe

    s = TS_terrainIdToName[str(idn)]

    ownedby = 0
    for e in armies:
        if e in s:
            ownedby = owners[e]
            s.removeprefix(ownedby)
            break
    # todo would it be better to have every terrain refer to an array with all the deets in? mayb after owner is removed

    stars = 3
    accessibility = 0
    for e in terrain:  # terrain misses all building types  # todo port is special case. sea can go on port.
        if e in s:
            stars = terrain[e]
            accessibility = access[e]

    production = 0  # 0 none, 1 base, 2 port, 3 airport
    for e in produce:
        if e in s:
            production = produce[e]

    repair = 0  # 0 none, 1 ground, 2 sea, 3 air
    for e in repairing:
        if e in s:
            repair = repairing[e]
    return ownedby, stars, accessibility, production, repair
