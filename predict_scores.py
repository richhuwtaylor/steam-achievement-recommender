import datetime
import os
import torch
import numpy as np
import pandas as pd
from spotlight.interactions import Interactions
from data_utils import interactions_to_sequences, load_achievement_descriptions_from_sqlite    
from get_achievements import get_player_achievements
from config import Config

def load_latest_model(appid):
    """
    Load the latest trained model for a given appid.

    Parameters:
        appid (str): Steam App ID of the game.
        model_dir (str, optional): Directory where models are saved. Default is 'models'.

    Returns:
        spotlight.sequence.implicit.ImplicitSequenceModel: Loaded model.
    """
    models_for_appid = [model for model in os.listdir(Config.MODEL_DIR) if model.startswith(f"{appid}_")]
    if not models_for_appid:
        raise FileNotFoundError(f"No models found for appid {appid}. Train a model first.")

    # Extract datetime from model names
    model_datetimes = [datetime.datetime.strptime('_'.join(model.split('_')[1:]), '%Y-%m-%d_%H-%M-%S') for model in models_for_appid]
    
    most_recent_model_datetime = max(model_datetimes)
    most_recent_model_index = model_datetimes.index(most_recent_model_datetime)
    most_recent_model = models_for_appid[most_recent_model_index]
    
    model_path = os.path.join(Config.MODEL_DIR, most_recent_model)
    model = torch.load(model_path)

    return model

def get_ranked_scores_for_user(model, user_sequence, achievement_name_dict, exclude_last_item=False):
    """
    Retrieves ranked scores for a user using a specified model.

    Parameters:
        model (spotlight.sequence.implicit.ImplicitSequenceModel): Trained sequence model.
        user_sequence (numpy.ndarray): User's sequence.
        achievement_name_dict (dict): Dictionary mapping achievement names to internal IDs.
        exclude_last_item (bool): Whether to exclude the last item in the user's sequence.

    Returns:
        pd.Series: Ranked scores for achievements.
    """
    # Items the user has already interacted with
    user_items = np.trim_zeros(user_sequence, 'f')
    
    # Items not in the user's set that we want to retrieve scores for
    if exclude_last_item:
        desired_items = [key for key, value in achievement_name_dict.items() if value not in user_items[:-1]]
    else:
        desired_items = [key for key, value in achievement_name_dict.items() if value not in user_items[:]]

    scores = model.predict(sequences=user_sequence)
    scores_series = pd.Series(scores[1:], index=achievement_name_dict.keys(), name='ScoresSeries')
    scores_series = scores_series.loc[desired_items]
    scores_series = scores_series.sort_values(ascending=False)

    return scores_series

def convert_achievements_to_interactions(achievements_list, achievement_name_dict):
    """
    Convert a list of achievement dictionaries to a pandas DataFrame and then to a Spotlight Interactions object.

    Parameters:
    - achievements_list (list of dict): List of dictionaries containing achievements with 'apiname' and 'unlocktime'.
    - achievement_name_dict (dict): Dictionary mapping achievement names to internal IDs.

    Returns:
    - spotlight.interactions.Interactions: Spotlight Interactions object.
    """
    data = []

    # We use 1 for the user_id for this user since we're only using this function
    # to help prepare a sequence for prediction rather than training
    for achievement in achievements_list:
        data.append({
            'steam_id': 1,
            'api_name': achievement['apiname'],
            'timestamp': achievement['unlocktime']
        })

    df_interactions = pd.DataFrame(data)
    df_interactions['achievement_name'] = df_interactions['api_name'].map(achievement_name_dict)
    df_interactions = df_interactions.dropna()
    df_interactions = df_interactions[df_interactions['timestamp'] != 0]

    interactions = Interactions(
        user_ids=df_interactions['steam_id'].values.astype(np.int32),
        item_ids=df_interactions['achievement_name'].values.astype(np.int32),
        timestamps=df_interactions['timestamp'].values.astype(np.int32)
    )

    return interactions

def join_scores_with_descriptions(scores_series, achievement_descriptions):
    """
    Join scores series with achievement descriptions.

    Parameters:
        scores_series (pd.Series): Series of scores for achievements.
        achievement_descriptions (pd.DataFrame): DataFrame with columns 'apiname' and 'description'.

    Returns:
        pd.DataFrame: DataFrame with columns 'apiname', 'score', and 'description'.
    """
    # Merge scores with descriptions and sort the DataFrame
    df = pd.merge(scores_series.rename('score'), achievement_descriptions, left_index=True, right_on='apiname', how='left')
    df = df.sort_values(by='score', ascending=False).reset_index(drop=True)

    return df[['apiname', 'score', 'displayName', 'description']]

def predict_scores(steam_id, appid):
    """
    Predict and return scores for achievements of a specific player and game.

    Parameters:
        steam_id (str): Steam ID of the player.
        appid (str): Steam App ID of the game.

    Returns:
        pd.Series: Predicted scores for achievements.
    """

    # Load the latest trained model
    model = load_latest_model(appid)

    # Retrieve dictionary of achievement names onto internal IDs used by the model
    achievement_name_dict  = {v: k for k, v in model.achievement_name_dict.items()}
    max_sequence_length = len(achievement_name_dict.keys())

    # Retrieve achievements for the player from the Steam API
    api_key = Config.STEAM_API_KEY
    if api_key is None:
        raise ValueError("API key not found in the configuration.")

    player_achievements = get_player_achievements(api_key, steam_id, appid)

    if player_achievements:
        missing_achievements = set(achievement_name_dict.keys()) - set([achievement['apiname'] for achievement in player_achievements])

        if missing_achievements:
            interactions = convert_achievements_to_interactions(player_achievements, achievement_name_dict)

            # Convert player achievements to sequence
            player_sequence = interactions_to_sequences(interactions, max_sequence_length).sequences[0]

            # Get ranked scores for the player using the model
            scores_series = get_ranked_scores_for_user(model, player_sequence, achievement_name_dict)

            return scores_series
        
        else:
            print(f"Player with steam_id {steam_id} already has all achievements for appid {appid}.")

    else:
        print(f"No achievements found for player with steam_id {steam_id} for appid {appid}.")
        return pd.Series()

if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: python predict_scores.py <steam_id> <appid>")
    else:
        steam_id = sys.argv[1]
        appid = sys.argv[2]
        predicted_scores = predict_scores(steam_id, appid)
        achievement_descriptions = load_achievement_descriptions_from_sqlite(appid)
        scores_with_descriptions = join_scores_with_descriptions(predicted_scores, achievement_descriptions)
        print(scores_with_descriptions)
