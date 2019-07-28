from pathlib import Path


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
