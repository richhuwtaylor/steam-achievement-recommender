import requests
from tqdm import tqdm
import datetime
import sqlite3
from config import Config
from get_steam_ids import get_steam_ids

API_KEY = Config.STEAM_API_KEY
if API_KEY is None:
    raise ValueError("API key not found in the configuration.")

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

def save_player_achievements_to_sqlite(achievements, steam_id, appid):
    """
    Save player achievements to a SQLite database.

    Parameters:
    - achievements (list of dict): List of dictionaries containing achieved achievements.
    - steam_id (str): Steam ID of the player.
    - appid (str): Steam App ID of the game.

    Returns:
    - bool: True if successful, False otherwise.
    """
    current_time = datetime.datetime.now()

    if achievements:
        conn = sqlite3.connect(Config.DB_NAME)
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

def get_achievements_for_appid(appid, num_steam_ids_to_retrieve=10000):
    """
    Retrieve and save achievements for a given game and a number of Steam IDs.

    Parameters:
    - appid (str): Steam App ID of the game.
    - num_steam_ids_to_retrieve (int, optional): Number of Steam IDs to retrieve. Default is 10000.

    Returns:
    - None
    """
    unique_steam_ids = get_steam_ids(appid, num_steam_ids_to_retrieve)
    
    if unique_steam_ids:
        print(f"Retrieved {len(unique_steam_ids)} unique SteamIDs. Fetching achievements...")

        with tqdm(total=len(unique_steam_ids), desc="Fetching Achievements", unit=" IDs") as pbar:
            for steam_id in unique_steam_ids:
                achievements = get_player_achievements(API_KEY, steam_id, appid)
                save_success = save_player_achievements_to_sqlite(achievements, steam_id, appid)
                if save_success:
                    pbar.update(1)

        print("Achievements retrieval and storage completed.")
    else:
        print("No Steam IDs were retrieved. Exiting.")

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2 or len(sys.argv) > 4:
        print("Usage: python get_achievements.py <appid> [num_steam_ids_to_retrieve]")
    else:
        appid = sys.argv[1]
        num_steam_ids_to_retrieve = int(sys.argv[2]) if len(sys.argv) == 3 else 10000
        get_achievements_for_appid(appid, num_steam_ids_to_retrieve)
