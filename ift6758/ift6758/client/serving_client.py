import json
import requests
import pandas as pd
import logging

from comet_ml.api import API

logger = logging.getLogger(__name__)


class ServingClient:
    def __init__(self, ip: str = "serving", port: int = 6565, features=None):
        self.base_url = f"http://{ip}:{port}"
        logger.info(f"Initializing client; base URL: {self.base_url}")

        if features is None:
            features = ["distance"]
        self.features = features

        # any other potential initialization

    def predict(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Formats the inputs into an appropriate payload for a POST request, and queries the
        prediction service. Retrieves the response from the server, and processes it back into a
        dataframe that corresponds index-wise to the input dataframe.

        Args:
            X (Dataframe): Input dataframe to submit to the prediction service.
        """
        r = requests.post(
            self.base_url+"/predict",
            json=json.loads(X.iloc[0:5].to_json())
        )
        logger.info(f"Successfully generated predictions")
        return r.json()

        # raise NotImplementedError("TODO: implement this function")

    def logs(self) -> dict:
        """Get server logs"""
        r = requests.post(
            self.base_url+"/logs",
            json= {'workspace': 'zilto', 'model': 'best_xgb', 'version': '1.0.1'}
        )
        logger.info(f"Server logs fetched")
        # raise NotImplementedError("TODO: implement this function")

    def download_registry_model(self, workspace: str, model: str, version: str) -> dict:
        """
        Triggers a "model swap" in the service; the workspace, model, and model version are
        specified and the service looks for this model in the model registry and tries to
        download it.

        See more here:

            https://www.comet.ml/docs/python-sdk/API/#apidownload_registry_model

        Args:
            workspace (str): The Comet ML workspace
            model (str): The model in the Comet ML registry to download
            version (str): The model version to download
        """
        logger.info(f"downloading the {model}-{version}")
        r = requests.post(
            self.base_url+"/download_registry_model",
            json= {'workspace': workspace, 'model': model, 'version': version}
        )
        logger.info(f"Successfully downloaded the model")
        # TODO make sure the model is correctly downloaded, and the appropriate files are cleared
        #API.download_registry_model(workspace=workspace, registry_name=model, version=version)
        #print(f"The model '{model}' was successfully downloaded.")
