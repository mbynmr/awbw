import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime

def fetch_monthly_matches(start_date, end_date):
    base_url = "http://awbw.mooo.com/search"
    matches = []
    page = 0

    while True:
        offset = page * 500
        url = f"{base_url}?q=Live+League+hf+after+{start_date}+before+{end_date}&offset={offset}"
        print(f"Fetching: {url}")

        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")

        rows = soup.select("tr")
        if not rows:
            break

        found = False
        for row in rows:
            players = row.select("td.pC, td.pC.l")
            ratings = row.select("td.eC")
            date = row.select_one("td.dtC")
            day = row.select_one("td.daC")
            map_name = row.select_one("td.mC a")

            if len(players) == 2 and len(ratings) == 2 and date:
                found = True
                p1 = players[0].get_text(strip=True)
                p2 = players[1].get_text(strip=True)
                r1 = ratings[0].get_text(strip=True)
                r2 = ratings[1].get_text(strip=True)
                game_date = date.get_text(strip=True)
                game_day = day.get_text(strip=True) if day else ""
                map_title = map_name.get_text(strip=True) if map_name else ""

                if "l" in players[0]["class"]:
                    winner, loser, result = p2, p1, "Win/Loss"
                elif "l" in players[1]["class"]:
                    winner, loser, result = p1, p2, "Win/Loss"
                else:
                    winner, loser, result = None, None, "Draw"

                matches.append({
                    "Player1": p1,
                    "Player2": p2,
                    "Rating1": r1,
                    "Rating2": r2,
                    "Winner": winner,
                    "Loser": loser,
                    "Result": result,
                    "Day": game_day,
                    "Map": map_title,
                    "Date": game_date,
                })

        if not found:
            break

        page += 1

    return matches


def scrape_years_to_sheets(start_year, end_year, output_file="matches_by_month_hf.xlsx"):
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        for year in range(start_year, end_year + 1):
            for month in range(1, 13):
                start_date = datetime(year, month, 1).strftime("%Y-%m-%d")
                if month == 12:
                    end_date = datetime(year + 1, 1, 1).strftime("%Y-%m-%d")
                else:
                    end_date = datetime(year, month + 1, 1).strftime("%Y-%m-%d")

                matches = fetch_monthly_matches(start_date, end_date)
                if not matches:
                    continue  # skip empty months

                df = pd.DataFrame(matches)
                sheet_name = f"{year}-{month:02d}"
                print(f"Writing {len(matches)} matches to sheet: {sheet_name}")
                df.to_excel(writer, sheet_name=sheet_name, index=False)

    print(f"Finished! Data saved to {output_file}")


if __name__ == "__main__":
    # Example: scrape from 2024 to 2025
    scrape_years_to_sheets(2023, 2025)
