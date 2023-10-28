import datetime
import json
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import random
import concurrent.futures
from dataclasses import dataclass
import argparse


@dataclass
class Item:
    sport_league: str = (
        ""  # sport as we classify it, e.g. baseball, basketball, football
    )
    event_date_utc: str = ""  # date of the event, in UTC, ISO format
    team1: str = ""  # team 1 name
    team2: str = ""  # team 2 name
    pitcher: str = ""  # optional, pitcher for baseball
    period: str = ""  # full time, 1st half, 1st quarter and so on
    line_type: str = (
        ""  # whatever site reports as line type, e.g. moneyline, spread, over/under
    )
    price: str = ""  # price site reports, e.g. '-133' or '+105'
    side: str = ""  # side of the bet for over/under, e.g. 'over', 'under'
    team: str = (
        ""  # team name, for over/under bets this will be either team name or total
    )
    spread: float = 0.0  # for handicap and over/under bets, e.g. -1.5, +2.5
    


def get_sport_league(row):
    try:
        # Get the a ref equal as trend-spotter
        a = row.find_element(By.TAG_NAME, "h2")
        print(a)
        # get the href of it
        href = a.get_attribute("href")
        print(href)
        # get the text of it
        text = href.split("?f=")[1]
    except:
        text = None

    return text


def clean_items(items):
    new_items = items
    # Create a list to store the indices of "N/A" values
    na_indices = []

    
    if "DRAW" in new_items:
        draw_item = items[items.index("DRAW")]
        items.pop(items.index("DRAW") + 1)
        items.remove(draw_item)
        
    # Iterate over items to detect "N/A" values and save their indices
    for index, item in enumerate(new_items):
        if "N/A" in item:
            na_indices.append(index)

    # Iterate over the saved indices in reverse order and insert "N/A" values after each index
    for index in reversed(na_indices):
        new_items.insert(index + 1, "N/A")
        print(f"Added 'N/A' to index {index + 1}")


    last_tem = new_items[-1]
    new_items.remove(last_tem)

    return new_items


# Function to safely parse price
def parse_price(price):
    if price == "N/A" or price == "":
        return None
    if " " in price:
        return float(price.split(" ")[1])
    if "." in price:
        return float(price)
    if price.startswith("+"):
        return int(price[1:])
    if price.startswith("-"):
        return -int(price[1:])
    if not price.isnumeric():
        return None
    return int(price)


def create_m1_and_m2(items, period, iso_8601_date_time, args):
    price = parse_price(str(items[2]))

    if price:
        ml_1 = Item(
            sport_league=items[-2],
            event_date_utc=iso_8601_date_time,
            team1=items[1],
            team2=items[7],
            pitcher="",
            period=period,
            line_type="moneyline",
            price=items[2],
            side=items[1] if price > 0 else items[7],
            team=items[1] if price > 0 else items[7],
            spread=0,
        )
    elif not args.handle_na:
        ml_1 = Item(
            sport_league=items[-2],
            event_date_utc=iso_8601_date_time,
            team1=items[1],
            team2=items[7],
            pitcher="",
            period=period,
            line_type="moneyline",
            price=items[2],
            side="N/A",
            team="N/A",
            spread=0,
        )

    price = parse_price(str(items[8]))

    if price:
        ml_2 = Item(
            sport_league=items[-2],
            event_date_utc=iso_8601_date_time,
            team1=items[1],
            team2=items[7],
            pitcher="",
            period=period,
            line_type="moneyline",
            price=items[8],
            side=items[1] if price > 0 else items[7],
            team=items[1] if price > 0 else items[7],
            spread=0,
        )
    elif not args.handle_na:
        ml_2 = Item(
            sport_league=items[-2],
            event_date_utc=iso_8601_date_time,
            team1=items[1],
            team2=items[7],
            pitcher="",
            period=period,
            line_type="moneyline",
            price=items[8],
            side="N/A",
            team="N/A",
            spread=0,
        )
    return ml_1, ml_2


