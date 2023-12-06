import os
import numpy as np
import pandas as pd
from spotlight.cross_validation import random_train_test_split
from spotlight.evaluation import sequence_mrr_score
from spotlight.interactions import Interactions
from spotlight.sequence.implicit import ImplicitSequenceModel
from tqdm import tqdm
import sqlite3
import datetime

def save_model(model, appid, model_dir='models'):
    """
    Saves a trained model in the 'models' directory with a specific format.

    Parameters:
        model (spotlight.sequence.implicit.ImplicitSequenceModel): Trained sequence model.
        appid (str): Steam App ID of the game.
        model_dir (str, optional): Directory to save the models. Default is 'models'.
    """
    today_date = datetime.datetime.now().strftime('%Y-%m-%d')
    model_name = f"{appid}_{today_date}"
    model_path = os.path.join(model_dir, model_name)
    os.makedirs(model_dir, exist_ok=True)
    model.save(model_path)

def load_most_recent_model(appid, model_dir='models'):
    """
    Loads the most recently trained model for a given appid.

    Parameters:
        appid (str): Steam App ID of the game.
        model_dir (str, optional): Directory where models are saved. Default is 'models'.

    Returns:
        spotlight.sequence.implicit.ImplicitSequenceModel: Loaded model.
    """
    models_for_appid = [model for model in os.listdir(model_dir) if model.startswith(f"{appid}_")]
    if not models_for_appid:
        # Train and save the model if it doesn't exist
        print(f"No models found for appid {appid}. Training a new model.")
        model = ImplicitSequenceModel(n_iter=10, representation='cnn', loss='adaptive_hinge', random_state=np.random.RandomState(42))
        model.fit(sequences, verbose=True)
        save_model(model, appid)
    else:
        most_recent_model = max(models_for_appid)
        model_path = os.path.join(model_dir, most_recent_model)
        model = ImplicitSequenceModel.load(model_path)

    return model

def get_ranked_scores_for_user_with_model(model, user_sequence, achievement_name_dict, exclude_last_item=True):
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
    
    # Items not in the users set that we want to retrieve scores for
    if exclude_last_item:
        desired_items = [key for key, value in achievement_name_dict.items() if value not in user_items[:-1]]
    else:
        desired_items = [key for key, value in achievement_name_dict.items() if value not in user_items[:]]

    scores = model.predict(sequences=user_sequence)
    scores_series = pd.Series(scores[1:], index=achievement_name_dict.keys(), name='ScoresSeries')
    scores_series = scores_series.loc[desired_items]
    scores_series = scores_series.sort_values(ascending=False)

    return scores_series

# Load achievement descriptions and interactions from SQLite database
df_achievements = load_achievement_descriptions_from_sqlite(APP_ID)
df_interactions = load_interactions_from_sqlite(APP_ID)

# Create dictionaries of Steam IDs and achievement names onto internal IDs used by the model
steam_id_dict = {steam_id: idx + 1 for idx, steam_id in enumerate(df_interactions['steamid'].unique())}
achievement_name_dict = {apiname: idx + 1 for idx, apiname in enumerate(df_interactions['apiname'].unique())}

# Replace 'steamid' and 'apiname' with integers using the dictionaries
df_interactions['steamid'] = df_interactions['steamid'].map(steam_id_dict)
df_interactions['apiname'] = df_interactions['apiname'].map(achievement_name_dict)

# Remove rows with missing values and timestamp equal to 0
df_interactions = df_interactions.dropna()
df_interactions = df_interactions[df_interactions['timestamp'] != 0]

# Convert the interaction sets into sequences
sequences = interactions_to_sequences(df_interactions, MAX_SEQUENCE_LENGTH)

# Load or train the model
loaded_model = load_most_recent_model(APP_ID)

# Use the loaded model to get ranked scores for a user sequence
user_sequence_to_predict = sequences.sequences[0]  # Change this to the user sequence you want to predict
scores_series_loaded_model = get_ranked_scores_for_user_with_model(loaded_model, user_sequence_to_predict, achievement_name_dict)

# Display the top 10 achievements with scores and descriptions using the loaded model
result_df_loaded_model = pd.merge(scores_series_loaded_model, df_achievements, right_on='apiname', left_index=True, how='left')
result_df_loaded_model = result_df_loaded_model.rename(columns={'ScoresSeries': 'score'})
result_df_loaded_model.head(10)
