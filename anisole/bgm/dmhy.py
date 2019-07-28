import pickle
import re
from pathlib import Path
from typing import List

from acrawler import Crawler, ParselItem, Processors, Request, Response, Task

from anisole.bgm.sub import Sub, SubJar
from anisole.utils import is_chs


class DMHYLink(ParselItem):
    store = True
    css_rules = {"title": ".title > a ::text"}
    css_rules_first = {
        "tag": ".tag a::text",
        "link": "a.arrow-magnet::attr(href)",
        "size": ".title + td + td::text",
        "sort": "a[href*=sort]::attr(href)",
    }

    field_processors = {
        "title": ["".join, Processors.strip],
        "tag": [Processors.strip, lambda s: "其它" if s is None else s],
        # "link": lambda s: s.split("&", 1)[0],
        "sort": lambda s: int(s.rsplit("/", 1)[-1]),
    }

    def custom_process(self, content):
        content["chs"] = is_chs(content["title"])

        title = content["title"]

        content["episode"] = -2
        if content["sort"] == 2:
            content["episode"] = self.get_episode(title)
        elif content["sort"] == 31:
            content["episode"] = -1

        if content["tag"] != "其它":
            if title.startswith("【"):
                title = re.sub(r"^【.*?】", "", title).strip()
            else:
                title = re.sub(r"^\[.*?\]", "", title).strip()
        content["title_clean"] = title

    @staticmethod
    def get_episode(text):
        cleans = ["1080P", "720P", "BIG5", "big5", "1080p", "720p", "MP4", "mp4"]
        for c in cleans:
            text = text.replace(c, "")

        if "合集" in text:
            return -1

        match = re.search(r"第(\d{1,3})[^季]", text)
        if match:
            return int(match.group(1))

        match = re.search(r"[^.S×x\-0-9](\d{2,3})[ \]】]", text)
        if match:
            return int(match.group(1))

        return -2


class DMHYTask(Task):
    def __init__(self, sub: Sub, sort_id=2, team_id=0, order="date-desc"):
        super().__init__()
        self.sub = sub
        self.sort_id = sort_id
        self.team_id = team_id
        self.order = order
        self.urls = []
        for page in range(1, 4):
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
    pass


class DMHY:
    wd = Path.home() / ".bgm"
    fp = wd / "bgm.data"

    def __init__(self):
        self.jar = SubJar()
        self.crawler = DMHYCrawler()
        self.last_uid = None

    @classmethod
    def load_from(cls, fp=None) -> "DMHY":
        if fp:
            cls.fp = Path(fp)
        fp = cls.fp
        if fp.is_file():
            with open(fp, "rb") as f:
                obj = pickle.load(f)
                return obj
        else:
            return cls()

    def save(self):
        self.fp.parent.mkdir(parents=True, exist_ok=True)
        with open(self.fp, "wb") as f:
            pickle.dump(self, f)

    def add(
        self,
        name: str,
        uid: int = None,
        keyword: str = None,
        regex=None,
        includes: List[str] = None,
        excludes: List[str] = None,
        prefers: List[str] = None,
    ):
        sub = Sub(
            name,
            uid=uid,
            keyword=keyword,
            regex=regex,
            includes=includes,
            excludes=excludes,
            prefers=prefers,
        )
        uid = self.jar.store(sub)
        return uid

    def update(self, uid, all_=False):
        origin_uid = uid
        if all_:
            uids = self.jar.ids
        else:
            uids = [uid]

        for uid in uids:
            if uid in self.jar.ids:
                sub = self.jar.content[uid]
                sub.links = {}
                task = DMHYTask(sub)
                self.crawler.add_task_sync(task)
        self.crawler.run()

        # collect results
        items = self.crawler.storage.get("DMHYLink", [])
        for item in items:
            uid = item["uid"]
            sub = self.jar.content[uid]
            sub.clutter_item(item)

        # print results
        if all_:
            for sub in self.jar.content.values():
                sub.sort()
                sub.echo(detailed=0, nl=True, dim_on_old=True)
        else:
            if origin_uid in self.jar.ids:
                sub = self.jar.content[origin_uid]
                sub.sort()
                sub.echo(detailed=0, nl=True, dim_on_old=True)

    def __getstate__(self):
        state = self.__dict__
        state.pop("crawler", None)
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.__dict__["crawler"] = DMHYCrawler()
