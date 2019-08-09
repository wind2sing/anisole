import re
from pathlib import Path

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
    return "".join(ft_li)
