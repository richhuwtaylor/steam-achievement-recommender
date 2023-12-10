import os

class Config:
    DB_NAME = 'achievements.db'
    MODEL_DIR = 'models'
    STEAM_API_KEY = os.environ.get('STEAM_API_KEY', None)