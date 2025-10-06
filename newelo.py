import pandas as pd


def rebuild_leaderboard(file_path="outputs/data/spreadsheets/matches_by_month.xlsx",
                        output_file="outputs/data/spreadsheets/leaderboard_by_month.xlsx"):
    # Dictionary to hold current ratings
    player_ratings = {}

    # Store leaderboard snapshots at end of each month
    snapshots = {}

    # Load all sheets (months)
    xls = pd.ExcelFile(file_path)

    # Sort sheets chronologically (e.g., 2024-01, 2024-02, ...)
    sheets = sorted(xls.sheet_names)

    for sheet in sheets:
        print(f"Processing {sheet}")
        df = pd.read_excel(file_path, sheet_name=sheet)

        # Reverse the order (since games are saved from end to start)
        df = df[::-1].reset_index(drop=True)

        for _, row in df.iterrows():
            p1, p2 = row["Player1"], row["Player2"]
            r1, r2 = int(row["Rating1"]), int(row["Rating2"])

            # Update ratings
            player_ratings[p1] = r1
            player_ratings[p2] = r2

        # Save snapshot for this month
        leaderboard = pd.DataFrame(
            sorted(player_ratings.items(), key=lambda x: x[1], reverse=True),
            columns=["Player", "Rating"]
        )
        snapshots[sheet] = leaderboard

    # Write all monthly leaderboards into one Excel file
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        for sheet, leaderboard in snapshots.items():
            leaderboard.to_excel(writer, sheet_name=sheet, index=False)

    print(f"Leaderboards saved to {output_file}")
