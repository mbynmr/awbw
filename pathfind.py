import numpy as np
import tcod as tc


def path_find(start, end, map):
    graph = tc.path.CustomGraph(map.shape)
    cost = np.array(map, dtype=np.int8)
    CARDINAL = [
        [0, 1, 0],
        [1, 0, 1],
        [0, 1, 0],
    ]
    graph.add_edges(edge_map=CARDINAL, cost=cost)
    pf = tc.path.Pathfinder(graph)
    pf.add_root(start)  # set cost of root to 0? probably not right?
    # print(pf.resolve(end))
    # print(pf.path_to(end))
    pf.resolve(end)
    return pf.distance[end]