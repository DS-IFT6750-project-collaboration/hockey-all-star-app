import requests
import json
import time
import logging

import pandas as pd

logger = logging.getLogger(__name__)

# class to interact with the API
class GameClient():
    def __init__(self, ip: str = "0.0.0.0", port: int = 5000):
        self.base_url = f"http://{ip}:{port}"
        logger.info(f"Initializing client; base URL: {self.base_url}")
        
        self.last_event_counter = 0
    
    # pass start_year, return a string to select a season (i.e., 2017 -> 20172018)
    def _start_year_to_season_string(self, start_year):
        return str(start_year) + str(start_year+1)
    
    # # save the API JSON response to file
    # def save_response(self, response, path, overwrite=False):
    #     if overwrite:
    #         with open(path, "w") as file:
    #             # if overwrite is true, return to beginning of file and overwrite
    #             file.seek(0)
    #             file.truncate()
    #             json.dump(response, file)
    #         return
        
    #     with open(path, "w") as file:
    #         json.dump(response, file)
    
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
    
    # # query API for the schedule of the year (to get valid gamePk)
    # def get_season_schedule(self, start_year):
    #     season_string = self._start_year_to_season_string(start_year)
    #     season_response = self.query_api("schedule", params={"season": season_string})
    #     save_path = f"{self.storage_path}/schedule/schedule_{season_string}.json"
    #     self.save_response(season_response, save_path, overwrite=False)
        
    # query API for a specific game
    def get_game(self, gamePk):
        game_response = self.query_api(f"game/{gamePk}/feed/live")
        plays_list = game_json_to_plays_list(game_response, augment=True)
    
      
def play_json_to_play_dict(play_json):
    # returns nothing if the event is not of type SHOT or GOAL
    if play_json["result"]["eventTypeId"] not in ["SHOT", "GOAL"]:
        return None
        
    shooter_id = None
    shooter_name = None
    goalie_id = None
    goalie_name = None
    # logic for attributing shooter and goalie name (if exists)
    if play_json.get("players"):
        for player in play_json["players"]:
            if player["playerType"] in ["Shooter", "Scorer"]:
                shooter_id = str(player["player"]["id"])
                shooter_name = player["player"]["fullName"]
            if player["playerType"] == "Goalie":
                goalie_id = str(player["player"]["id"])
                goalie_name = player["player"]["fullName"]
                
    strength = None
    if play_json["result"].get("strength"):
        strength = play_json["result"]["strength"]["code"]
    
    play_dict = {
        "event_idx": play_json["about"]["eventIdx"],
        "event_type_id": play_json["result"]["eventTypeId"],
        "period_idx": play_json["about"]["period"],
        "period_type": play_json["about"]["periodType"],
        "game_time": play_json["about"]["dateTime"],
        "period_time": play_json["about"]["periodTime"],
        "shot_type": play_json["result"].get("secondaryType"),
        "team_initiative_id": play_json["team"].get("triCode"),
        "team_initiative_name": play_json["team"].get("name"),
        "x_coord": play_json["coordinates"].get("x"),
        "y_coord": play_json["coordinates"].get("y"),
        "shooter_id": shooter_id,
        "shooter_name": shooter_name,
        "goalie_id": goalie_id,
        "goalie_name": goalie_name,
        "strength": strength,
        "empty_net_bool": play_json["result"].get("emptyNet")
    }
    
    return play_dict


def augment_with_previous_event(all_plays_list, plays_dict_list):
    augmented_plays_dict = []
    for play_dict in plays_dict_list:
        current_event_idx = play_dict["event_idx"]
        previous_event_idx = current_event_idx - 1
        
        previous_event = {
            "previous_event_idx": previous_event_idx,
            "previous_event_period": None,
            "previous_event_period_time": None,
            "previous_event_time": None,
            "previous_event_type": None,
            "previous_event_x_coord": None,
            "previous_event_y_coord": None,
        }
        
        for play_json in all_plays_list:
            if play_json["about"]["eventIdx"] == previous_event_idx:
                previous_event["previous_event_type"] = play_json["result"]["eventTypeId"]
                previous_event["previous_event_period"] = int(play_json["about"]["period"])
                previous_event["previous_event_period_time"] = play_json["about"]["periodTime"]
                previous_event["previous_event_time"] = play_json["about"]["dateTime"]
                previous_event["previous_event_x_coord"] = play_json["coordinates"].get("x")
                previous_event["previous_event_y_coord"] = play_json["coordinates"].get("y")
                
                break
            
        play_dict.update(previous_event)
        augmented_plays_dict.append(play_dict)
        
    return augmented_plays_dict


def game_json_to_plays_list(game_json, augment=False):
    all_plays_list = game_json["liveData"]["plays"]["allPlays"]
    plays_dict_list = list(filter(None, [play_json_to_play_dict(play) for play in all_plays_list]))
    if augment:
        plays_dict_list = augment_with_previous_event(all_plays_list, plays_dict_list)
    
    game_metadata = {
        "gamePk": game_json["gameData"]["game"]["pk"],
        "game_season": game_json["gameData"]["game"]["season"],
        "game_type": game_json["gameData"]["game"]["type"],
        "game_start_time": game_json["gameData"]["datetime"].get("dateTime")
    }
    
    plays_with_metadata = []
    for play_dict in plays_dict_list:
        play_dict.update(game_metadata)
        plays_with_metadata.append(play_dict)
        
    return plays_with_metadata