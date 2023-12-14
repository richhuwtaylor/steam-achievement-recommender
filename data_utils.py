import requests
import sqlite3
import pandas as pd

def load_interactions_from_sqlite(db_name, appid):
    """
    Loads player-achievement interactions from an SQLite database.

    Parameters:
        db_name (str): Name of SQLite database.
        appid (str): Steam App ID of the game.

    Returns:
        pd.DataFrame: DataFrame containing player-achievement interactions.
    """
    conn = sqlite3.connect(db_name)
    query = f"SELECT * FROM achievement WHERE appid = {appid}"
    df_interactions = pd.read_sql(query, conn)
    conn.close()

    return df_interactions

def interactions_to_sequences(interactions, max_sequence_length):
    """
    Convert interactions to sequences for training a sequence model.

    Parameters:
    - interactions (spotlight.interactions.Interactions): Interaction set containing user-item interactions.
    - max_sequence_length (int): Maximum length of sequences to generate.

    Returns:
    spotlight.interactions.SequenceInteractions: Sequences suitable for training a sequence model.
    """
    return interactions.to_sequence(max_sequence_length=max_sequence_length, min_sequence_length=None, step_size=None)

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

        result = [
            {
                'apiname': achievement.get('name', ''),  # Use an empty string if 'name' is not available
                'displayName': achievement.get('displayName', ''),
                'description': achievement.get('description', ''),
                'hidden': bool(achievement.get('hidden', 0)),  # Convert to Boolean, default is 0
            }
            for achievement in achievements
        ]

        return result
    
    else:
        return None