def create_spread1_and_spread2(items, period, iso_8601_date_time, args):
    price = parse_price(str(items[3]))

    if price:
        spread_1 = Item(
            sport_league=items[-2],
            event_date_utc=iso_8601_date_time,
            team1=items[1],
            team2=items[7],
            pitcher="",
            period=period,
            line_type="spread",
            price=items[4].replace("(", "").replace(")", ""),
            side=items[1] if price > 0 else items[7],
            team=items[1] if price > 0 else items[7],
            spread=price,
        )

        price = parse_price(str(items[9]))

        spread_2 = Item(
            sport_league=items[-2],
            event_date_utc=iso_8601_date_time,
            team1=items[1],
            team2=items[7],
            pitcher="",
            period=period,
            line_type="spread",
            price=items[10].replace("(", "").replace(")", ""),
            side=items[1] if price > 0 else items[7],
            team=items[1] if price > 0 else items[7],
            spread=price,
        )

    elif not args.handle_na:
        price = "N/A"
        spread_1 = Item(
            sport_league=items[-2],
            event_date_utc=iso_8601_date_time,
            team1=items[1],
            team2=items[7],
            pitcher="",
            period=period,
            line_type="spread",
            price=price,
            side=price,
            team=price,
            spread=price,
        )
        spread_2 = Item(
            sport_league=items[-2],
            event_date_utc=iso_8601_date_time,
            team1=items[1],
            team2=items[7],
            pitcher="",
            period=period,
            line_type="spread",
            price=price,
            side=price,
            team=price,
            spread=price,
        )
    return spread_1, spread_2


def create_over_under1_and_over_under2(items, period, iso_8601_date_time, args):
    string_price = items[5]
    if " " in string_price:
        price = parse_price(str(string_price.split(" ")[1]))
    else:
        price = parse_price(str(string_price))
    if price:
        over_under_1 = Item(
            sport_league=items[-2],
            event_date_utc=iso_8601_date_time,
            team1=items[1],
            team2=items[7],
            pitcher="",
            period=period,
            line_type="over/under",
            price=items[6].replace("(", "").replace(")", ""),
            side="over" if "O" in items[5] else "under",
            team="total",
            spread=price,
        )

        price = parse_price(str(items[11].split(" ")[1]))

        over_under_2 = Item(
            sport_league=items[-2],
            event_date_utc=iso_8601_date_time,
            team1=items[1],
            team2=items[7],
            pitcher="",
            period=period,
            line_type="over/under",
            price=items[12].replace("(", "").replace(")", ""),
            side="over" if "O" in items[11] else "under",
            team="total",
            spread=price,
        )

    elif not args.handle_na:
        price = "N/A"

        over_under_1 = Item(
            sport_league=items[-2],
            event_date_utc=iso_8601_date_time,
            team1=items[1],
            team2=items[7],
            pitcher="",
            period=period,
            line_type="over/under",
            price=price,
            side=price,
            team="total",
            spread=price,
        )

        over_under_2 = Item(
            sport_league=items[-2],
            event_date_utc=iso_8601_date_time,
            team1=items[1],
            team2=items[7],
            pitcher="",
            period=period,
            line_type="over/under",
            price=price,
            side=price,
            team="total",
            spread=price,
        )
    return over_under_1, over_under_2

