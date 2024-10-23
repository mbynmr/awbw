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

from customclasses import WinError, CustomError
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

    P1 = Player()  # make 2 players to take each turn
    P2 = Player()

    with open('replays/ai/' + '_'.join([str(e).zfill(2) for e in time.localtime()[0:6]]) + '.txt', 'w') as replayfile:
        # save replay file
        replayfile.write(mp + '\n')
        replayfile.write(str(E.p1) + '\n')
        replayfile.write(str(E.p2) + '\n')
        replayfile.write(str(rng) + '\n')

        win = 0
        turn = 0
        move1 = 0
        move2 = 0
        for _ in tqdm(range(int(1e5))):  # 1e5 moves should be enough to finish a game! xD
            if turn % 2 == 0:
                action, pos1, pos2, pos3, unit = P1.ask_brain(E.p1, E.p2, E.map_info)
                move1 += 1
            else:
                action, pos1, pos2, pos3, unit = P2.ask_brain(E.p2, E.p1, E.map_info)  # swap p1 and p2
                move2 += 2

            try:
                match action:
                    case 'turn_end':
                        E.turn_end()
                        turn += 1
                    case 'cop':
                        E.power(1)
                    case 'scop':
                        E.power(2)
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
            except CustomError:
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
                    break


class Player:
    def __init__(self):
        self.win = 0  # 0 = ongoing, 1 = win, 2 = loss
        # self.actions = {'cop':0.01, 'scop':0.02, 'unload':0.05, 'move':0.25, 'hide':0.45, 'fire':0.65, 'repair':0.68, 'delete_coords':0.69, 'build':0.995, 'turn_end':1}
        self.actions = ['cop', 'scop', 'unload', 'move', 'hide', 'fire', 'repair', 'delete_coords', 'build', 'turn_end']
        self.action_intervals = [0.01, 0.02, 0.05, 0.25, 0.45, 0.65, 0.68, 0.69, 0.995, 1]
        self.units = [
            'inf', 'mech', 'tank', 'arty', 'apc', 'aa', 'med', 'neo', 'mega', 'rocket', 'recon', 'missile', 'pipe',
            'bboat', 'lander', 'carrier', 'cruiser', 'sub', 'bship',
            'bcopter','tcopter', 'bomber', 'fighter', 'stealth', 'bbomb'
        ]  # units sorted by movement type
        # self.genomeInputs = 4
        # self.genomeOutputs = 1
        # self.brain = Genome(self.genomeInputs, self.genomeOutputs)

    def ask_brain(self, p1, p2, map_info):
        # self.turns
        # self.p1 (contains updated units and stats and money and charge etc)
        # self.p2
        # self.map_info
        action = np.random.random()  #  [turn_end, scop, cop, build, move, fire, repair, hide, unload, delete_coords]
        coords1 = (np.random.random(), np.random.random())
        coords2 = (np.random.random(), np.random.random())
        coords3 = (np.random.random(), np.random.random())
        unit = np.random.random()
        # brain always makes action and 3 coords and unit (8 numbers in the interval 0-1, not inclusive of 1 itself)
        return self.convert_brain_return(action, coords1, coords2, coords3, unit, map_info[0].shape)

    def convert_brain_return(self, action, coords1, coords2, coords3, unit, shape):
        for i in range(len(self.action_intervals)):
            if self.action_intervals[i] >= action:
                action = self.actions[i]
                break
        # if type(action) is not str:
        #     raise ValueError("action didn't get chosen somehow")
        unit = self.units[int(unit * len(self.units))]  # equally weighted. let the ai figure this out itself :>
        coords1 = (int(coords1[0] * shape[0]), int(coords1[1] * shape[0]))
        coords2 = (int(coords2[0] * shape[0]), int(coords2[1] * shape[0]))
        coords3 = (int(coords3[0] * shape[0]), int(coords3[1] * shape[0]))
        return action, coords1, coords2, coords3, unit


class Genome:
    def __init__(self, a, b):
        x = 1
        # save genome details to "ai stuff" folder
