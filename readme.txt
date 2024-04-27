$ pip install -r requirements.txt
$ uvicorn app:app --reload

$ gunicorn app:app --access-logfile - --bind 0.0.0.0:80 --workers 4 --worker-class uvicorn.workers.UvicornWorker
