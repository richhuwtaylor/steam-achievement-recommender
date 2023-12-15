# steam-achievement-recommender

This project is designed to provide a personalized Steam achievement recommendation system. The recommendation is based on implicit user interactions with achievements in a particular game on the Steam platform.

This project uses the `spotlight.sequence.implicit.ImplicitSequenceModel` model class from [Spotlight](https://github.com/maciejkula/spotlight), and uses the `spotlight.sequence.representations.LSTMNet` representation of players by running a recurrent neural network over player sequences.

## Prerequisites

Before using this system, you need to obtain a Steam API key. You can obtain an API key by following the instructions [here](https://steamcommunity.com/dev/apikey). Set the obtained API key as the value for the `STEAM_API_KEY` environment variable.

## Installation

Clone the repository and install the required dependencies using the following:

```bash
pip install -r requirements.txt
```

## Usage

### 1. Train Model

To train a model for a specific game, use the `train_model.py` script. This script fetches achievement data for the specified game and desired number of players, and trains an implicit sequence model.

```bash
python train_model.py <appid> <n_steam_ids>
```

- `<appid>`: Steam App ID of the game.
- `<n_steam_ids>`: Number of players whose interactions should be retrieved for training.

### 2. Predict Scores

After training the model, use the `predict_scores.py` script to predict achievement scores for a specific player in the trained game.

```bash
python predict_scores.py <steam_id> <appid>
```

- `<steam_id>`: Steam ID of the player.
- `<appid>`: Steam App ID of the game.

The script will output a DataFrame containing ranked achievement scores along with their descriptions.

## Example

```bash
# Train model for game with App ID 12345 using 5000 Steam IDs
python train_model.py 12345 5000

# Predict achievement scores for player with Steam ID 67890 in the trained game
python predict_scores.py 67890 12345
```

## Notes

* Ensure that the `STEAM_API_KEY` environment variable is set before running the scripts.
* The project can't build models for games with fewer than 2 achievements.
