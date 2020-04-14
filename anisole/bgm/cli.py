import click

from anisole.bgm.watcher import Watcher
from anisole.utils import pfixed


@click.group()
def bgm():
    pass


@bgm.command()
@click.argument("names", nargs=-1)
@click.option("-k", "--keyword", help="Keyword for searching, default to the name")
@click.option(
    "-i",
    "--uid",
    type=click.INT,
    help="Uid of the subscription, auto-generated if not set",
)
@click.option("-re", "--regex", help="Regular expression for matching results")
@click.option("-inc", "--includes", multiple=True, help="Includes specific words")
@click.option("-exc", "--excludes", multiple=True, help="Excludes specific words")
@click.option("-p", "--prefers", multiple=True, help="Prefers specific words")
def add(names, keyword, regex, includes, excludes, prefers, uid):
    watcher = Watcher.load_from()
    # if not prefers:
    #     prefers = ["#chs", "1080P"]
    for name in names:
        sub = watcher.add(
            name,
            uid=uid,
            keyword=keyword,
            regex=regex,
            includes=includes,
            excludes=excludes,
            prefers=prefers,
        )
        watcher.last_uid = sub.uid
        click.secho("Add:", fg="green")
        sub.echo(detailed=1)
        click.echo("")

    watcher.save()


@bgm.command()
@click.argument("uidset", nargs=2, type=click.INT)
def setuid(uidset):
    watcher = Watcher.load_from()
    old_uid = uidset[0]
    new_uid = uidset[1]

    jar = watcher.jar.content.pop(old_uid, None)
    if jar:
        click.echo("Change uid from:")
        jar.echo(detailed=False)
        click.echo("\nto")

        jar.uid = new_uid
        watcher.jar.store(jar)
        jar.echo(detailed=False)
        click.echo("")

        watcher.last_uid = new_uid
        watcher.save()


@bgm.command()
@click.argument("uid", type=click.INT, required=False)
@click.option("-nk", "--name-and-keyword", help="Name and keyword of subscrition")
@click.option("-n", "--name", help="Name of the subscription")
@click.option("-k", "--keyword", help="Keyword for searching")
@click.option("-i", "--uid-new", type=click.INT, help="Uid of the subscription")
@click.option("-re", "--regex", help="Regular expression for matching results")
@click.option("-inca", "--includes-add", multiple=True)
@click.option("-incr", "--includes-remove", multiple=True)
@click.option("-incc", "--includes-clear", is_flag=True)
@click.option("-exca", "--excludes-add", multiple=True)
@click.option("-excr", "--excludes-remove", multiple=True)
@click.option("-excc", "--excludes-clear", is_flag=True)
@click.option("-pa", "--prefers-add", multiple=True)
@click.option("-pr", "--prefers-remove", multiple=True)
@click.option("-pc", "--prefers-clear", is_flag=True)
def config(
    uid,
    uid_new,
    name_and_keyword,
    name,
    keyword,
    regex,
    includes_clear,
    includes_add,
    includes_remove,
    excludes_add,
    excludes_remove,
    excludes_clear,
    prefers_add,
    prefers_remove,
    prefers_clear,
):

    watcher = Watcher.load_from()
    if not uid:
        uid = watcher.last_uid
    jar = watcher.jar.content.pop(uid, None)
    if jar:
        click.echo("Config from:")
        jar.echo(detailed=1)
        click.echo("\n-->")

        if name_and_keyword:
            jar.name = name_and_keyword
            jar.keyword = name_and_keyword
        jar.name = name or jar.name
        jar.keyword = keyword or jar.keyword
        jar.uid = uid_new or jar.uid

        jar.re(regex)
        jar.include(kw=includes_add, nkw=includes_remove, clear=includes_clear)
        jar.exclude(kw=excludes_add, nkw=excludes_remove, clear=excludes_clear)
        jar.prefer(kw=prefers_add, nkw=prefers_remove, clear=prefers_clear)

        watcher.jar.store(jar)
        jar.echo(detailed=1)
        click.echo("")
        watcher.last_uid = uid

        watcher.save()


@bgm.command()
@click.argument("uid", type=click.INT, required=False)
@click.option("-a", "--all-update", is_flag=True, help="Update all subscriptions")
def update(uid, all_update):
    watcher = Watcher.load_from()
    if not uid:
        uid = watcher.last_uid
    if all_update:
        watcher.update(uid, all_=all_update)
    else:
        watcher.update(uid)

    if uid in watcher.jar.ids:
        watcher.last_uid = uid
    watcher.save()


@bgm.command()
@click.option("-s", "--simplified", is_flag=True, help="print in minimal format")
def ls(simplified):
    detailed = -1 if simplified else 0
    watcher = Watcher.load_from()
    for jar in sorted(watcher.jar.content.values(), key=lambda j: j.uid):
        jar.echo(detailed=detailed, dim_on_old=True)
        if detailed == -1:
            click.echo(" ", nl=False)
        else:
            if watcher.last_uid == jar.uid:
                click.secho(" <<<<", fg="yellow", nl=False)
            click.echo("")

    if detailed == -1:
        click.echo("")


