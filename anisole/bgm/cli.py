import click
from anisole.bgm.dmhy import DMHY


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
@click.option("-p", "--prefers", multiple=True, help="Prefered specific words")
def add(names, keyword, regex, includes, excludes, prefers, uid):
    dm = DMHY.load_from()
    # if not prefers:
    #     prefers = ["#chs", "1080P"]
    for name in names:
        last_uid = dm.add(
            name,
            uid=uid,
            keyword=keyword,
            regex=regex,
            includes=includes,
            excludes=excludes,
            prefers=prefers,
        )
        dm.last_uid = last_uid

    dm.save()


@bgm.command()
@click.argument("uidset", nargs=2, type=click.INT)
def setuid(uidset):
    dm = DMHY.load_from()
    old_uid = uidset[0]
    new_uid = uidset[1]

    jar = dm.jar.content.pop(old_uid, None)
    if jar:
        click.echo("Change uid from:")
        jar.echo(detailed=False)
        click.echo("\nto")

        jar.uid = new_uid
        dm.jar.store(jar, echo=False)
        jar.echo(detailed=False)
        click.echo("")

        dm.last_uid = new_uid
        dm.save()


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

    dm = DMHY.load_from()
    if not uid:
        uid = dm.last_uid
    jar = dm.jar.content.pop(uid, None)
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

        dm.jar.store(jar, echo=False)
        jar.echo(detailed=1)
        click.echo("")
        dm.last_uid = uid

        dm.save()


@bgm.command()
@click.argument("uid", type=click.INT, required=False)
@click.option("-a", "--all-update", is_flag=True)
def update(uid, all_update):
    dm = DMHY.load_from()
    if not uid:
        uid = dm.last_uid
    if all_update:
        dm.update(uid, all_=all_update)
    else:
        dm.update(uid)

    click.echo("")
    if uid in dm.jar.ids:
        dm.last_uid = uid
    dm.save()


@bgm.command()
@click.option("-s", "--simplified", is_flag=True)
def ls(simplified):
    detailed = 0
    if simplified:
        detailed = -1
    dm = DMHY.load_from()
    dm.jar.list(detailed=detailed)


@bgm.command()
@click.argument("uid", type=click.INT, required=False)
@click.option("-a", "--all-info", is_flag=True)
def info(uid, all_info):
    dm = DMHY.load_from()
    if not uid:
        uid = dm.last_uid
    jar = dm.jar.content.get(uid, None)
    if jar:
        d = 3 if all_info else 2
        jar.echo(detailed=d)
        click.echo("")
        dm.last_uid = uid
        dm.save()


@bgm.command()
@click.argument("uids", type=click.INT, nargs=-1)
def rm(uids):
    dm = DMHY.load_from()
    dm.jar.rm(*uids)
    dm.save()


@bgm.command()
@click.argument("uid", type=click.INT, required=False)
@click.option("-t", "--tag", multiple=True)
@click.option("-a", "--all-down", is_flag=True)
def dl(uid, tag, all_down):
    dm = DMHY.load_from()
    if not uid:
        uid = dm.last_uid
    if uid in dm.jar.ids:
        sub = dm.jar.content[uid]
        sub.download(*tag, all_=all_down)
        dm.last_uid = sub.uid
        dm.save()


@bgm.command()
@click.argument("uid", nargs=1, required=False)
@click.argument("tag", nargs=1, required=False)
def play(uid, tag):
    dm = DMHY.load_from()

    stag = None
    if not uid and not tag:
        uid = dm.last_uid
        stag = None
    else:
        if not tag:
            stag = uid
            uid = dm.last_uid
        else:
            uid = int(uid)
            stag = tag
    if uid in dm.jar.ids:
        sub = dm.jar.content[uid]
        sub.play(stag)
        dm.last_uid = sub.uid
        dm.save()


@bgm.command()
@click.argument("uid", nargs=1, type=click.INT)
@click.argument("mark-ep", nargs=1, type=click.INT, required=False)
def mark(uid, mark_ep):
    dm = DMHY.load_from()
    if not mark_ep:
        mark_ep = uid
        uid = dm.last_uid

    if uid in dm.jar.ids:
        sub = dm.jar.content[uid]
        sub.marked = mark
        sub.echo(nl=True)
        dm.save()

