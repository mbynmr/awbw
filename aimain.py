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


import tensorflow as tf


def test():
    x = 1


class Player:
    def __init__(self):
        self.win = 0  # 0 = ongoing, 1 = win, 2 = loss
        self.genomeInputs = 4
        self.genomeOutputs = 1  #
        self.brain = Genome(self.genomeInputs, self.genomeOutputs)


class Genome:
    def __init__(self):
        x = 1
