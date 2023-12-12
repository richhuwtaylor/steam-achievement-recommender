import requests
from config import Config
from get_achievements import get_player_achievements, save_player_achievements_to_sqlite
from tqdm import tqdm
from typing import List, Optional

API_KEY = Config.STEAM_API_KEY
if API_KEY is None:
    raise ValueError("API key not found in the configuration.")

def get_steam_ids(appid: str, n_steam_ids: int = 20) -> List[str]:
    """
    Scrape unique Steam IDs associated with reviews for a given Steam game.

    Parameters:
    - appid (str): The Steam AppID of the game.
    - n_steam_ids (int, optional): The number of unique Steam IDs to retrieve.
      Default is 20.

    Returns:
    List[str]: A list of unique SteamIDs scraped from reviews.

    Raises:
    - ValueError: If AppID is not supplied.
    """
    if not appid:
        raise ValueError("AppID is not supplied.")

    cursor = '*'
    unique_steam_ids = set()

    pbar = tqdm(total=n_steam_ids, desc="Scraping Steam IDs", unit=" IDs")

    while len(unique_steam_ids) < n_steam_ids:
        reviews_url = f"https://store.steampowered.com/appreviews/{appid}?json=1&filter=recent"
        try:
            response = requests.get(reviews_url, params={'cursor': cursor})
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            print(f"Request failed: {e}")
            break
        except ValueError as e:
            print(f"Failed to parse JSON: {e}")
            break

        if data.get("success") != 1:
            print("Error: Unable to retrieve data.")
            break

        num_reviews_on_page = data['query_summary']['num_reviews']
        reviews = data['reviews']

        if num_reviews_on_page == 0 or data['cursor'] == "":
            break

        for review in reviews:
            steam_id = review['author']['steamid']
            if steam_id not in unique_steam_ids:
                achievements = get_player_achievements(API_KEY, steam_id, appid)
                save_success = save_player_achievements_to_sqlite(achievements, steam_id, appid)
                if save_success:
                    pbar.update(1)
                    unique_steam_ids.add(steam_id)

        cursor = data['cursor']

    pbar.close()

    if unique_steam_ids:
        print(f"Scraped {len(unique_steam_ids)} unique SteamIDs.")
        return list(unique_steam_ids)
    else:
        print("No Steam IDs were scraped.")
        return []

if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: python get_steam_ids.py <appid> <num_steam_ids_to_retrieve>")
    else:
        appid = sys.argv[1]
        num_steamids_to_receive = int(sys.argv[2])
        unique_steam_ids = get_steam_ids(appid, num_steamids_to_receive)
        print("Unique Steam IDs:", unique_steam_ids)
