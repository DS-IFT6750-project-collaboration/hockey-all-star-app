#!/bin/bash
docker run -it -e 0.0.0.0:5000:5000/tcp --env COMET_API_KEY=$COMET_API_KEY hockeyallstar
