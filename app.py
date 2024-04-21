import typing
import datetime
import json
import pathlib

import requests
import fastapi

app = fastapi.FastAPI()

@app.get("/stats/")
@app.get("/stats/{ref:path}")
async def stats(ref: str):
    path = pathlib.Path("stats") / (ref or "index.html")
    print(path)

    res = fastapi.responses.FileResponse(path)
    res.headers["Cache-Control"] = "public, max-age=3600, s-maxage=3600"
    res.headers["CDN-Cache-Control"] = "max-age=3600"
    return res

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
