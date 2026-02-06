import math
import random
from datetime import datetime
from collections import defaultdict

from game.customerrors import CustomError


# -------------------------------------------------------------
# ELO HELPERS
# -------------------------------------------------------------

def expected_score(Ra, Rb):
    """Compute expected score for player A"""
    return 1 / (1 + 10 ** ((Rb - Ra) / 400))


def elo_change(Ra, Rb, Sa, K):
    """Compute delta Elo for player A (positive if A gains)"""
    Ea = expected_score(Ra, Rb)
    return K * (Sa - Ea)


# -------------------------------------------------------------
# RECONSTRUCTION ALGORITHM
# -------------------------------------------------------------

def is_game_possible(Ra_before, game, games_played, elo_floor=None, tol=0.5):
    """
    Check whether the game could have happened when the player
    had rating Ra_before.

    game fields:
      - R_a_after
      - R_b_after
      - result (1, 0.5, 0)
    """
    R_a_after, R_b_after, result = game

    # Correct K for game count
    K = 50 if games_played < 30 else 30

    # Step 1: infer delta from A's perspective
    observed_delta = R_a_after - Ra_before

    # Step 2: infer opponent's starting rating
    Rb_before = R_b_after - observed_delta

    # Optional: enforce minimum opponent elo floor
    if elo_floor is not None and Rb_before < elo_floor:
        return False

    # Step 3: recompute predicted delta based on Ra_before, Rb_before, result
    predicted_delta = elo_change(Ra_before, Rb_before, result, K)

    # Step 4: consistency check
    # if abs(predicted_delta - observed_delta) < 10:
    #     print(abs(predicted_delta - observed_delta))
    return abs(predicted_delta - observed_delta) <= tol


def sort_games_by_actual_order(games, elo_floor=None, tol=0.5):
    """
    games: list of tuples (R_a_after, R_b_after, result)
    Returns: ordered list of games
    """

    i = 0
    while 1:  # return is the only exit
        i += 1
        try:
            # unsorted_games = np.random.shuffle(games.copy())
            unsorted_games = games.copy()
            ordered = []
            indexes = []

            Ra = 800  # initial rating
            games_played = 0

            while unsorted_games:

                # Check which games could occur at current Ra
                possible = []
                for g in unsorted_games:
                    if is_game_possible(Ra, g, games_played, elo_floor, tol):
                        possible.append(g)

                if not possible:
                    raise CustomError(
                        f"No consistent next game found at Ra={Ra}, games_played={games_played}. "
                        "Input dataset may be inconsistent or tol too small."
                    )

                # If multiple possible, pick the one with the smallest rating jump.
                # This heuristically resolves ambiguous steps.
                if len(possible) > 1:
                    possible.sort(key=lambda g: abs((g[0] - Ra)))
                # chosen = possible[0]
                chosen = possible[random.choices(range(len(possible)), weights=[
                    math.exp(-0.5 * i) for i in range(len(possible))], k=1)[0]]  # inject some randomness

                # indexes.append(possible[0])
                indexes.append(games.index(chosen))
                ordered.append(chosen)
                unsorted_games.remove(chosen)

                # Update rating after chosen game
                R_a_after, R_b_after, result = chosen
                Ra = R_a_after
                games_played += 1

            print(f"completed on atteem {i}")
            return ordered, indexes
        except CustomError:
            continue


# # -------------------------------------------------------------
# # Example usage
# # -------------------------------------------------------------
#
#
# if __name__ == "__main__":
#     # Example scrambled games:
#     # Format: (player_final_elo, opponent_final_elo, result)
#     scrambled_games = [
#         (827, 773, 1),  # win
#         (812, 788, 0),  # loss
#         (800, 800, 0.5),  # draw
#     ]
#
#     ordered = sort_games_by_actual_order(scrambled_games, elo_floor=700)
#     for g in ordered:
#         print(g)


def invert_pre_elo(post_elo, opp_elo, result_raw, K):
    # Convert your result to Elo score S
    if result_raw == 1:
        S = 1.0
    elif result_raw == 0:
        S = 0.5
    else:
        S = 0.0

    lo, hi = 700, 3000
    for _ in range(40):
        mid = (lo + hi) / 2

        expected = 1 / (1 + 10 ** ((opp_elo - mid) / 400))
        predicted_post = mid + K * (S - expected)

        if predicted_post > post_elo:
            hi = mid
        else:
            lo = mid

    return (lo + hi) / 2


def reorder_with_dates(player_elo, opp_elo, result, dates,
                       allow_cross_day_swaps=False):
    n = len(player_elo)

    # Parse string dates -> date objects
    parsed_dates = [datetime.strptime(d, "%Y-%m-%d").date() for d in dates]

    # Group indices by date
    groups = defaultdict(list)
    for i, d in enumerate(parsed_dates):
        groups[d].append(i)

    # Sort the dates chronologically
    unique_dates = sorted(groups.keys())

    # Precompute estimates for all games (initial K=50)
    pre_est = [invert_pre_elo(player_elo[i], opp_elo[i], result[i], K=50)
               for i in range(n)]

    # Perform local sorting within each date group
    final_order = []
    for d in unique_dates:
        day_indices = groups[d]

        # If more than 30 games total have passed, K=30 applies—need multiple passes.
        # But since date groups are small, the effect is small.
        # First rough sort:
        day_indices.sort(key=lambda i: pre_est[i])

        # Refinement pass for K-factor (only within the day's games)
        # and only if more than 30 games overall before this group.
        for _ in range(2):
            for local_rank, i in enumerate(day_indices):
                # Compute global chronological rank approximated by final_order so far
                global_rank = len(final_order) + local_rank
                K = 50 if global_rank < 30 else 30
                pre_est[i] = invert_pre_elo(player_elo[i], opp_elo[i], result[i], K)

            day_indices.sort(key=lambda i: pre_est[i])

        final_order.extend(day_indices)

    if not allow_cross_day_swaps:
        # Just return the date-locked order
        return final_order

    # -------------------------------------------------------------
    # OPTIONAL: cross-day correction phase (rare, but powerful)
    # -------------------------------------------------------------
    # This takes the date-ordered list and does a *gentle* Elo correction pass.
    # Changes will happen only if Elo discrepancy is huge.

    indexes = final_order
    for _ in range(2):  # a couple refinement passes
        # Recompute pre_est using this ordering
        for rank, i in enumerate(indexes):
            K = 50 if rank < 30 else 30
            pre_est[i] = invert_pre_elo(player_elo[i], opp_elo[i], result[i], K)

        # Sort by: (date, pre_est)
        indexes.sort(
            key=lambda i: (parsed_dates[i], pre_est[i])
        )

    return indexes
