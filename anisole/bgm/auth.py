import json
from urllib.parse import urlencode

from aiohttp import ClientSession, web

from anisole import TOKEN_FP

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
            with open(TOKEN_FP, "w") as f:
                json.dump(info, f)
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

print(f"---> Please open {url_to_go} in your browser to get access token.")


app = web.Application()
app.add_routes(routes)
web.run_app(app, port=8079)
