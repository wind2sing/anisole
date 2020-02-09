from typing import List
import pickle
import toml

from anisole import BASE_PATH, CONFIG, CONFIG_FP
from anisole.bgm.dmhy import DMHYCrawler, DMHYTask
from anisole.bgm.sub import Sub, SubJar
from anisole.bgm.bangumi import API


class Watcher:
    wd = BASE_PATH
    fp = wd / "bgmlinks.data"

    def __init__(self, jar, crawler, last_uid=None):
        self.jar = jar  # Storage of subscriptions
        self.crawler = crawler  # Crawler for source website
        self.last_uid = last_uid

        self._api = None  # bgm.tv API client

    @property
    def api(self):
        if not self._api:
            self._api = API(watcher=self)
        return self._api

    @classmethod
    def load_from(cls) -> "Watcher":
        sub_dicts = CONFIG.get("bgm", {}).get("sub", [])
        last_uid = CONFIG.get("bgm", {}).get("last_uid", None)

        if cls.fp.is_file():
            with open(cls.fp, "rb") as f:
                links_dict = pickle.load(f)
        else:
            links_dict = {}

        jar = SubJar.load_from(sub_dicts, links_dict)
        crawler = DMHYCrawler()

        return cls(jar, crawler, last_uid)

    def save(self):
        """Save to two files"""
        sub_dicts, links_dict = self.jar.dump_to()
        bgm = CONFIG.setdefault("bgm", {})
        if self.last_uid:
            bgm["last_uid"] = self.last_uid
        if sub_dicts:
            bgm["sub"] = sub_dicts
        else:
            bgm.pop("sub", None)
        with open(CONFIG_FP, "w") as f:
            toml.dump(CONFIG, f)
        with open(self.fp, "wb") as f:
            pickle.dump(links_dict, f)

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
        sub = self.jar.store(sub)
        return sub

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
                sub.echo(detailed=0, nl=True, dim_on_old=True, last_uid=self.last_uid)
        else:
            if origin_uid in self.jar.ids:
                sub = self.jar.content[origin_uid]
                sub.sort()
                sub.echo(detailed=0, nl=True, dim_on_old=True, last_uid=self.last_uid)
