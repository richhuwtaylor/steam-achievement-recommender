import requests
import datetime
import sqlite3
from config import Config

API_KEY = Config.STEAM_API_KEY
if API_KEY is None:
    raise ValueError("API key not found in the configuration.")

def get_achievement_descriptions(api_key, appid):
    """
    Fetches the achievement descriptions from the Steam API.

    Parameters:
        api_key (str): Steam API key.
        appid (int): Steam App ID of the game.

    Returns:
        List or None: list of achievement descriptions, or None if the request fails.
    """
    url = f"http://api.steampowered.com/ISteamUserStats/GetSchemaForGame/v2/?key={api_key}&appid={appid}&language=english"
    response = requests.get(url)

    if response.status_code == 200:
        game_schema = response.json()

        if 'game' not in game_schema or 'availableGameStats' not in game_schema['game']:
            raise ValueError("Missing 'game' or 'availableGameStats' key in the game schema.")
        
        if 'achievements' not in game_schema['game']['availableGameStats']:
            raise ValueError("Missing 'achievements' key in the game schema.")
        
        achievements = game_schema['game']['availableGameStats']['achievements']

        return achievements
    
    else:
        return None

def save_achievement_descriptions_to_sqlite(api_key, appid):
    """
    Saves achievement descriptions to an SQLite database.

    Parameters:
        api_key (str): Steam API key.
        appid (int): Steam App ID of the game.

    Returns:
        bool: True if the achievement descriptions are saved successfully, False otherwise.
    """
    achievement_descriptions = get_achievement_descriptions(api_key, appid)

    if achievement_descriptions:
        conn = sqlite3.connect(Config.DB_NAME)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS achievement_description (
                appid INTEGER,
                apiname TEXT PRIMARY KEY,
                displayName TEXT,
                description TEXT,
                hidden BOOLEAN,
                retrieved TIMESTAMP
            )
        ''')

        for achievement in achievement_descriptions:
            apiname = achievement.get('name', '')  # Use an empty string if 'name' is not available
            displayName = achievement.get('displayName', '')
            description = achievement.get('description', '')
            hidden = bool(achievement.get('hidden', 0))  # Convert to Boolean, default is 0
            retrieved = datetime.datetime.now()

            cursor.execute('''
                INSERT OR REPLACE INTO achievement_description (appid, apiname, displayName, description, hidden, retrieved)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (appid, apiname, displayName, description, hidden, retrieved))

        conn.commit()
        conn.close()

        return True
    else:
        raise ValueError("Failed to retrieve achievement descriptions from game schema.")

if __name__ == "__main__":
    import sys

    if len(sys.argv) != 2:
        print("Usage: python get_achievement_descriptions.py <appid>")
    else:
        appid = sys.argv[1]
        try:
            save_success = save_achievement_descriptions_to_sqlite(API_KEY, appid)
            if save_success:
                print("Achievement descriptions saved successfully.")
            else:
                print("Failed to retrieve achievement descriptions.")
        except ValueError as e:
            print(f"Error: {e}")
