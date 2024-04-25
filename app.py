import typing
import datetime
import json
import pathlib
import time
import io

import requests
import fastapi
import pydantic
import matplotlib.figure
import matplotlib.backends.backend_agg

app = fastapi.FastAPI()

class LiteYItem(pydantic.BaseModel):
    content: str

class LiteYDeleteItem(pydantic.BaseModel):
    id: str

def json_read(pos: str) -> dict:
    path = pathlib.Path(pos)

    if not path.is_file():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps([]))

    text = path.read_text("UTF-8")
    print(path, "から読み込みました")

    return json.loads(text)

def json_write(pos: str, data: dict):
    path = pathlib.Path(pos)
    text = json.dumps(data)

    path.write_text(text, "UTF-8")
    print(path, "に書き込みました")

def fastapi_serve(dir: str, ref: str, index: str = "index.html") -> fastapi.Response:
    path = pathlib.Path(dir) / (ref or index)
    print(path, "をサーブ中")

    if not path.is_file():
        return fastapi.responses.PlainTextResponse("指定されたファイルが見つかりません", fastapi.status.HTTP_404_NOT_FOUND)

    return fastapi.responses.FileResponse(path)

def get_cloudflare_domain_name(token: str, zone_id: str) -> str:
    result = requests.get(
        f"https://api.cloudflare.com/client/v4/zones/{zone_id}",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )
    return result.json()["result"]["name"]

def get_cloudflare_analytics(token: str, zone_id: str, hours: int = 72) -> bytes:
    now = datetime.datetime.now()
    before = now - datetime.timedelta(hours=hours)

    query = pathlib.Path("analytics_hourly.txt").read_text("UTF-8")
    variables = {
        "zoneTag": zone_id,
        "from": before.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "to": now.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "limit": hours
    }

    result = requests.post(
        "https://api.cloudflare.com/client/v4/graphql",
        headers={
            "Authorization": f"Bearer {token}"
        },
        data=json.dumps({
            "query": query,
            "variables": variables
        })
    )

    first_group = result.json()["data"]["viewer"]["zones"][0]["httpRequests1hGroups"]

    y1 = [group["uniq"]["uniques"] for group in first_group]
    x1 = range(0 - len(y1) + 1, 0 + 1)

    y2 = [group["sum"]["bytes"] for group in first_group]
    x2 = range(0 - len(y2) + 1, 0 + 1)

    y3 = [group["sum"]["cachedBytes"] for group in first_group]
    x3 = range(0 - len(y3) + 1, 0 + 1)

    fig = matplotlib.figure.Figure((7, 7))
    fig.suptitle(get_cloudflare_domain_name(token, zone_id))

    canvas = matplotlib.backends.backend_agg.FigureCanvasAgg(fig)

    axs = fig.subplots(2, 1)
    axs[0].set_title("Users")
    axs[0].fill_between(x1, y1, color="#87ceeb", alpha=0.1)
    axs[0].plot(x1, y1, marker="*", color="#87ceeb")
    axs[0].set_ylim(ymin=0)
    axs[1].set_title("Bytes")
    axs[1].fill_between(x2, y2, color="silver", alpha=0.1)
    axs[1].plot(x2, y2, marker="*", color="silver")
    axs[1].fill_between(x3, y3, color="orange", alpha=0.1)
    axs[1].plot(x3, y3, marker="*", color="orange")
    axs[1].set_ylim(ymin=0)

    img = io.BytesIO()
    canvas.print_png(img)
    img.seek(0)
    return img.getvalue()

@app.get("/cloudflare")
async def cloudflare(zone_id: str, x_token: typing.Union[str, None] = fastapi.Header()):
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

@app.get("/cloudflare2")
async def cloudflare2(token: str, zone_id: str):
    res = fastapi.responses.Response(get_cloudflare_analytics(token, zone_id), media_type="image/png")
    res.headers["Access-Control-Allow-Origin"] = "*"
    res.headers["Cache-Control"] = "public, max-age=60, s-maxage=60"
    res.headers["CDN-Cache-Control"] = "max-age=60"
    return res

@app.get("/stats/")
@app.get("/stats/{ref:path}")
async def stats(ref: str = None):
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
async def litey(ref: str = None):
    res = fastapi_serve("litey", ref)
    res.headers["Cache-Control"] = "public, max-age=3600, s-maxage=3600"
    res.headers["CDN-Cache-Control"] = "max-age=3600"
    return res

@app.get("/stats-realtime/")
@app.get("/stats-realtime/{ref:path}")
async def stats_realtime(ref: str = None):
    res = fastapi_serve("stats-realtime", ref)
    res.headers["Cache-Control"] = "public, max-age=3600, s-maxage=3600"
    res.headers["CDN-Cache-Control"] = "max-age=3600"
    return res

@app.get("/image-proxy")
async def image_proxy(url: str):
    result = requests.get(url)

    content = result.content
    media_type = result.headers.get("Content-Type")

    res = fastapi.responses.Response(content, media_type=media_type)
    res.headers["Access-Control-Allow-Origin"] = "*"
    res.headers["Cache-Control"] = "public, max-age=86400, s-maxage=86400"
    res.headers["CDN-Cache-Control"] = "max-age=86400"
    return res

@app.get("/")
@app.get("/{ref:path}")
async def home(ref: str = None):
    res = fastapi_serve("public", ref)
    res.headers["Cache-Control"] = "public, max-age=3600, s-maxage=3600"
    res.headers["CDN-Cache-Control"] = "max-age=3600"
    return res
