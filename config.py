import os

class Config:
    STEAM_API_KEY = os.environ.get('STEAM_API_KEY', None)