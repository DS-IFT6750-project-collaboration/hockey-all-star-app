import requests
import json
import time
import logging

import pandas as pd
import numpy as np

from features import advanced_features
from plays_model import game_json_to_plays_list

logger = logging.getLogger(__name__)

# class to interact with the API
class GameClient():
    def __init__(self, ip: str = "0.0.0.0", port: int = 5000):
        self.base_url = f"http://{ip}:{port}"
        logger.info(f"Initializing client; base URL: {self.base_url}")

        self.features_df = pd.DataFrame(columns=
            ['seconds_elapsed', 'period_idx', 'x_coord', 'y_coord', 'x_coord_norm',
             'y_coord_norm', 'dist_from_net', 'angle_from_net', 'Backhand',
             'Deflected', 'Slap Shot', 'Snap Shot', 'Tip-In', 'Wrap-around',
             'Wrist Shot', 'BLOCKED_SHOT', 'FACEOFF', 'GIVEAWAY', 'GOAL', 'HIT',
             'MISSED_SHOT', 'OTHER', 'PENALTY', 'PERIOD_START', 'SHOT', 'STOP',
             'TAKEAWAY', 'previous_x_coord', 'previous_y_coord','seconds_from_previous',
             'dist_from_previous', 'rebound','angle_change', 'speed'
            ]
        )
        self.plays_team = pd.Series(name="team_initiative_id")
        self.predictions = pd.Series(name="expected_goal")
        self.last_play_idx = 0

        self.period = None
        self.time_left = None

        self.home_abbrev = None
        self.home_team = None
        self.home_xg = 0
        self.away_abbrev = None
        self.away_team = None
        self.away_xg = 0


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
        self.last_ping_at = time.strftime("%Y/%m/%d %H:%M:%S", time.localtime())
        game_response = self.query_api(f"game/{gamePk}/feed/live")
        if self.home_team is None:
            self.home_abbrev = game_response["gameData"]["teams"]["home"]["triCode"]
            self.home_team = game_response["gameData"]["teams"]["home"]["name"]
            self.away_abbrev = game_response["gameData"]["teams"]["away"]["triCode"]
            self.away_team = game_response["gameData"]["teams"]["away"]["name"]

        plays_list = game_json_to_plays_list(game_response, augment=True, last_play_idx=self.last_play_idx)
        plays_df = pd.DataFrame.from_records(plays_list)
        # checks if new plays happened since last_event_idx
        if not plays_df.empty:
            # if new plays, update last_play_idx
            self.last_play_idx = plays_df.iloc[-1]["event_idx"]
            self.period = plays_df.iloc[-1]["period_idx"]
            self.time_left = pd.to_datetime("20:00", format="%M:%S") - pd.to_datetime(plays_df.iloc[-1]["period_time"], format="%M:%S")
            self.plays_team = self.plays_team.append(plays_df["team_initiative_id"])

            new_features_df = advanced_features(plays_df)
            new_features_df = new_features_df.reindex(columns=self.features_df.columns)
            new_features_df = new_features_df.fillna(0)
            self.features_df = self.features_df.append(new_features_df)

    def update_predictions(self):
        print(len(self.plays_team), len(self.predictions))
        home_plays_idx = self.plays_team.loc[self.plays_team==self.home_abbrev].index
        self.home_xg = np.sum(self.predictions[home_plays_idx])

        away_plays_idx = self.plays_team.loc[self.plays_team==self.away_abbrev].index
        self.away_xg = np.sum(self.predictions[away_plays_idx])
