$ pip install --requirement requirements.txt
$ docker run --detach --name db-debug --publish 27017:27017 mongo
$ MONGO_URI='mongodb://127.0.0.1:27017/' uvicorn app:app --reload
