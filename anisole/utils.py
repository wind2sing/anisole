import re
from pathlib import Path
from itertools import chain
from collections import defaultdict
from wcwidth import wcswidth

_EP_PATTERNS = [
    re.compile(r"第(\d{1,3})[^季\-0-9]"),
    re.compile(r"[^.S×xX\-0-9](\d{2,3})[ \]】V]"),
]


def parse_anime_ep(text):
    """Analyze the episode from link's title."""
    text = text.upper()
    cleans = ["1080P", "720P", "480P", "BIG5", "MP4"]
    for c in cleans:
        text = text.replace(c, "")

    if "合集" in text:
        return -1

    for pattern in _EP_PATTERNS:
        match = pattern.search(text)
        if match:
            return int(match.group(1))

    return -2


def is_chs(title):
    keys = ["繁體", "BIG5", "big5", "繁体", "CHT", "繁日"]
    chs = True
    for key in keys:
        if key in title:
            chs = False
            break

    return chs


def is_video(f: Path):
    if not f.is_file():
        return False
    ext = f.suffix
    ext = ext.lstrip(".").lower()
    vexts = [
        "mp4",
        "m4v",
        "mkv",
        "mov",
        "avi",
        "wmv",
        "webm",
        "mov",
        "webm",
        "mpg",
        "flv",
        "strm",
    ]
    return ext in vexts


def all_videos(fp: Path):
    if not isinstance(fp, Path):
        fp = Path(fp)

    if fp.is_dir():
        for f in fp.iterdir():
            yield from all_videos(f)
    else:
        if is_video(fp):
            yield fp


def plen(s):
    return wcswidth(s)


def pcut(s, maxl):
    length = 0
    rli = []
    for char in s:
        length += wcswidth(char)
        if length > maxl:
            break
        else:
            rli.append(char)
    return "".join(rli)


def pfixed(s, length):
    slen = plen(s)
    if slen > length:
        s = pcut(s, length)
        slen = length

    return s + " " * (length - slen)


def pformat_list(li, each_line=4, name_maxl=30, align=None):
    if not li:
        return

    if not align:
        align = min(max([plen(name) for name in li]) + 2, name_maxl + 2)

    i = 1  # count for each line
    ft_li = []

    length = len(li)
    for idx, name in enumerate(li):

        end = i == each_line
        name = pcut(name, align)
        space = "" if end else " " * (align - plen(name))
        ft_li.append(f"{name}{space}")

        if end:
            if idx != length - 1:
                ft_li.append("\n")
                i = 1
        else:
            ft_li.append("   ")
            i += 1
    return ft_li


def _collapse_range(ranges):
    end = None
    for value in ranges:
        yield range(max(end, value.start), max(value.stop, end)) if end else value
        end = max(end, value.stop) if end else value.stop


def _split_range(value: str):
    m = re.match(r"(.*)@(\d+)$", value)
    post = 0
    if m:
        post = int(m.group(2))
        value = m.group(1)
    value = value.split("-")
    for val, prev in zip(value, chain((None,), value)):
        if val != "":
            val = int(val)
            if prev == "":
                val *= -1
            yield [val, post]


def _parse_range(r):
    if len(r) == 0:
        return []
    parts = [*_split_range(r)]
    if len(parts) > 2:
        raise ValueError("Invalid range: {}".format(r))

    left, post = parts[0]
    (right, post) = parts[-1]
    return range(left, right + 1), post


def parse_eps_list(rl):

    res = {}
    for x in rl.split(","):
        rg, post = _parse_range(x)
        for i in rg:
            res[i] = post
    return sorted([*res.items()], key=lambda v: v[0])
