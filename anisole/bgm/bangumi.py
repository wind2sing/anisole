import requests
import click

from anisole import TOKEN
from anisole.utils import pformat_list


API_PREFIX = "https://api.bgm.tv"


class TokenNotFound(Exception):
    pass


class API:
    """Simple API class to work with bgm.tv"""

    def __init__(self, watcher):
        if not TOKEN:
            raise TokenNotFound
        self.watcher = watcher

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

