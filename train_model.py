import sys
import datetime
import numpy as np
import os
import pandas as pd
import torch
from config import Config
from spotlight.interactions import Interactions
from spotlight.sequence.implicit import ImplicitSequenceModel
from tqdm import tqdm
from data_utils import interactions_to_sequences, load_interactions_from_sqlite
from get_steam_ids import get_steam_ids
from get_achievements import get_achievements_for_appid
from get_achievement_descriptions import save_achievement_descriptions_to_sqlite

API_KEY = Config.STEAM_API_KEY
if API_KEY is None:
    raise ValueError("API key not found in the configuration.")

def fetch_data_and_train_model(appid, n_steam_ids, loss='adaptive_hinge', representation='lstm', embedding_dim=32, n_iter=10, batch_size=256, l2=0.0, learning_rate=0.01, model_dir='models'):
    """
    Fetch data, train and save an ImplicitSequenceModel using achievement data.

    Parameters:
    - appid (str): Steam App ID of the game.
    - n_steam_ids (int): Number of Steam IDs to retrieve.
    - loss (str, optional): Loss function. Default is 'adaptive_hinge'.
    - representation (str, optional): Type of sequence representation. Default is 'lstm'.
    - embedding_dim (int, optional): Dimensionality of embedding vectors. Default is 32.
    - n_iter (int, optional): Number of training iterations. Default is 10.
    - batch_size (int, optional): Size of batches for training. Default is 256.
    - l2 (float, optional): L2 regularization term. Default is 0.0.
    - learning_rate (float, optional): Learning rate for training. Default is 0.01.
    - model_dir (str, optional): Directory to save the trained model. Default is 'models'.
    """

    # Fetch achievements for the game and number of Steam IDs
    get_achievements_for_appid(appid, n_steam_ids)

    # Save achievement descriptions to SQLite
    save_achievement_descriptions_to_sqlite(API_KEY, appid)

    # Proceed with model training
    df_interactions = load_interactions_from_sqlite(appid)
    steam_id_dict = {steam_id: idx + 1 for idx, steam_id in enumerate(df_interactions['steamid'].unique())}
    achievement_name_dict = {apiname: idx + 1 for idx, apiname in enumerate(df_interactions['apiname'].unique())}

    df_interactions['steamid'] = df_interactions['steamid'].map(steam_id_dict)
    df_interactions['apiname'] = df_interactions['apiname'].map(achievement_name_dict)

    # Remove rows with missing values and timestamp equal to 0
    df_interactions = df_interactions.dropna()
    df_interactions = df_interactions[df_interactions['unlocked'] != 0]

    interactions = Interactions(
        user_ids=df_interactions['steamid'].values.astype(np.int32),
        item_ids=df_interactions['apiname'].values.astype(np.int32),
        timestamps=df_interactions['unlocked'].values.astype(np.int32)
    )   

    # Convert the interaction set into sequences
    max_sequence_length = len(achievement_name_dict.keys())
    sequences = interactions_to_sequences(interactions, max_sequence_length)

    # Train the model
    model = ImplicitSequenceModel(
        loss=loss,
        representation=representation,
        embedding_dim=embedding_dim,
        n_iter=n_iter,
        batch_size=batch_size,
        l2=l2,
        learning_rate=learning_rate,
        random_state=np.random.RandomState(42)
    )

    model.fit(sequences, verbose=False)

    # Add the achievement name dictionary to the model
    model.achievement_name_dict = {v: k for k, v in achievement_name_dict.items()}

   # Save the trained model with date and time
    today_datetime = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    model_name = f"{appid}_{today_datetime}"
    model_path = os.path.join(model_dir, model_name)
    os.makedirs(model_dir, exist_ok=True)
    torch.save(model, model_path)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python train_model.py <appid> <n_steam_ids>")
    else:
        appid = sys.argv[1]
        n_steam_ids = int(sys.argv[2])

        fetch_data_and_train_model(appid, n_steam_ids)
