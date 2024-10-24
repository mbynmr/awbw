"""
Genetic algorithms work like this:
    Come up with a simple way to describe your AI's code. In the example video, it's described as an extremely simple neural network.
    Create one or more initial AI. You could do this by generating completely random descriptions, or you could try hand-coding a basic one.
    Start the training loop:
    a. Create many "mutated" copies of the AI, by randomly tweaking the description. These are the AI's "offspring".
    b. Have each offspring run the game, and give it a score.
    c. Keep the N highest-scoring offspring around for the next generation.
You can use a genetic algorithm on any system which can be randomly "mutated" in small ways, adding up to big mutations over time.
"""

# That depends on the game but it's either faking keyboard inputs
# or instead of processing input, you process the AI instead

# options for the type of ai:
# play against itself (advantage: can be better than humans, disadvantage: much harder)
# learn from high level GL match replays (advantage: much easier, disadvantage: only beats good players on a good day)
# why is playing itself hard? I don't think it is. get one version to play 1000 games and train itself on win/loss
# then use better trained version to do the same again?

# reward:
#  ++++winning in as few turns as possible
#  +++winning
#  ++unit count advantage (prevents stalls where ai just builds units and hides them)
#  ++income advantage
#  +moving
#  +attacking
# punish:
#  ----losing
#  0.00001-CustomError (very very very small punish, we want it to try things before assuming it won't work)
# training idea: a set of stages it has to pass before moving on to the next
# give it a nearly winning position (like 10 of them?) where they just cap hq to win or kill 1 unit
# then level it up, make it so it needs 2 turns to win.
# then add some resistance (inf on hq to kill, then cap)
# then make it a few turns before victory
# then make it play itself from turn 0 lots of times on a few maps
# then let it choose CO and repeat
# play me!
# profit??
# play against sensei a lot bcus the "calcs" the ai has won't account for 9hp inf/mech spawns: spawns are always 10hp

# total things to interract with:

# --inputs to engine--
# scop
# cop
# ----
# build
# build options
# ----
# 3 sets of x,y (current, desired, target)
# display move (instantly returns possible "desired" for "current" which should b useful)
# ----
# join/load/cap + move
# hide/unhide + move
# fire + move
# repair + move
# unload???
# delete
# ----
# end turn (saves full game state to a file)

# --outputs from engine--
# self.win  (0 = ongoing, 1 = win, 2 = loss)
# self.turns
# self.p1 (contains updated units and stats and money and charge etc)
# self.p2
# self.map_info


# 3 sets of x,y should probably be 1 set of x,y for current, and 2 sets of x,y deltas for desired and target.
# apart from powers and end turn, everything needs current coords.
# unit move/del options need other 2 coords.

# when the ai reads in self.p1['units'][0]['hp'] it should be garbled to be 1-10hp instead of full info 0-99hp

# train on replays (won't be better than humans)
# train on itself

# set start state for a given map
# text file goes through every operation performed (e.g. "cap/wait func" "pos1" "pos2" every line is an action)

import platform
import time
import numpy as np
from tqdm import tqdm
import tensorflow as tf

from customerrors import CustomError
from engine import Engine
from co import co_maker


def test():
    if platform.system() == 'Linux':
        mp = r"/home/nathaniel/PycharmProjects/awbw/maps/"
    else:
        mp = r"maps/"
    # mp = mp + "Last Vigil.txt"
    mp = mp + "training maps/simple/simple.txt"
    rng = np.random.randint(1e9)
    E = Engine(mp, co_maker('jake', 'purplelightning'), co_maker('jess', 'yellowcomet'), rng)
    E.load_map()
    unit_limit = E.map_rules['unitl']
    map_info = E.map_info

    #{'unitl':0, 'capturel': 0, 'dayl': 0, 'fog': 0, 'weather': 0, 'fundstart': 0, 'banned': []}
    # todo integrate map rules into the array so every input lets it know what the rules are :>
    # probably just another slice?

    mps = mp.split('maps/')
    load = None  # file path to load weights from
    save = mps[0] + 'ai stuff/' + mps[1].split('.txt')[0]  # file path to save weights to
    # make 2 players to take each turn
    P1 = Player(unit_limit, map_info[0].shape, load)
    P2 = Player(unit_limit, map_info[0].shape, load)

    with open('replays/ai/' + '_'.join([str(e).zfill(2) for e in time.localtime()[0:6]]) + '.txt', 'w') as replayfile:
        # save replay file
        replayfile.write(mp + '\n')
        replayfile.write(str(E.p1) + '\n')
        replayfile.write(str(E.p2) + '\n')
        replayfile.write(str(rng) + '\n')

        win = do_turns(E, P1, P2, replayfile)

    # if you win your weights get saved
    if win == E.p1['army']:
        P1.brain.save_weights(save)
        print("p1 win")
        # P2.delete_weights()  # not needed
    elif win == E.p2['army']:
        P2.brain.save_weights(save)
        print("p2 win")
    else:
        print("neither won. sadge")


