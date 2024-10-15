

def check_move(unit, desired_position, stars, access, special):
    if unit['move'] < 0:
        return False
    # yea screw fog. fog gna be too painful :>


def move(unit, desired_position, desired_action, stars, access, special):
    if check_move(unit, desired_position, stars, access, special):
        unit['position'] = desired_position
        unit['move'] = 0  # set 0 move so it can't move anymore!
        # set fuel
        # set terrain stars + bonuses

        # todo desired_action
        # wait: shouldn't be anything to do :>
        # captures: tell co to increase value (city) or Av (com) or win (hq)
        # attacks: run fire.py ig
        # delete: figure that out. needs to be done before move tho.
    else:
        raise ValueError("can't move there bb sry")  # todo
