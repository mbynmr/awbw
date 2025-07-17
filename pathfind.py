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
    # noinspection PyTypeChecker
    graph.add_edges(edge_map=CARDINAL, cost=cost)
    pf = tc.path.Pathfinder(graph)
    pf.add_root(start)
    if end is None:
        pf.resolve()
        return pf.distance
    # print(pf.resolve(end))
    # print(pf.path_to(end))
    pf.resolve(end)  # adding "end" here just stops it doing too much searching for no reason
    return pf.distance[end]


def check_movement(access, enemy_units, tread, move, fuel, pos1, pos2):
    # 0: road, 1: plain, 2: wood, 3: river, 4: shoal, 5: sea, 6: pipe, 7: port, 8: base, 9: mountain, 10: reef
    grid = np.zeros_like(access)  # todo set all to 12? grid = np.ones_like(access) * 12
    # special = self.map_info[5]
    # # special - 0: misc, 1: pipeseam, 2: missile, 3: road, 4: plain, 5: urban, 6: lab&hq
    match tread:
        case 'tracks':
            grid = np.where(access == 0, 1, 12)  # road
            grid = np.where(access == 1, 1, grid)  # plain
            grid = np.where(access == 2, 2, grid)  # wood
            grid = np.where(access == 4, 1, grid)  # shoal
            grid = np.where(access == 7, 1, grid)  # port
            grid = np.where(access == 8, 1, grid)  # base
        case 'air':
            grid = np.where(access != 6, 1, 12)  # just not pipe :>
        case 'sea':
            grid = np.where(access == 5, 1, 12)
            grid = np.where(access == 10, 2, grid)
        case 'lander':
            grid = np.where(access == 5, 1, 12)
            grid = np.where(access == 10, 2, grid)
            grid = np.where(access == 4, 1, grid)
        case 'inf':
            grid = np.where(access == 0, 1, 12)
            grid = np.where(access == 1, 1, grid)
            grid = np.where(access == 2, 1, grid)
            grid = np.where(access == 3, 2, grid)  # river
            grid = np.where(access == 4, 1, grid)
            grid = np.where(access == 7, 1, grid)
            grid = np.where(access == 8, 1, grid)
            grid = np.where(access == 9, 2, grid)  # mtn
        case 'mech':
            grid = np.where(access == 0, 1, 12)
            grid = np.where(access == 1, 1, grid)
            grid = np.where(access == 2, 1, grid)
            grid = np.where(access == 3, 1, grid)
            grid = np.where(access == 4, 1, grid)
            grid = np.where(access == 7, 1, grid)
            grid = np.where(access == 8, 1, grid)
            grid = np.where(access == 9, 1, grid)
        case 'tyre':
            grid = np.where(access == 0, 1, 12)
            grid = np.where(access == 1, 2, grid)
            grid = np.where(access == 2, 3, grid)
            grid = np.where(access == 4, 1, grid)
            grid = np.where(access == 7, 1, grid)
            grid = np.where(access == 8, 1, grid)
        case 'pipe':
            grid = np.where(access == 6, 1, 12)

    # add enemy units as blockers
    for enemy_unit in enemy_units:
        if enemy_unit['position'][0] != -10:  # if the unit isn't in a lander
            grid[enemy_unit['position']] = 12  # set movement cost to 12 which is impossible to move in any scenario

    if pos2 is None:
        all_costs = path_find(grid, pos1)  # evaluate costs of the whole grid from start position
        all_costs = np.where(all_costs <= move, all_costs, 100)
        return np.argwhere(all_costs <= fuel)  # return indexes where movement is allowed to
    else:
        movecost = path_find(grid, pos1, pos2)
        if movecost > move:  # costs too much movement so it is impossible
            return -2
        elif movecost > fuel:
            return -3
        return movecost