def do_turns(E, P1, P2, replayfile):
    turn = 0
    move1 = 0
    move2 = 0
    for _ in tqdm(range(int(1e4))):  # 1e5 moves should be enough to finish a game! xD
        if turn % 2 == 0:
            action, pos1, pos2, pos3, unit = P1.ask_brain(E.p1, E.p2, E.map_info)
            move1 += 1
        else:
            action, pos1, pos2, pos3, unit = P2.ask_brain(E.p2, E.p1, E.map_info)  # swap p1 and p2
            move2 += 1

        try:
            match action:
                case 'turn_end':
                    E.turn_end()
                    turn += 1
                case 'cop':
                    E.power(1)
                    # todo small reward?
                case 'scop':
                    E.power(2)
                    # todo small reward?
                case 'unload':
                    E.unload(pos1, pos2, pos3[0])  # choice of unit to unload, hard,
                case 'move':
                    E.action(pos1, pos2, desired_action='wait')
                case 'hide':
                    E.action(pos1, pos2, desired_action='hide')
                case 'fire':
                    E.action(pos1, pos2, desired_action='fire', target_pos=pos3)
                case 'repair':
                    E.action(pos1, pos2, desired_action='repair', target_pos=pos3)
                case 'delete_coords':
                    E.delete_coords(pos1)
                case 'build':
                    E.build(pos1, unit)
                    # todo small reward?
        except CustomError:  # CustomError means the move was invalid for some reason (reason is stored by the error)
            pass  # could add move to make moves that are invalid cost more overall moves than normal moves.
        else:  # if the action goes through alright (no CustomError)
            if action == 'build':
                replayfile.write(f"build {pos1[1]} {pos1[0]} {unit}" + '\n')
            elif action == 'turn_end':
                replayfile.write('turn_end' + '\n')
            else:
                replayfile.write(f"{action} {pos1[1]} {pos1[0]} {pos2[1]} {pos2[0]} {pos3[1]} {pos3[0]}" + '\n')
        finally:
            win = E.winner
            if win != 0:
                print(f"omg a win??? army {win} wins")
                return win


