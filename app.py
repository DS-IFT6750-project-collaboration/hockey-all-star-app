"""
If you are in the same directory as this file (app.py), you can run run the app using gunicorn:

    $ gunicorn --bind 0.0.0.0:<PORT> app:app

gunicorn can be installed via:

    $ pip install gunicorn

"""
import os
from pathlib import Path
import logging
from flask import Flask, jsonify, request, abort
import sklearn
import pandas as pd
import joblib
from comet_ml.api import API
import pickle
import ift6758
from xgboost import XGBClassifier
import json




LOG_FILE = os.environ.get("FLASK_LOG", "flask.log")


app = Flask(__name__)

model = None
model_in_use = None
COMET_API_KEY = None

@app.before_first_request
def before_first_request():
    """
    Hook to handle any initialization before the first request (e.g. load model,
    setup logging handler, etc.)
    """
    global COMET_API_KEY
    # TODO: setup basic logging configuration
    logging.basicConfig(filename=LOG_FILE, level=logging.INFO)
    # df = pd.read_csv("./data/plays_2015-2020.csv", index_col=False)
    # advanced_df = advanced_features(df)
    with open('comet_key.txt', 'r') as file:
        COMET_API_KEY = file.read().rstrip()
    with open(LOG_FILE, 'w'):
        pass

    if(os.path.isfile('best_xgb.json')):
        model = XGBClassifier() # or which ever sklearn booster you're are using
        model.load_model("best_xgb.json")
    else:
    #except (OSError, IOError) as e:
        api = API(str(COMET_API_KEY))

        api.download_registry_model("zilto", "best-xgb", "1.0.1",output_path="./", expand=True)
        model = XGBClassifier() # or which ever sklearn booster you're are using
        model.load_model("best_xgb.json")
    pass


@app.route("/logs", methods=["GET"])
def logs():
    """Reads data from the log file and returns them as the response"""

    # TODO: read the log file specified and return the data
    # raise NotImplementedError("TODO: implement this endpoint")
    file = open('flask.log', 'r')
    response = file.read().splitlines()
    file.close()
    return jsonify(response)  # response must be json serializable!


@app.route("/download_registry_model", methods=["POST"])
def download_registry_model():
    """
    Handles POST requests made to http://IP_ADDRESS:PORT/download_registry_model

    The comet API key should be retrieved from the ${COMET_API_KEY} environment variable.

    Recommend (but not required) json with the schema:

        {
            workspace: (required),
            model: (required),
            version: (required),
            ... (other fields if needed) ...
        }

    """
    global model
    global model_in_use
    global COMET_API_KEY
    # Get POST json data
    with open('comet_key.txt', 'r') as file:
        COMET_API_KEY = file.read().rstrip()
    json = request.get_json()
    app.logger.info(json)
    str = "best_xgb.json"
    model_in_use = json['model']
    if json['model'] == "best-xgb":
        str = "best_xgb.json"
    else:
        str = "base_xgb.json"
    app.logger.info(str)
    try:
        model = XGBClassifier() # or which ever sklearn booster you're are using
        model.load_model(str)
        app.logger.info("model already downloaded")
    except (OSError, IOError) as e:
        app.logger.info("model not found...downloading")
        api = API(str(COMET_API_KEY))
        # api.download_registry_model("zilto", "best-xgb", "1.0.1",
        #                     output_path="./", expand=True)
        api.download_registry_model(json['workspace'], json['model'], json['version'],output_path="./", expand=True)
        model = XGBClassifier() # or which ever sklearn booster you're are using
        model.load_model(str)
        app.logger.info("model downloaded")
    app.logger.info(str+"model loaded")
    response = str+":model loaded"
    # app.logger.info(response)
    return jsonify(response)  # response must be json serializable!


@app.route("/predict", methods=["POST"])
def predict():
    """
    Handles POST requests made to http://IP_ADDRESS:PORT/predict

    Returns predictions
    """
    global model
    global model_in_use
    # Get POST json data
    json = request.get_json()
    app.logger.info(json)

    # TODO:
    if model_in_use == 'base-xgb':
        # X_test = pd.read_csv('test_base.csv')
        features = ["angle_from_net", "dist_from_net"]
    else:
        # X_test = pd.read_csv('test.csv')
        features = ['seconds_elapsed', 'period_idx', 'x_coord', 'y_coord', 'x_coord_norm',
       'y_coord_norm', 'dist_from_net', 'angle_from_net', 'Backhand',
       'Deflected', 'Slap Shot', 'Snap Shot', 'Tip-In', 'Wrap-around',
       'Wrist Shot', 'BLOCKED_SHOT', 'FACEOFF', 'GIVEAWAY', 'GOAL', 'HIT',
       'MISSED_SHOT', 'OTHER', 'PENALTY', 'SHOT', 'STOP', 'TAKEAWAY',
       'previous_x_coord', 'previous_y_coord', 'seconds_from_previous',
       'dist_from_previous', 'rebound', 'angle_change', 'speed']
    X = pd.DataFrame(json)[features].drop_duplicates()
    response = model.predict_proba(X)[::,1]
    return jsonify(response.to_list())  # response must be json serializable!

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
