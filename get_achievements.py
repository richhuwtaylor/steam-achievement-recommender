import requests
from tqdm import tqdm
import datetime
import sqlite3
from config import Config

def get_player_achievements(api_key, steam_id, appid):
    """
    Get achievements for a specific player and game.

    Parameters:
    - api_key (str): Steam API key.
    - steam_id (str): Steam ID of the player.
    - appid (str): Steam App ID of the game.

    Returns:
    - list of dict: A list of dictionaries containing achieved achievements with 'apiname' and 'unlocktime'.
    """
    url = f"http://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v0001/?appid={appid}&key={api_key}&steamid={steam_id}"
    response = requests.get(url)
    
    achievements = []

    if response.status_code == 200:
        player_stats = response.json().get('playerstats', {})
        for achievement in player_stats.get('achievements', []):
            if achievement.get('achieved') == 1:
                achievements.append({
                    'apiname': achievement.get('apiname'),
                    'unlocktime': achievement.get('unlocktime')
                })

    return achievements

def save_player_achievements_to_sqlite(db_name, achievements, steam_id, appid):
    """
    Save player achievements to a SQLite database.

    Parameters:
    - db_name (str): Name of SQLite database.
    - achievements (list of dict): List of dictionaries containing achieved achievements.
    - steam_id (str): Steam ID of the player.
    - appid (str): Steam App ID of the game.

    Returns:
    - bool: True if successful, False otherwise.
    """
    current_time = datetime.datetime.now()

    if achievements:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS achievement (
                steamid TEXT,
                appid INTEGER,
                apiname TEXT,
                unlocked INTEGER,
                retrieved TIMESTAMP,
                PRIMARY KEY (steamid, appid, apiname)
            )
        ''')
        
        for achievement in achievements:
            cursor.execute('''
                INSERT OR IGNORE INTO achievement (steamid, appid, apiname, unlocked, retrieved)
                VALUES (?, ?, ?, ?, ?)
            ''', (steam_id, appid, achievement.get('apiname'), achievement.get('unlocktime'), current_time))
        
        conn.commit()
        conn.close()
        
        return True
    
    else:
        return False

def get_achievements_for_appid(api_key, db_name, appid, n_steam_ids: 10000):
    """
    Retrieve and save achievements for a given game and a number of Steam IDs.

    Parameters:
    - api_key (str): Steam API key.
    - db_name (str): Name of SQLite database.
    - appid (str): Steam App ID of the game.
    - n_steam_ids (int, optional): Number of Steam IDs to retrieve. Default is 10000.

    Returns:
    - None
    """
    if not appid:
        raise ValueError("AppID is not supplied.")
    
    try:
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
                    achievements = get_player_achievements(api_key, steam_id, appid)
                    save_success = save_player_achievements_to_sqlite(db_name, achievements, steam_id, appid)
                    if save_success:
                        pbar.update(1)
                        unique_steam_ids.add(steam_id)

            cursor = data['cursor']

        pbar.close()

        if unique_steam_ids:
            print(f"Achievements retrieval and storage for {len(unique_steam_ids)} Steam IDs completed.")
        else:
            print("No Steam IDs were retrieved. Exiting.")

    except Exception as e:
        print(f"Error: {e}")
        raise

    return None

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2 or len(sys.argv) > 4:
        print("Usage: python get_achievements.py <appid> [num_steam_ids_to_retrieve]")
    else:
        appid = sys.argv[1]
        num_steam_ids_to_retrieve = int(sys.argv[2]) if len(sys.argv) == 3 else 10000
        
        api_key = Config.STEAM_API_KEY
        if api_key is None:
            raise ValueError("API key not found in the configuration.")
        
        db_name = Config.DB_NAME
        if db_name is None:
            raise ValueError("DB_NAME not found in the configuration.")
        
        get_achievements_for_appid(api_key, db_name, appid, num_steam_ids_to_retrieve)
