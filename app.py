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
from features import basic_features, advanced_features, normalize_plays_coords



LOG_FILE = os.environ.get("FLASK_LOG", "flask.log")


app = Flask(__name__)

model = None
@app.before_first_request
def before_first_request():
    """
    Hook to handle any initialization before the first request (e.g. load model,
    setup logging handler, etc.)
    """
    # TODO: setup basic logging configuration
    logging.basicConfig(filename=LOG_FILE, level=logging.INFO)
    # df = pd.read_csv("./data/plays_2015-2020.csv", index_col=False)
    # advanced_df = advanced_features(df)

    # TODO: any other initialization before the first request (e.g. load default model)
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
    # Get POST json data
    json = request.get_json()
    app.logger.info(json)


    try:
        model = XGBClassifier() # or which ever sklearn booster you're are using
        model.load_model("best_xgb.json")
        app.logger.info("model already downloaded")

    except (OSError, IOError) as e:
        app.logger.info("model not found...downloading")
        api = API()
        api.download_registry_model("zilto", "best-xgb", "1.0.1",
                            output_path="./", expand=True)
        model = XGBClassifier() # or which ever sklearn booster you're are using
        model.load_model("best_xgb.json")
        app.logger.info("model downloaded")
    response = "model loaded"
    # app.logger.info(response)
    return jsonify(response)  # response must be json serializable!


@app.route("/predict", methods=["POST"])
def predict():
    """
    Handles POST requests made to http://IP_ADDRESS:PORT/predict

    Returns predictions
    """
    global model
    # Get POST json data
    json = request.get_json()
    app.logger.info(json)

    # TODO:
    # raise NotImplementedError("TODO: implement this enpdoint")
    # model = pickle.load(open("best-xgb_1.0.0.pickle", "rb"))
    X_test = pd.read_csv('test.csv')
    response = model.predict_proba(X_test)[::,1]

    return jsonify(response)  # response must be json serializable!

# if __name__ == "__main__":
#     app.run(host='0.0.0.0')
