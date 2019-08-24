import re

from acrawler import Crawler, ParselItem, Processors as x, Request, Response, Task

from anisole.bgm.sub import Sub
from anisole.utils import is_chs, parse_anime_ep


class DMHYLink(ParselItem):
    store = True
    css = {
        "tag": [".tag a::text", x.strip(), lambda s: "其它" if s is None else s],
        "link": "a.arrow-magnet::attr(href)",  # lambda s: s.split("&", 1)[0],
        "size": ".title + td + td::text",
        "sort": ["a[href*=sort]::attr(href)", lambda s: int(s.rsplit("/", 1)[-1])],
        "title": ["[.title > a ::text]", "".join, x.strip()],
    }

    def custom_process(self, content):
        content["chs"] = is_chs(content["title"])
        title = content["title"]

        content["episode"] = -2
        if content["sort"] == 2:
            content["episode"] = parse_anime_ep(title)
        elif content["sort"] == 31:
            content["episode"] = -1

        if content["tag"] != "其它":
            if title.startswith("【"):
                title = re.sub(r"^【.*?】", "", title).strip()
            else:
                title = re.sub(r"^\[.*?\]", "", title).strip()
        content["title_clean"] = title


class DMHYTask(Task):
    def __init__(self, sub: Sub, sort_id=2, team_id=0, order="date-desc"):
        super().__init__()
        self.sub = sub
        self.sort_id = sort_id
        self.team_id = team_id
        self.order = order
        self.urls = []
        for page in range(1, 6):
            url = "https://share.dmhy.org/topics/list/page/{}?keyword={}&sort_id={}&team_id={}&order={}".format(
                page, self.sub.keyword, self.sort_id, self.team_id, self.order
            )
            self.urls.append(url)

    async def _execute(self):
        for url in self.urls:
            yield Request(url=url, callback=self.parse_search)

    def parse_search(self, resp: Response):
        for tr in resp.sel.css(".table .clear tbody tr"):
            yield DMHYLink(tr, extra={"uid": self.sub.uid})


class DMHYCrawler(Crawler):
    request_config = {"timeout": 4}
