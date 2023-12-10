import sqlite3
import pandas as pd
from config import Config

def load_achievement_descriptions_from_sqlite(appid):
    """
    Loads achievement descriptions from an SQLite database.

    Parameters:
        appid (str): Steam App ID of the game.

    Returns:
        pd.DataFrame: DataFrame containing achievement descriptions.
    """
    conn = sqlite3.connect(Config.DB_NAME)
    query = f"SELECT * FROM achievement_description WHERE appid = {appid}"
    df_achievements = pd.read_sql(query, conn)
    conn.close()

    return df_achievements

def load_interactions_from_sqlite(appid):
    """
    Loads player-achievement interactions from an SQLite database.

    Parameters:
        appid (str): Steam App ID of the game.

    Returns:
        pd.DataFrame: DataFrame containing player-achievement interactions.
    """
    conn = sqlite3.connect(Config.DB_NAME)
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