class Player:
    def __init__(self, unit_limit, map_shape, load):
        self.win = 0  # 0 = ongoing, 1 = win, 2 = loss
        self.actions = ['cop', 'scop', 'unload', 'move', 'hide', 'fire', 'repair', 'delete_coords', 'build', 'turn_end']
        # make move/fire/build have a wider range than end_turn/cop/scop with action_intervals
        self.action_intervals = [0.01, 0.02, 0.05, 0.25, 0.45, 0.65, 0.68, 0.69, 0.995, 1]
        self.units = [
            'inf', 'mech', 'tank', 'arty', 'apc', 'aa', 'med', 'neo', 'mega', 'rocket', 'recon', 'missile', 'pipe',
            'bboat', 'lander', 'carrier', 'cruiser', 'sub', 'bship',
            'bcopter','tcopter', 'bomber', 'fighter', 'stealth', 'bbomb'
        ]  # units sorted by movement type
        self.treads = [
            'inf', 'mech', 'treads', 'treads', 'treads', 'treads', 'treads', 'treads', 'treads',
            'tyre', 'tyre', 'tyre',
            'pipe',
            'lander', 'lander', 'sea', 'sea', 'sea', 'sea',
            'air', 'air', 'air', 'air', 'air', 'air'
        ]  # movement type in the same ordering as self.units
        self.armies = [
            'neutral', 'amberblaze', 'blackhole', 'bluemoon', 'browndesert', 'greenearth', 'jadesun', 'orangestar',
            'redfire', 'yellowcomet', 'greysky', 'cobaltice', 'pinkcosmos', 'tealgalaxy', 'purplelightning',
            'acidrain', 'whitenova', 'azureasteroid', 'noireclipse'
        ]  # army names sorted the same way the site sorts them (alphabetical then updated ones)
        self.co_list = [
            'andy', 'hachi', 'jake', 'max', 'nell', 'rachel', 'sami',
            'colin', 'grit', 'olaf', 'sasha',
            'drake', 'eagle', 'javier', 'jess',
            'grimm', 'kanbei', 'sensei', 'sonja',
            'adder', 'flak', 'hawke', 'jugger', 'kindle', 'koal', 'lash', 'sturm', 'von bolt'
        ]  # co names sorted by faction then alphabetical
        self.map_shape = map_shape
        # 19 is how wide the unit details are but 3 have 2 elements (position, range, luck) so it comes out to 22
        width = 22 if self.map_shape[0] < 22 else self.map_shape[0]
        height = (unit_limit + 1) if self.map_shape[1] < (unit_limit + 1) else self.map_shape[1]
        self.arr_example = np.zeros([width, height, 2 + 6], dtype=int)  # slices: co1, co2, map0, map1, map2, ...

        brainInputs = self.arr_example.shape
        brainOutputs = 8
        self.brain = Brain(brainInputs, brainOutputs, load=load)

    def ask_brain(self, p1, p2, map_info):
        # self.turns
        # self.p1 (contains updated units and stats and money and charge etc)
        # self.p2
        # self.map_info
        # brain always makes action and 3 coords and unit (8 numbers in the interval 0-1, not inclusive of 1 itself)
        p1coints, p1unitints = self.make_arrays(p1)
        p2coints, p2unitints = self.make_arrays(p2)
        arr = np.zeros_like(self.arr_example)  # fresh array
        arr[:len(p1coints), -1, 0] = p1coints  # append co1 information to the bottom of slice 0
        arr[:len(p2coints), -1, 1] = p2coints  # append co2 information to the bottom of slice 1
        arr[:p1unitints.shape[0], :p1unitints.shape[1], 0] = p1unitints  # co1 units in slice 0
        arr[:p2unitints.shape[0], :p2unitints.shape[1], 1] = p2unitints  # co2 units in slice 1
        for i, s in enumerate(map_info):
            arr[:self.map_shape[0], :self.map_shape[1], 2 + i] = s

        brain_output = self.brain.ask(arr)  # send off to nn for a result!

        return self.convert_brain_return(brain_output, self.map_shape)

    def convert_brain_return(self, out, shape):
        for i in range(len(self.action_intervals)):
            if self.action_intervals[i] >= out[0]:
                action = self.actions[i]
                break
        # if type(action) is not str:
        #     raise ValueError("action didn't get chosen somehow")
        unit = self.units[int(out[7] * len(self.units))]  # equally weighted. let the ai figure this out itself :>
        coords1 = (int(out[1] * shape[0]), int(out[2] * shape[0]))
        coords2 = (int(out[3] * shape[0]), int(out[4] * shape[0]))
        coords3 = (int(out[5] * shape[0]), int(out[6] * shape[0]))
        return action, coords1, coords2, coords3, unit

    def make_arrays(self, p):
        coints = []
        unitints = []
        for _, (key, element) in enumerate(p.items()):  # todo no need to enumerate?
            if key == 'units':
                for u in element:
                    for _, (k, e) in enumerate(u.items()):
                        if k == 'army':
                            unitints.append(self.armies.index(e))
                        elif k == 'type':
                            unitints.append(self.units.index(e))
                        elif k == 'tread':
                            unitints.append(self.treads.index(e))
                        elif k == 'position' or k == 'range' or k == 'L':
                            unitints.append(e[0])
                            unitints.append(e[1])
                        elif k == 'hidden':
                            unitints.append(1 if e else 0)  # hidden = 1, not hidden = 0
                        elif k == 'loaded':
                            unitints.append(len(e))  # only length, uhhh? not good probably? idk.
                        else:
                            unitints.append(e)
                        # units needs reshaping. bigly. units have 19 options (0-18, len = 19)
            elif key == 'army':
                coints.append(self.armies.index(element)) # change army to number
            elif key == 'name':
                coints.append(self.co_list.index(element)) # change co name to number
            else:
                coints.append(element)  # alternative to p1 = p1.copy().pop('units')
        return coints, np.reshape(unitints, (22, -1))


class Brain:
    def __init__(self, inshape, outshape, load=None):

        # self.cp_callback = tf.keras.callbacks.ModelCheckpoint(filepath=path, save_weights_only=True, verbose=1)
        # auto save weights for long runs? 0.0

        self.model = tf.keras.models.Sequential([
            tf.keras.layers.Input(inshape),
            tf.keras.layers.Flatten(),
            tf.keras.layers.Dropout(0.6),  # set some values to 0
            tf.keras.layers.Dense(128, activation='relu', bias_initializer=tf.keras.initializers.RandomUniform()),
            tf.keras.layers.Dense(128, activation='relu', bias_initializer=tf.keras.initializers.RandomNormal(stddev=0.05)),
            tf.keras.layers.GaussianNoise(0.1),
            tf.keras.layers.Dense(128, activation='relu', bias_initializer=tf.keras.initializers.RandomNormal(stddev=0.02)),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(outshape, activation='softmax')
        ])

        if load is not None:
            self.model.load_weights(
                tf.train.latest_checkpoint(load)
            )  # load weights from file

    def ask(self, big_array):
        shape = big_array.shape
        predictions = self.model(tf.reshape(tf.convert_to_tensor(big_array), (1, *shape)))
        out = tf.nn.softmax(predictions)
        # print(out)
        # time.sleep(3/5)
        return np.array(out)[0]

    def save_weights(self, path):
        x = path + '_'.join([str(e).zfill(2) for e in time.localtime()[0:6]]) + '.ckpt'  # todo
        self.model.save_weights(path)