# Replace your loop with concurrent execution
def process_row(row, args):
    # print(tbody.text)
    items = row.text.split("\n")

    if len(items) <= 5:
        return

    bets = []

    items = clean_items(items)

    string_period = items[0].split(" ")

    period = f"{string_period[0]} {string_period[1]}"
    
    date_time_str = items[-1]
    
    # Define a format string to match the input format
    input_format_with_date = "%I:%M %p ET (%m/%d/%Y)"
    input_format_without_date = "%I:%M %p ET"

    # Initialize date to today's date
    today_date = datetime.date.today()

    try:
        # Try parsing with date included
        date_time = datetime.datetime.strptime(date_time_str, input_format_with_date)
    except ValueError:
        try:
            # Try parsing without date
            date_time = datetime.datetime.strptime(date_time_str, input_format_without_date)
            # Add today's date as the date component
            date_time = datetime.datetime.combine(today_date, date_time.time())
        except ValueError:
            print(f"Error processing date time: {date_time_str} is in an unsupported format")

    # Format the datetime object to ISO 8601
    iso_8601_date_time = date_time.isoformat()

    print(iso_8601_date_time)

    try:
        ml_1, ml_2 = create_m1_and_m2(items, period, iso_8601_date_time, args)

    except Exception as e:
        print(f"Error processing ml_1 and ml_2: {e}")

    try:
        spread_1, spread_2 = create_spread1_and_spread2(items, period, iso_8601_date_time, args)

    except Exception as e:
        print(f"Error processing spread_1 and spread_2: {e}")

    try:
        over_under_1, over_under_2 = create_over_under1_and_over_under2(items, period, iso_8601_date_time, args)

    except Exception as e:
        print(f"Error processing over_under_1 and over_under_2: {e} {items}")

    # Print row index
    print(f"Processed row {rows.index(row)}/{len(rows)}")

    print("-----------------------------")

    bets.append(ml_1)
    bets.append(ml_2)

    bets.append(spread_1)
    bets.append(spread_2)

    bets.append(over_under_1)
    bets.append(over_under_2)

    bets_for_game = []
    for game in bets:
        game_data = {
            "sport league": game.sport_league,
            "event date (UTC)": game.event_date_utc,
            "team 1": game.team1,
            "team 2": game.team2,
            "pitcher": game.pitcher,
            "period": game.period,
            "line type": game.line_type,
            "price": game.price,
            "side": game.side,
            "team": game.team,
            "spread": game.spread,
        }
        bets_for_game.append(game_data)
    games_with_names.append(bets_for_game)



# Use different agent strings to not 
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/99.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/99.0.1158.58",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Firefox/99.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Edge/99.0.1158.58",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Safari/605.1.15",
]


if __name__ == "__main__":
    
    # Add command-line argument for handling "N/A" values
    parser = argparse.ArgumentParser(description="Scrape and process data from a website")
    parser.add_argument("-nna", "--handle_na", action="store_true", help="Do not Add 'N/A' for missing values")
    parser.add_argument("--noheadless", action="store_true", help="Disable headless mode for Chrome WebDriver")
    args = parser.parse_args()

    # Check the value of the '-na' argument
    if not args.handle_na:
        print("The -nna flag was not provided, so 'N/A' values will be added for missing values.")
    else:
        print("The -nna flag was provided, 'N/A' values will not be added.")

    # Check the value of the 'headless' argument
    if args.noheadless:
        print("Headless mode is disabled.")
    else:
        print("Headless mode is enabled.")
    
    # Randomly select a user-agent from the list
    selected_user_agent = random.choice(user_agents)

    # Initialize a Selenium WebDriver with the selected user-agent
    options = webdriver.ChromeOptions()
    options.add_argument(f"user-agent={selected_user_agent}")
    
    if not args.noheadless:
        options.add_argument("--headless")  # Enable headless mode
    driver = webdriver.Chrome(options=options)

    # Navigate to the website
    driver.get("https://veri.bet/odds-picks?filter=upcoming")

    # Wait for the data to load (you may need to adjust the wait condition)
    wait = WebDriverWait(driver, 30)  # Adjust the timeout as needed

    # Wait for the element with ID "odds-picks" to become present
    table = wait.until(EC.presence_of_element_located((By.ID, "odds-picks")))

    print("Data loaded")

    # Replace the following lines with your specific logic to extract and manipulate the table data
    table_data = []

    # Get the tbody from the table
    tbody = table.find_element(By.TAG_NAME, "tbody")


    rows = table.find_elements(By.CLASS_NAME, "col")

    # Create a dictionary to store game data with game names as keys
    games_with_names = []


    # Define the number of workers (e.g., 75% of available CPU cores)
    max_workers_percentage = 0.9
    max_workers = int(max_workers_percentage * os.cpu_count())

    # Use ThreadPoolExecutor for concurrent execution
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers * 2) as executor:
        futures = [executor.submit(process_row, row, args) for row in rows]

        # Wait for all futures to complete
        concurrent.futures.wait(futures)

    # Print the data in the format you mentioned
    for game_data in games_with_names:
        print(json.dumps(game_data, indent=4))

    # Save the data to a JSON file
    with open("parse_veri_bet_output.json", "w") as json_file:
        json.dump(games_with_names, json_file, indent=4)

    # Close the Selenium WebDriver
    driver.quit()