import json
from urllib.parse import urlencode

import requests
from aiohttp import ClientSession, web

from anisole import TOKEN, TOKEN_FP, CONFIG

client_id = "bgm11505d350198b7d4e"
client_secret = "20e87e75077c448a9a2bd7cfa97d15d6"


access_token_url = "https://bgm.tv/oauth/access_token"
authorize_url = "https://bgm.tv/oauth/authorize"
routes = web.RouteTableDef()
redirect_uri = "http://localhost:8079"


@routes.get("/")
async def hello(request):
    echo = ""
    try:
        code = request.query["code"]
        async with ClientSession() as session:
            r = await session.request(
                "POST",
                access_token_url,
                data={
                    "grant_type": "authorization_code",
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "code": code,
                    "redirect_uri": redirect_uri,
                },
            )
            text = await r.text()
            info = await r.json()
        if info and "access_token" in info:
            TOKEN.update(info)
            with open(TOKEN_FP, "w") as f:
                json.dump(TOKEN, f)
            echo = info
        else:
            echo = Exception(text)
    except Exception as e:
        echo = e

    if isinstance(echo, Exception):
        return web.Response(text=f"Failed!\n{echo}")

    return web.Response(text=f"Hello Anisole!\n{echo}")


params_authorize = {"client_id": client_id, "response_type": "code"}
url_to_go = authorize_url + f"?{urlencode(params_authorize)}"


def run_auth():
    print(f"---> Please open {url_to_go} in your browser to get access token.")
    app = web.Application()
    app.add_routes(routes)
    web.run_app(app, port=8079)


def check_token():
    if TOKEN and "access_token" in TOKEN:
        resp = requests.post(
            "https://bgm.tv/oauth/token_status",
            data={"access_token": TOKEN["access_token"]},
            headers={"User-Agent": CONFIG["User-Agent"]},
        )
        print(resp.text)
        if resp.status_code == 200:
            return True
        else:
            return refresh_token()
    else:
        run_auth()


def refresh_token():
    print("Refreshing Token...")
    data = {
        "grant_type": "refresh_token",
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": TOKEN["refresh_token"],
        "redirect_uri": redirect_uri,
    }

    resp = requests.post(
        "https://bgm.tv/oauth/access_token",
        data=data,
        headers={"User-Agent": CONFIG["User-Agent"]},
    )
    print(resp.text)
    info = resp.json()
    if info and "access_token" in info:
        TOKEN.update(info)
        with open(TOKEN_FP, "w") as f:
            json.dump(TOKEN, f)
        return True
    else:
        run_auth()
