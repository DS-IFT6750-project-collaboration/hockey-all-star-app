import requests
import json
import time
import logging

import pandas as pd

from features import advanced_features
from plays_model import game_json_to_plays_list, play_json_to_play_dict, augment_with_previous_event 

logger = logging.getLogger(__name__)

# class to interact with the API
class GameClient():
    def __init__(self, ip: str = "0.0.0.0", port: int = 5000):
        self.base_url = f"http://{ip}:{port}"
        logger.info(f"Initializing client; base URL: {self.base_url}")
        
        self.features_df = None
        self.last_play_idx = 0
    
    # pass start_year, return a string to select a season (i.e., 2017 -> 20172018)
    def _start_year_to_season_string(self, start_year):
        return str(start_year) + str(start_year+1)
    
    
    # query API endpoint
    def query_api(self, endpoint, params=None):
        # base url of the API
        url = f"https://statsapi.web.nhl.com/api/v1/{endpoint}"
        r = requests.get(url, params=params, timeout=3)
        # check if the HTTP request is valid
        try:
            r.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Could not reach API endpoint:\n'{url}'")
        return r.json()
    
        
    # query API for a specific game
    def ping_game(self, gamePk):
        game_response = self.query_api(f"game/{gamePk}/feed/live")
        plays_list = game_json_to_plays_list(game_response, augment=True, last_play_idx=self.last_play_idx)
        plays_df = pd.DataFrame.from_records(plays_list)
        # checks if new plays happened since last_event_idx
        if not plays_df.empty:
            # if new plays, update last_play_idx
            self.last_play_idx = plays_df.iloc[-1]["event_idx"]
        
            # if first time computing features, create features dataframe
            if self.features_df is None:
                self.features_df = advanced_features(plays_df)
            # if features dataframe exists, update it
            else:
                self.features_df.append(advanced_features(plays_df))