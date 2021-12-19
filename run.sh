#!/bin/bash
gunicorn --bind 0.0.0.0:6565 app:app
