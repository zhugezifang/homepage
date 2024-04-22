import typing
import datetime
import json
import pathlib
import time

import requests
import fastapi
import pydantic

app = fastapi.FastAPI()

class LiteYItem(pydantic.BaseModel):
    content: str

class LiteYDeleteItem(pydantic.BaseModel):
    id: str

def json_read(pos):
    path = pathlib.Path(pos)

    if not path.is_file():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps([]))

    text = path.read_text("UTF-8")
    print(path, "から読み込みました")

    return json.loads(text)

def json_write(pos, data):
    path = pathlib.Path(pos)
    text = json.dumps(data)

    path.write_text(text, "UTF-8")
    print(path, "に書き込みました")

def fastapi_serve(dir, ref, index = "index.html"):
    path = pathlib.Path(dir) / (ref or index)
    print(path, "をサーブ中")

    if not path.is_file():
        return fastapi.responses.PlainTextResponse("指定されたファイルが見つかりません", fastapi.status.HTTP_404_NOT_FOUND)

    return fastapi.responses.FileResponse(path)

@app.get("/cloudflare")
async def cloudflare(x_token: typing.Union[str, None] = fastapi.Header(default=None), zone_id: str = None):
    today = datetime.datetime.now()
    last_month = today - datetime.timedelta(days=30)

    query = pathlib.Path("analytics_daily.txt").read_text("UTF-8")
    variables = {
        "zoneTag": zone_id,
        "from": last_month.astimezone(datetime.timezone.utc).strftime("%Y-%m-%d"),
        "to": today.astimezone(datetime.timezone.utc).strftime("%Y-%m-%d"),
        "limit": 30
    }
    data = {
        "query": query,
        "variables": variables
    }
    result = requests.post(
        url="https://api.cloudflare.com/client/v4/graphql",
        headers={
            "Authorization": f"Bearer {x_token}"
        },
        data=json.dumps(data)
    )

    res = fastapi.responses.JSONResponse(result.json())
    res.headers["Access-Control-Allow-Origin"] = "*"
    res.headers["Cache-Control"] = "public, max-age=60, s-maxage=60"
    res.headers["CDN-Cache-Control"] = "max-age=60"
    return res

@app.get("/stats/")
@app.get("/stats/{ref:path}")
async def stats(ref: str):
    res = fastapi_serve("stats", ref)
    res.headers["Cache-Control"] = "public, max-age=3600, s-maxage=3600"
    res.headers["CDN-Cache-Control"] = "max-age=3600"
    return res

@app.get("/memo")
async def memo():
    memo = pathlib.Path("memo.txt").read_text("UTF-8")

    res = fastapi.responses.PlainTextResponse(memo)
    res.headers["Cache-Control"] = "public, max-age=3600, s-maxage=3600"
    res.headers["CDN-Cache-Control"] = "max-age=3600"
    return res

@app.get("/litey/get")
async def litey_get():
    db = json_read("litey_data/db.json")

    res = fastapi.responses.JSONResponse(db)
    res.headers["Access-Control-Allow-Origin"] = "*"
    res.headers["Cache-Control"] = "public, max-age=5, s-maxage=5"
    res.headers["CDN-Cache-Control"] = "max-age=5"
    return res

@app.post("/litey/post")
async def litey_post(item: LiteYItem, request: fastapi.Request):
    db = json_read("litey_data/db.json")

    db += [{
        "id": str(time.time_ns()),
        "content": item.content,
        "date": datetime.datetime.now().astimezone(datetime.timezone.utc).isoformat(),
        "ip": request.client.host
    }]

    json_write("litey_data/db.json", db)

    return fastapi.responses.PlainTextResponse("OK")

@app.post("/litey/delete")
async def litey_delete(item: LiteYDeleteItem):
    db = json_read("litey_data/db.json")

    for i, x in enumerate(db):
        if x["id"] == item.id:
            del db[i]

    json_write("litey_data/db.json", db)

    return fastapi.responses.PlainTextResponse("OK")

@app.get("/litey/")
@app.get("/litey/{ref:path}")
async def litey(ref: str):
    res = fastapi_serve("litey", ref)
    res.headers["Cache-Control"] = "public, max-age=3600, s-maxage=3600"
    res.headers["CDN-Cache-Control"] = "max-age=3600"
    return res

@app.get("/")
@app.get("/{ref:path}")
async def home(ref: str):
    res = fastapi_serve("public", ref)
    res.headers["Cache-Control"] = "public, max-age=3600, s-maxage=3600"
    res.headers["CDN-Cache-Control"] = "max-age=3600"
    return res
