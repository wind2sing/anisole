import requests
import click

from anisole import TOKEN
from anisole.utils import pformat_list
from anisole.bgm.auth import check_token


API_PREFIX = "https://api.bgm.tv"


class TokenNotFound(Exception):
    pass


class BadAPIRequest(Exception):
    pass


class API:
    """Simple API class to work with bgm.tv"""

    def __init__(self, watcher):
        self.watcher = watcher

    @property
    def headers(self):
        if not TOKEN:
            raise TokenNotFound
        return {"Authorization": f'Bearer {TOKEN.get("access_token")}'}

    def cal(self, filter_rating_count=10):
        url = f"{API_PREFIX}/calendar"
        r = requests.get(url)
        weekdays = r.json()
        index = 1
        for weekday in weekdays:
            click.secho(weekday["weekday"]["cn"], fg="green")
            items = weekday["items"]
            li = []
            for item in items:
                name = item["name_cn"] or item["name"]
                if "rating" in item and item["rating"]["total"] >= filter_rating_count:
                    text = f"#{index:<3}{name}"
                    # click.secho(text)
                    li.append(text)
                    index += 1

            click.echo(pformat_list(li, align=40))

    def search(self, keyword, typ=2):
        r = requests.get(f"{API_PREFIX}/search/subject/{keyword}?type={typ}")
        r.raise_for_status()
        return r.json()

    def auth(self):
        return check_token()

    def collection_update(self, subject_id: int, status="do", action="update"):
        url = f"{API_PREFIX}/collection/{subject_id}/{action}"
        r = requests.post(url, headers=self.headers, data={"status": status})
        if r.status_code == 200:
            return True
        print(r.text)
        raise BadAPIRequest(url)

    def watched_until(self, subject_id: int, watched_eps: int):
        url = f"{API_PREFIX}/subject/{subject_id}/update/watched_eps"
        r = requests.post(url, headers=self.headers, data={"watched_eps": watched_eps})

        if r.status_code == 200:
            if r.json()["code"] == 202:
                return True
        print(r.text)
        raise BadAPIRequest(url)

