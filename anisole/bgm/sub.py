import re
import subprocess
import xmlrpc.client
from collections import Iterable
from shutil import rmtree
from typing import Dict, List

import click
from hanziconv import HanziConv

from anisole import BASE_PATH
from anisole.utils import all_videos, parse_anime_ep


def append_or_extend(li: list, ele, remove=False):
    if remove:
        if isinstance(ele, Iterable):
            for e in ele:
                if e in li:
                    li.remove(e)
        else:
            if ele in li:
                li.remove(ele)
    else:
        if isinstance(ele, Iterable):
            li.extend(ele)
        else:
            li.append(ele)


class Sub:
    """A subscription object.
    """

    wd = BASE_PATH / "downloads"
    _fields = ["name", "marked", "keyword", "includes", "excludes", "prefers", "regex"]

    def __init__(
        self,
        name: str,
        uid: int = None,
        keyword: str = None,
        regex=None,
        includes: List[str] = None,
        excludes: List[str] = None,
        prefers: List[str] = None,
        **kwargs,
    ):

        self._uid = None
        self._fp = None

        self.name = name
        self.uid = uid
        if not keyword:
            keyword = name
        self.keyword = keyword
        self.regex = re.compile(regex) if regex else None
        self.includes = []
        self.include(kw=includes)
        self.excludes = []
        self.exclude(kw=excludes)
        self.prefers = []
        self.prefer(kw=prefers)

        self.links = {}

        self.marked = kwargs.get("marked", 0)

    @classmethod
    def load_from(cls, sub_dict: dict, links=None):
        name = sub_dict.pop("name")
        obj = cls(name, **sub_dict)
        obj.links = links or {}
        return obj

    def dump_to(self):
        sub_dict = {"uid": self.uid}
        sub_dict.update({field: self.__dict__[field] for field in self._fields})
        return sub_dict, self.links

    @property
    def uid(self):
        return self._uid

    @uid.setter
    def uid(self, val):
        if val is None:
            self._uid = None
            return
        if isinstance(val, int) and val > 0:
            self._uid = val
            new_fp = self.wd / str(val)
            old_fp = self._fp

            if old_fp:
                old_fp.rename(new_fp)
            else:
                new_fp.mkdir(parents=True, exist_ok=True)
            self._fp = new_fp
        else:
            raise ValueError("UID should be a positive integer!")

    @property
    def fp(self):
        return self._fp

    def download(self, *tag, all_=False):
        s = xmlrpc.client.ServerProxy("http://localhost:6800/rpc")

        aria2 = s.aria2

        eis = []

        if not tag:
            ep = max(self.links.keys())
            tag = [str(ep)]
        for t in tag:
            li = t.split(":", 1)
            if len(li) == 1:
                li.append("0")
            ep = int(li[0])
            idx = int(li[1])
            eis.append((ep, idx))

        if all_:
            eps = [ep for ep, _ in eis]
            for ep in self.links:
                if ep > 0 and ep not in eps:
                    eis.append((ep, 0))

        for ep, idx in eis:
            link = self.links[ep][idx]
            magnet = link["link"]

            path = str(self.get_fp_by_ep(ep))
            aria2.addUri("token:", [magnet], {"dir": path})

            self.echo(detailed=0)
            click.secho(f"\n-Downloading...{link['title']} to {path}")

    def play(self, tag):
        if tag is None:
            self.echo(detailed=0)
            click.echo("")
            for e, files in self.play_dic.items():
                click.secho(f"    @{e}:", fg="yellow")
                for i, f in enumerate(files):
                    click.secho(f"       {i:<2}{f}")
        else:
            li = tag.split(":", 1)
            if len(li) == 1:
                li.append("0")
            ep = int(li[0])
            idx = int(li[1])

            if ep in self.play_dic and idx < len(self.play_dic[ep]) and idx >= 0:
                f = self.play_dic[ep][idx]
                click.secho(f"Play... {f}")
                subprocess.run(["open", f], check=True)
            else:
                click.secho(f"Invalid tag: {tag}", fg="red")

    @property
    def play_dic(self):
        """Return a dictionary of {episode: List[path]}"""
        pd = {}

        for f in all_videos(self.fp):
            ep = parse_anime_ep(f.stem)
            li = pd.setdefault(ep, [])
            li.append(f)
        return {k: v for k, v in sorted(pd.items(), key=lambda x: x[0])}

    @property
    def downloaded(self):
        pl_a = {k: v for k, v in self.play_dic.items() if v}
        keys = [k for k in pl_a.keys() if isinstance(k, int)]
        if keys:
            return max(keys)
        else:
            return 0

    @property
    def episoded(self):
        """Max episode"""
        episodes = self.links.keys()
        if episodes:
            eps = max(episodes)
        else:
            eps = 0
        return eps

    def get_fp_by_ep(self, ep: int, mkdir=True):
        path = self.fp / str(ep)
        if mkdir:
            path.mkdir(parents=True, exist_ok=True)
        return path

    def re(self, regex):
        if regex:
            self.regex = re.compile(regex)

    def include(self, kw=None, nkw=None, clear: bool = False):
        if clear:
            self.includes = []

        if kw:
            append_or_extend(self.includes, kw)
        if nkw:
            append_or_extend(self.includes, nkw, remove=True)

    def exclude(self, kw=None, nkw=None, clear: bool = False):
        if clear:
            self.excludes = []

        if kw:
            append_or_extend(self.excludes, kw)
        if nkw:
            append_or_extend(self.excludes, nkw, remove=True)

    def prefer(self, kw=None, nkw=None, clear: bool = False):
        if clear:
            self.prefers = []

        if kw:
            append_or_extend(self.prefers, kw)
        if nkw:
            append_or_extend(self.prefers, nkw, remove=True)

    def clutter_item(self, item):
        content = item.content
        if self.is_valid(content):
            li = self.links.setdefault(content["episode"], [])
            li.append(content)

    def sort(self):
        for _, li in self.links.items():
            li.sort(key=self.get_priority, reverse=True)

    def get_priority(self, item):
        priority = 0
        for p in self.prefers:
            point = 1
            while p.startswith("#"):
                p = p.split("#", 1)[-1]
                point += 1
            if p == "chs" and item["chs"]:
                priority += point
            elif p == "1080P" and ("1080" in item["title"]):
                priority += point
            elif p == "720P" and ("720" in item["title"]):
                priority += point
            else:
                if p in item["title"]:
                    priority += point
        return priority

    def is_valid(self, content):
        text = content["tag"] + content["title"]
        text = HanziConv.toSimplified(text)

        if self.regex:
            if not self.regex.search(text):
                return False

        pass_exc = True
        for exc in self.excludes:
            if exc in text:
                pass_exc = False
                break

        pass_inc = True
        if self.includes:
            pass_inc = False
            for inc in self.includes:
                if inc in text:
                    pass_inc = True

        return pass_exc and pass_inc

    def echo(self, fg_1="green", detailed=0, nl=False, dim_on_old=False):

        if detailed == -1:
            click.secho(f"{self.name}", nl=False)
        else:
            new = self.marked < self.episoded
            click.secho(
                f"{self.uid:<4}{self.name} ({self.episoded},{self.downloaded},{self.marked})",
                fg=fg_1,
                nl=False,
                dim=(not new) and dim_on_old,
            )
        if detailed > 0:
            click.echo("")
            click.secho(f"    --keyword: {self.keyword}", nl=False)
            if self.regex:
                click.echo("")
                click.secho(f"    --regex: {self.regex.pattern}", nl=False)
            if self.includes:
                click.echo("")
                click.secho(f"    --includes: {self.includes}", nl=False)
            if self.excludes:
                click.echo("")
                click.secho(f"    --excludes: {self.excludes}", nl=False)
            if self.prefers:
                click.echo("")
                click.secho(f"    --prefers: {self.prefers}", nl=False)

            click.echo("")
            click.secho(f"    --local: {self.fp}", nl=False)

            if detailed > 1 and self.links:
                click.echo("")
                click.secho(f"    --links:", nl=False)
                for episode, li in sorted(self.links.items(), key=lambda x: x[0]):
                    if detailed == 2:
                        # echo the prior links
                        item = li[0]
                        click.echo("")
                        click.secho(f"      @{episode:<4}", fg="yellow", nl=False)
                        click.secho(f": {item['title']}", nl=False)
                    else:
                        # echo all links
                        click.echo("")
                        click.secho(f"      @{episode}:", fg="yellow", nl=False)
                        for i, item in enumerate(li):
                            click.echo("")
                            click.secho(f"       {i:>4} {item['title']}", nl=False)

        if nl:
            click.echo("")


