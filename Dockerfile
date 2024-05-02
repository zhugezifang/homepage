FROM python:3
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
ENV PYTHONUNBUFFERED 1
CMD ["gunicorn", "app:app", "--access-logfile", "-", "--bind", "0.0.0.0", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker"]
