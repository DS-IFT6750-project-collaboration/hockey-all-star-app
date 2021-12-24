####
This repository is part of milestone-3 for course ift6758 by group number: 8 
To Run jupyter dashboard follow below notes:<br><br>
Since the machine that was to build the docker image has MAC m1 processor you can't use directly the link obtained from docker-compose up to run jupyter notebook.  <br><br>
1)Run docker-compose up (build the image and run it).<br>
2)After running docker-compose up, go to http://0.0.0.0:5001/ and paste the token obtained from terminal after running docker-compose up. <br> 
3)Run dashboard from ift6758/ift6758/client/jupyter_dashboard.ipynb <br>

Note: If you are unable to fetch COMET_API_KEY directly from environment, then paste your COMET_API_KEY into comet_key.txt and uncomment the line 46-47 in app.py