@bgm.command()
@click.argument("uid", type=click.INT, required=False)
@click.option("-a", "--all-info", is_flag=True, help="print detailed information")
def info(uid, all_info):
    watcher = Watcher.load_from()
    if not uid:
        uid = watcher.last_uid
    jar = watcher.jar.content.get(uid, None)
    if jar:
        d = 2 if all_info else 1
        jar.echo(detailed=d)
        click.echo("")
        watcher.last_uid = uid
        watcher.save()


@bgm.command()
@click.argument("uids", type=click.INT, nargs=-1)
@click.option("-s", "--save-files", is_flag=True, help="Do not remove downloaded files")
def rm(uids, save_files):
    click.secho("Remove:", fg="red")
    watcher = Watcher.load_from()
    for uid in uids:
        if uid in watcher.jar.ids:
            sub, new_fp = watcher.jar.rm(uid, save_files=save_files)
            sub.echo(fg_1="red", detailed=0)
            click.echo("")
            if new_fp:
                click.echo(f"Downloaded files are moved to {new_fp}.")
    watcher.save()


@bgm.command()
@click.argument("uid", type=click.INT, required=False)
@click.option("-t", "--tags")
@click.option("-a", "--all-down", is_flag=True)
def dl(uid, tags, all_down):
    watcher = Watcher.load_from()
    if not uid:
        uid = watcher.last_uid
    if uid in watcher.jar.ids:
        sub = watcher.jar.content[uid]
        results = sub.download(tags, all_=all_down)
        for title, path in results:
            sub.echo(detailed=0)
            click.secho(f"\n-Downloading...{title} in {path}")
        watcher.last_uid = sub.uid
        watcher.save()


@bgm.command()
@click.argument("uid", nargs=1, type=click.INT, required=False)
@click.option("-t", "--tag", help="If not provided, play the latest episode")
@click.option("-l", "--list-all", is_flag=True, help="Print all playable files")
def play(uid, tag, list_all):
    watcher = Watcher.load_from()

    if not uid:
        uid = watcher.last_uid

    if uid in watcher.jar.ids:
        sub = watcher.jar.content[uid]
        if list_all:
            sub.echo(detailed=1)
            click.echo("")
            for e, files in sub.play_dic.items():
                click.secho(f"    @{e}:", fg="yellow")
                for i, f in enumerate(files):
                    click.secho(f"       {i:<2}{f}")
        else:
            f = sub.play(tag)
            if f:
                click.secho(f"Play... {f}")
                print(sub.bgm_url)
            else:
                click.secho(f"Invalid tag: {tag}", fg="red")
        watcher.last_uid = sub.uid
        watcher.save()


@bgm.command()
@click.argument("uid", nargs=1, type=click.INT)
@click.argument("mark-ep", nargs=1, type=click.INT, required=False)
def mark(uid, mark_ep):
    watcher = Watcher.load_from()
    if mark_ep is None:
        mark_ep = uid
        uid = watcher.last_uid

    if uid in watcher.jar.ids:
        sub = watcher.jar.content[uid]
        sub.marked = mark_ep
        if sub.bid:
            watcher.api.watched_until(sub.bid, mark_ep)
        sub.echo(nl=True)
        watcher.last_uid = sub.uid
        watcher.save()


# commands for bgm.tv
@bgm.command()
def auth():
    watcher = Watcher.load_from()
    if watcher.api.auth():
        click.secho("OK!", fg="green")


@bgm.command()
def cal():
    watcher = Watcher.load_from()
    watcher.api.cal()


# @bgm.command()
# @click.argument("uid", nargs=1, type=click.INT, required=False)
# @click.option("-b", "--bid", type=click.INT, help="directly assign the bangumi id")
@bgm.command()
@click.argument("uids", type=click.INT, nargs=-1, required=False)
def link(uids):
    watcher = Watcher.load_from()
    if not uids:
        uids = [watcher.last_uid]
    for uid in uids:
        if uid in watcher.jar.ids:
            sub = watcher.jar.content[uid]
            p = watcher.api
            sub.echo(detailed=0)
            click.echo("\nSearching...")

            bidx = 0
            page = 0
            while bidx == 0:
                page += 1
                results = p.search(sub.keyword, page=page)
                if not results:
                    print("No results!")
                    return
                for idx, result in enumerate(results):
                    name = result.get("name_cn", "") or result.get("name", "")
                    url = result["url"]
                    text = f"{idx+1:<4}{pfixed(name,50)} {url}"
                    click.secho(text)

                bidx = click.prompt(
                    "Please enter the index integer(0 for next page)", type=int
                )

            target = results[bidx - 1]

            if click.confirm(f"Change name to {target['name']} ?"):
                sub.name = target["name"]
            bid = target["id"]
            sub.bid = bid
            sub.img = target["images"]["large"]
            p.collection_update(bid)
            click.secho(f'Link <{sub.name}> to Subject {target["url"]}', fg="green")

    if uids:
        watcher.last_uid = uids[0]
        watcher.save()
