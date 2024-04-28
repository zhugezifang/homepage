$ pip install --requirement requirements.txt
$ docker run --detach --name db-debug --publish 27017:27017 mongo
$ uvicorn app:app --reload
