import click

from anisole.bgm.watcher import Watcher


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
        last_uid = watcher.add(
            name,
            uid=uid,
            keyword=keyword,
            regex=regex,
            includes=includes,
            excludes=excludes,
            prefers=prefers,
        )
        watcher.last_uid = last_uid

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
        watcher.jar.store(jar, echo=False)
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

        watcher.jar.store(jar, echo=False)
        jar.echo(detailed=1)
        click.echo("")
        watcher.last_uid = uid

        watcher.save()


@bgm.command()
@click.argument("uid", type=click.INT, required=False)
@click.option("-a", "--all-update", is_flag=True)
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
@click.option("-s", "--simplified", is_flag=True)
def ls(simplified):
    detailed = 0
    if simplified:
        detailed = -1
    watcher = Watcher.load_from()
    watcher.jar.list(detailed=detailed)


@bgm.command()
@click.argument("uid", type=click.INT, required=False)
@click.option("-a", "--all-info", is_flag=True)
def info(uid, all_info):
    watcher = Watcher.load_from()
    if not uid:
        uid = watcher.last_uid
    jar = watcher.jar.content.get(uid, None)
    if jar:
        d = 3 if all_info else 2
        jar.echo(detailed=d)
        click.echo("")
        watcher.last_uid = uid
        watcher.save()


@bgm.command()
@click.argument("uids", type=click.INT, nargs=-1)
@click.option(
    "-s", "--save-files", is_flag=True, help="Do not remove downloaded files."
)
def rm(uids, save_files):
    watcher = Watcher.load_from()
    watcher.jar.rm(*uids, save_files=save_files)
    watcher.save()


@bgm.command()
@click.argument("uid", type=click.INT, required=False)
@click.option("-t", "--tag", multiple=True)
@click.option("-a", "--all-down", is_flag=True)
def dl(uid, tag, all_down):
    watcher = Watcher.load_from()
    if not uid:
        uid = watcher.last_uid
    if uid in watcher.jar.ids:
        sub = watcher.jar.content[uid]
        sub.download(*tag, all_=all_down)
        watcher.last_uid = sub.uid
        watcher.save()


@bgm.command()
@click.argument("uid", nargs=1, required=False)
@click.argument("tag", nargs=1, required=False)
def play(uid, tag):
    watcher = Watcher.load_from()

    stag = None
    if not uid and not tag:
        uid = watcher.last_uid
        stag = None
    else:
        if not tag:
            stag = uid
            uid = watcher.last_uid
        else:
            uid = int(uid)
            stag = tag
    if uid in watcher.jar.ids:
        sub = watcher.jar.content[uid]
        sub.play(stag)
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
        sub.echo(nl=True)
        watcher.save()
