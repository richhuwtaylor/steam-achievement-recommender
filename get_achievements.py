import requests
import datetime
import sqlite3
from config import Config

API_KEY = Config.STEAM_API_KEY
if API_KEY is None:
    raise ValueError("API key not found in the configuration.")

def retrieve_game_schema(api_key, appid):
    """
    Fetches game information schema from the Steam API.

    Parameters:
        api_key (str): Steam API key.
        appid (int): Steam App ID of the game.

    Returns:
        dict or None: Game information schema in JSON format, or None if the request fails.
    """
    url = f"http://api.steampowered.com/ISteamUserStats/GetSchemaForGame/v2/?key={api_key}&appid={appid}&language=english"
    response = requests.get(url)

    if response.status_code == 200:
        return response.json()
    else:
        return None

def save_achievement_descriptions_to_sqlite(api_key, appid, db_file='achievements.db'):
    """
    Saves achievement descriptions to an SQLite database.

    Parameters:
        api_key (str): Steam API key.
        appid (int): Steam App ID of the game.
        db_file (str, optional): SQLite database file name. Default is 'achievements.db'.

    Returns:
        bool: True if the achievement descriptions are saved successfully, False otherwise.
    """
    game_schema = retrieve_game_schema(api_key, appid)

    if game_schema:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS achievement_descriptions (
                apiname TEXT PRIMARY KEY,
                displayName TEXT,
                description TEXT,
                retrieved TIMESTAMP
            )
        ''')

        achievements = game_schema['game']['availableGameStats']['achievements']

        for achievement in achievements:
            apiname = achievement['name']
            displayName = achievement['displayName']
            description = achievement['description']
            retrieved = datetime.datetime.now()

            cursor.execute('''
                INSERT OR REPLACE INTO achievement_descriptions (apiname, displayName, description, retrieved)
                VALUES (?, ?, ?, ?)
            ''', (apiname, displayName, description, retrieved))

        conn.commit()
        conn.close()

        return True
    else:
        return False

if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python get_achievement_descriptions.py <appid>")
    else:
        appid = sys.argv[1]
        save_success = save_achievement_descriptions_to_sqlite(API_KEY, appid)
        if save_success:
            print("Achievement descriptions saved successfully.")
        else:
            print("Failed to retrieve achievement descriptions.")
