import requests
import click
from datetime import date

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
        return {
            "Authorization": f'Bearer {TOKEN.get("access_token")}',
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.70 Safari/537.36",
        }

    def cal(self, filter_rating_count=10):
        url = f"{API_PREFIX}/calendar"
        r = requests.get(url, headers=self.headers)
        weekdays = r.json()
        index = 1
        today = date.today()
        for weekday in weekdays:
            if weekday["weekday"]["id"] == today.weekday() + 1:
                click.secho("-> " + weekday["weekday"]["cn"] + "-" * 12, fg="magenta")
            else:
                click.secho(weekday["weekday"]["cn"] + "-" * 15, fg="green")
            items = weekday["items"]
            li = []
            for item in items:
                name = item["name_cn"] or item["name"]
                bid = item["id"]
                if "rating" in item and item["rating"]["total"] >= filter_rating_count:
                    text = f"#{index:<3}{name[:12]} {item['rating']['score']}"
                    if self.watcher.jar.get_sub_by_bid(bid):
                        text = "@" + text
                    # click.secho(text)
                    li.append(text)
                    index += 1
            ft_li = pformat_list(li, align=40)
            for ft in ft_li:
                if ft.startswith("@"):
                    ft = ft[1:] + " "
                    click.secho(ft, nl=False, fg="cyan")
                else:
                    click.secho(ft, nl=False)
            click.echo("\n")

    def search(self, keyword, typ=2, page=1, max_results=25):
        r = requests.get(
            f"{API_PREFIX}/search/subject/{keyword}?type={typ}&max_results={max_results}&start={0+(page-1)*max_results}",
            headers=self.headers,
        )
        r.raise_for_status()
        try:
            res = r.json()
            if "list" in res:
                return res["list"]
            else:
                return []
        except Exception as e:
            return []

    def auth(self):
        return check_token()

    def subject_info(self, subject_id: int, response_group="small"):
        r = requests.get(
            f"{API_PREFIX}/subject/{subject_id}?responseGroup={response_group}",
            headers=self.headers,
        )
        return r.json()

    def collection_update(self, subject_id: int, status="do", action="update"):
        url = f"{API_PREFIX}/collection/{subject_id}/{action}"
        r = requests.post(url, headers=self.headers, data={"status": status})
        if r.status_code == 200:
            return True
        print(r.text)
        raise BadAPIRequest(url)

    def ep_info(self, subject_id: int, watched_eps: int):
        url = f"{API_PREFIX}/subject/{subject_id}/ep"
        r = requests.get(url, headers=self.headers)
        data = r.json()["eps"][watched_eps - 1]
        return data

    def watched_until(self, subject_id: int, watched_eps: int):
        data = self.ep_info(subject_id, watched_eps)
        id_ = data["id"]
        print(data["url"], data["name"], data["airdate"])
        url = f"{API_PREFIX}/subject/{subject_id}/update/watched_eps"
        r = requests.post(url, headers=self.headers, data={"watched_eps": watched_eps})
        print(r.text)
        if r.status_code == 200:
            if r.json()["code"] == 202:
                return True

        raise BadAPIRequest(url)
