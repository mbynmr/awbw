import numpy as np
import tcod as tc


def path_find(grid, start, end=None):
    graph = tc.path.CustomGraph(grid.shape)
    cost = np.array(grid, dtype=np.int8)
    CARDINAL = [
        [0, 1, 0],
        [1, 0, 1],
        [0, 1, 0],
    ]
    graph.add_edges(edge_map=CARDINAL, cost=cost)
    pf = tc.path.Pathfinder(graph)
    pf.add_root(start)  # set cost of root to 0? probably not right?
    if end is None:
        pf.resolve()
        return pf.distance
    # print(pf.resolve(end))
    # print(pf.path_to(end))
    pf.resolve(end)  # adding "end" here just stops it doing too much searching for no reason
    return pf.distance[end]
