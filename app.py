import typing
import datetime
import json
import pathlib
import time
import io
import os
import base64

import requests
import fastapi
import fastapi.templating
import pydantic
import matplotlib.figure
import matplotlib.backends.backend_agg
import pymongo

app = fastapi.FastAPI()

templates = fastapi.templating.Jinja2Templates("templates")

mongo = pymongo.MongoClient(
    os.environ.get("MONGO_URI", "mongodb://127.0.0.1:27017/"),
    username=os.environ.get("MONGO_USER"),
    password=os.environ.get("MONGO_PASSWORD")
)

for db_name in mongo.list_database_names():
    print(db_name)

    if db_name == "local":
        continue

    for col_name in mongo[db_name].list_collection_names():
        index_info = mongo[db_name][col_name].index_information()
        print(db_name, col_name, index_info)

class LiteYItem(pydantic.BaseModel):
    content: str

class LiteYDeleteItem(pydantic.BaseModel):
    id: str

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

def get_cloudflare_analytics_as_json(token: str, zone_id: str, query_path: str, limit: int, time_type: str, time_format: str) -> bytes:
    query = pathlib.Path(query_path).read_text("UTF-8")

    now = datetime.datetime.now()
    before = now - datetime.timedelta(**{ time_type: limit })

    variables = {
        "zoneTag": zone_id,
        "from": before.astimezone(datetime.timezone.utc).strftime(time_format),
        "to": now.astimezone(datetime.timezone.utc).strftime(time_format),
        "limit": limit
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

    return result.json()

def convert_cloudflare_json_to_png(json: dict, title: str, group: str) -> bytes:
    first_group = json["data"]["viewer"]["zones"][0][group]

    y1 = [group["uniq"]["uniques"] for group in first_group]
    x1 = range(0 - len(y1) + 1, 0 + 1)

    y2 = [group["sum"]["bytes"] for group in first_group]
    x2 = range(0 - len(y2) + 1, 0 + 1)

    y3 = [group["sum"]["cachedBytes"] for group in first_group]
    x3 = range(0 - len(y3) + 1, 0 + 1)

    fig = matplotlib.figure.Figure((7, 7))
    fig.suptitle(title)

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
    canvas = matplotlib.backends.backend_agg.FigureCanvasAgg(fig)
    canvas.print_png(img)
    img.seek(0)
    return img.getvalue()

def get_ip(req: fastapi.Request) -> str:
    return req.headers.get("CF-Connecting-IP") or req.client.host

def ip_to_uid(ip: typing.Optional[str]) -> str:
    if not ip:
        return "-"

    return base64.b64encode(ip.encode("utf-8")).decode("utf-8")[:11]

templates.env.filters["ip_to_uid"] = ip_to_uid

@app.middleware("http")
async def cors_handler(req: fastapi.Request, call_next: typing.Callable[[fastapi.Request], typing.Awaitable[fastapi.Response]]):
    res = await call_next(req)

    if req.url.path.startswith("/api/"):
        res.headers["Access-Control-Allow-Origin"] = "*"
        res.headers["Access-Control-Allow-Credentials"] = "true"
        res.headers["Access-Control-Allow-Methods"] = "*"
        res.headers["Access-Control-Allow-Headers"] = "*"

        if req.method == "OPTIONS":
            res.status_code = fastapi.status.HTTP_200_OK

    return res

@app.get("/api/test")
async def api_test(req: fastapi.Request):
    json = {
        "ip": get_ip(req),
        "ua": req.headers.get("User-Agent")
    }

    res = fastapi.responses.JSONResponse(json)
    res.headers["Cache-Control"] = "public, max-age=0, s-maxage=0"
    res.headers["CDN-Cache-Control"] = "max-age=0"
    return res

@app.get("/api/request_headers")
async def api_request_headers(req: fastapi.Request):
    json = req.headers.items()

    res = fastapi.responses.JSONResponse(json)
    res.headers["Cache-Control"] = "public, max-age=0, s-maxage=0"
    res.headers["CDN-Cache-Control"] = "max-age=0"
    return res

@app.get("/api/cloudflare")
async def api_cloudflare(token: str, zone_id: str):
    json = get_cloudflare_analytics_as_json(token, zone_id, "analytics_daily.txt", 30, "days", "%Y-%m-%d")
    title = get_cloudflare_domain_name(token, zone_id)
    png = convert_cloudflare_json_to_png(json, title, "httpRequests1dGroups")

    res = fastapi.responses.Response(png, media_type="image/png")
    res.headers["Cache-Control"] = "public, max-age=600, s-maxage=600"
    res.headers["CDN-Cache-Control"] = "max-age=600"
    return res

@app.get("/api/cloudflare2")
async def api_cloudflare2(token: str, zone_id: str):
    json = get_cloudflare_analytics_as_json(token, zone_id, "analytics_hourly.txt", 72, "hours", "%Y-%m-%dT%H:%M:%SZ")
    title = get_cloudflare_domain_name(token, zone_id)
    png = convert_cloudflare_json_to_png(json, title, "httpRequests1hGroups")

    res = fastapi.responses.Response(png, media_type="image/png")
    res.headers["Cache-Control"] = "public, max-age=600, s-maxage=600"
    res.headers["CDN-Cache-Control"] = "max-age=600"
    return res

@app.get("/api/memo")
async def api_memo():
    memo = pathlib.Path("memo.txt").read_text("UTF-8")

    res = fastapi.responses.PlainTextResponse(memo)
    res.headers["Cache-Control"] = "public, max-age=3600, s-maxage=3600"
    res.headers["CDN-Cache-Control"] = "max-age=3600"
    return res

@app.get("/api/litey/get")
async def api_litey_get(id: str = None):
    col = mongo["litey"].notes

    if not id:
        json = list(col.find({}, { "_id": False }).sort("id", pymongo.ASCENDING))
    else:
        json = col.find_one({ "id": id }, { "_id": False })

    res = fastapi.responses.JSONResponse(json)
    res.headers["Cache-Control"] = "public, max-age=5, s-maxage=5"
    res.headers["CDN-Cache-Control"] = "max-age=5"
    return res

@app.post("/api/litey/post")
async def api_litey_post(item: LiteYItem, req: fastapi.Request):
    col = mongo["litey"].notes

    col.insert_one({
        "id": str(time.time_ns()),
        "content": item.content,
        "date": datetime.datetime.now().astimezone(datetime.timezone.utc).isoformat(),
        "ip": get_ip(req)
    })

    return fastapi.responses.PlainTextResponse("OK")

@app.post("/api/litey/delete")
async def api_litey_delete(item: LiteYDeleteItem):
    col = mongo["litey"].notes

    col.delete_one({ "id": item.id })

    return fastapi.responses.PlainTextResponse("OK")

@app.get("/api/litey/image-proxy")
async def api_litey_image_proxy(url: str):
    result = requests.get(url, timeout=5, headers={
        "User-Agent": pathlib.Path("user_agent.txt").read_text("UTF-8").rstrip("\n")
    })

    content = result.content
    media_type = result.headers.get("Content-Type")

    res = fastapi.responses.Response(content, media_type=media_type)
    res.headers["Cache-Control"] = "public, max-age=86400, s-maxage=86400"
    res.headers["CDN-Cache-Control"] = "max-age=86400"
    return res

@app.get("/stats")
async def stats(req: fastapi.Request):
    res = templates.TemplateResponse(req, "stats.html")
    res.headers["Cache-Control"] = "public, max-age=0, s-maxage=0"
    res.headers["CDN-Cache-Control"] = "max-age=0"
    return res

@app.get("/litey")
async def litey(req: fastapi.Request):
    col = mongo["litey"].notes
    json = list(col.find({}, { "_id": False }).sort("id", pymongo.ASCENDING))

    context = {
        "notes": json
    }

    res = templates.TemplateResponse(req, "litey.html", context)
    res.headers["Cache-Control"] = "public, max-age=0, s-maxage=0"
    res.headers["CDN-Cache-Control"] = "max-age=0"
    return res

@app.get("/stats-realtime")
async def stats_realtime(req: fastapi.Request):
    res = templates.TemplateResponse(req, "stats-realtime.html")
    res.headers["Cache-Control"] = "public, max-age=0, s-maxage=0"
    res.headers["CDN-Cache-Control"] = "max-age=0"
    return res

@app.get("/")
async def home(req: fastapi.Request):
    context = {
        "ip": get_ip(req),
        "ua": req.headers.get("User-Agent")
    }

    res = templates.TemplateResponse(req, "home.html", context)
    res.headers["Cache-Control"] = "public, max-age=0, s-maxage=0"
    res.headers["CDN-Cache-Control"] = "max-age=0"
    return res

@app.get("/{ref:path}")
async def static(ref: str = None):
    res = fastapi_serve("static", ref)
    res.headers["Cache-Control"] = "public, max-age=3600, s-maxage=3600"
    res.headers["CDN-Cache-Control"] = "max-age=3600"
    return res