class SubJar:
    def __init__(self):
        self.content: Dict[int, Sub] = {}

    @property
    def ids(self) -> set:
        return self.content.keys()

    def list(self, detailed=0):
        for jar in sorted(self.content.values(), key=lambda j: j.uid):
            jar.echo(detailed=detailed, dim_on_old=True)
            if detailed == -1:
                click.echo(" ", nl=False)
            else:
                click.echo("")

        if detailed == -1:
            click.echo("")

    def store(self, sub: Sub, echo=True):
        if isinstance(sub.uid, int) and sub.uid > 0:
            if sub.uid in self.ids:
                old_sub = self.content[sub.uid]
                old_sub.uid = self._gen_uid()
                self.content[old_sub.uid] = old_sub
        else:
            sub.uid = self._gen_uid()
        self.content[sub.uid] = sub
        if echo:
            click.secho("Add:", fg="green")
            sub.echo(detailed=1)
            click.echo("")
        return sub.uid

    def rm(self, *uids: int, save_files=False):
        click.secho("Remove:", fg="red")
        for uid in uids:
            if uid in self.ids:
                sub = self.content.pop(uid)
                sub.echo(fg_1="red", detailed=0)
                click.echo("")
                if save_files:
                    new_fp = sub.fp.parent / sub.name
                    new_fp.mkdir(parents=True, exist_ok=True)
                    sub.fp.rename(new_fp)
                    click.echo(f"Downloaded files are moved to {new_fp}.")
                else:
                    rmtree(sub.fp)

    def _gen_uid(self) -> int:
        i = 1
        while True:
            if i not in self.ids:
                break
            else:
                i += 1
        return i

    @classmethod
    def load_from(cls, sub_dicts, links_dict):
        """Load from (a list of sub info, a dictionary of uid->links)"""
        jar = cls()
        for sub_dict in sub_dicts:
            uid = sub_dict["uid"]
            links = links_dict.pop(uid, {})
            sub = Sub.load_from(sub_dict, links)
            jar.content[uid] = sub
        return jar

    def dump_to(self):
        """Return (a list of sub info, a dictionary of uid->links)"""
        links_dict = {}
        sub_dicts = []
        for sub in sorted(self.content.values(), key=lambda s: s.uid):
            sub: Sub
            uid = sub.uid
            sub_dict, links = sub.dump_to()
            sub_dicts.append(sub_dict)
            links_dict[uid] = links

        return sub_dicts, links_dict
