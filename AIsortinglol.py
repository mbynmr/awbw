import math


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
    return abs(predicted_delta - observed_delta) <= tol


def sort_games_by_actual_order(games, elo_floor=None, tol=0.5):
    """
    games: list of tuples (R_a_after, R_b_after, result)
    Returns: ordered list of games
    """

    unsorted_games = games.copy()
    ordered = []
    indexes = []

    Ra = 800  # initial rating
    games_played = 0

    while unsorted_games:
        possible = []

        # Check which games could occur at current Ra
        for g in unsorted_games:
            if is_game_possible(Ra, g, games_played, elo_floor, tol):
                possible.append(g)

        if not possible:
            raise ValueError(
                f"No consistent next game found at Ra={Ra}, games_played={games_played}. "
                "Input dataset may be inconsistent or tol too small."
            )

        # If multiple possible, pick the one with the smallest rating jump.
        # This heuristically resolves ambiguous steps.
        if len(possible) > 1:
            possible.sort(key=lambda g: abs((g[0] - Ra)))
        chosen = possible[0]

        indexes.append(possible[0])
        ordered.append(chosen)
        unsorted_games.remove(chosen)

        # Update rating after chosen game
        R_a_after, R_b_after, result = chosen
        Ra = R_a_after
        games_played += 1

    return ordered, indexes


# -------------------------------------------------------------
# Example usage
# -------------------------------------------------------------


if __name__ == "__main__":
    # Example scrambled games:
    # Format: (player_final_elo, opponent_final_elo, result)
    scrambled_games = [
        (827, 773, 1),  # win
        (812, 788, 0),  # loss
        (800, 800, 0.5),  # draw
    ]

    ordered = sort_games_by_actual_order(scrambled_games, elo_floor=700)
    for g in ordered:
        print(g)
