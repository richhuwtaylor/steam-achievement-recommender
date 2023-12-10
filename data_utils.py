import sqlite3
import pandas as pd

def load_achievement_descriptions_from_sqlite(appid, db_file='achievements.db'):
    """
    Loads achievement descriptions from an SQLite database.

    Parameters:
        appid (str): Steam App ID of the game.
        db_file (str, optional): SQLite database file name. Default is 'achievements.db'.

    Returns:
        pd.DataFrame: DataFrame containing achievement descriptions.
    """
    conn = sqlite3.connect(db_file)
    query = f"SELECT * FROM achievement_description WHERE appid = {appid}"
    df_achievements = pd.read_sql(query, conn)
    conn.close()

    return df_achievements

def load_interactions_from_sqlite(appid, db_file='achievements.db'):
    """
    Loads player-achievement interactions from an SQLite database.

    Parameters:
        appid (str): Steam App ID of the game.
        db_file (str, optional): SQLite database file name. Default is 'achievements.db'.

    Returns:
        pd.DataFrame: DataFrame containing player-achievement interactions.
    """
    conn = sqlite3.connect(db_file)
    query = f"SELECT * FROM achievement WHERE appid = {appid}"
    df_interactions = pd.read_sql(query, conn)
    conn.close()

    return df_interactions

def interactions_to_sequences(interactions, max_sequence_length):
    return interactions.to_sequence(max_sequence_length=max_sequence_length, min_sequence_length=None, step_size=None)


