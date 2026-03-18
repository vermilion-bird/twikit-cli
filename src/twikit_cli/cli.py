#!/usr/bin/env python3
"""Twitter/X information retrieval CLI built on twikit."""

import asyncio
import json
import shutil
import sys
from pathlib import Path
from typing import Optional

import click
from httpx import Timeout
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from twikit import Client
from twikit.errors import TweetNotAvailable, UserNotFound

# 强制使用 UTF-8 编码（修复 Windows GBK 编码问题）
if sys.platform == "win32":
    import io
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if isinstance(sys.stderr, io.TextIOWrapper):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')

CONFIG_DIR = Path.home() / ".config" / "twikit"
DEFAULT_COOKIES_FILE = CONFIG_DIR / "cookies.json"

console = Console()
err_console = Console(stderr=True)


# ─── Helpers ──────────────────────────────────────────────────────────────────


def fmt_num(n) -> str:
    """Format large numbers with K/M suffixes."""
    if n is None:
        return "—"
    n = int(n)
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def make_client(proxy: Optional[str], lang: str) -> Client:
    timeout = Timeout(connect=30.0, read=60.0, write=30.0, pool=5.0)
    return Client(language=lang, proxy=proxy, timeout=timeout)


async def load_cookies(client: Client, cookies_file: str) -> bool:
    """Load cookies from file (supports both array and dict formats)."""
    path = Path(cookies_file)
    if not path.exists():
        return False
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            cookies = {
                c["name"]: c["value"]
                for c in data
                if "name" in c
                and "value" in c
                and ("twitter.com" in c.get("domain", "") or "x.com" in c.get("domain", ""))
            }
            client.set_cookies(cookies)
        elif isinstance(data, dict):
            client.set_cookies(data)
        return True
    except Exception as e:
        err_console.print(f"[yellow]Warning:[/] Failed to load cookies: {e}")
        return False


def require_auth(ctx: click.Context) -> tuple[Client, asyncio.AbstractEventLoop]:
    """Build client and verify cookies exist. Exits on failure."""
    client = make_client(ctx.obj["proxy"], ctx.obj["lang"])

    async def _auth():
        ok = await load_cookies(client, ctx.obj["cookies_file"])
        if not ok:
            err_console.print(
                "[yellow]No cookies found.[/] Run [cyan]twikit-cli auth login[/] or "
                "[cyan]twikit-cli auth set-cookies <file>[/] first."
            )
            raise SystemExit(1)

    asyncio.run(_auth())
    return client


# ─── Root Command ─────────────────────────────────────────────────────────────


@click.group()
@click.version_option(version="1.0.0", prog_name="twikit-cli")
@click.option(
    "--proxy",
    envvar="TWIKIT_PROXY",
    default=None,
    metavar="URL",
    help="Proxy URL  [env: TWIKIT_PROXY]",
)
@click.option(
    "--cookies",
    "cookies_file",
    envvar="TWIKIT_COOKIES",
    default=str(DEFAULT_COOKIES_FILE),
    show_default=True,
    help="Path to cookies JSON file  [env: TWIKIT_COOKIES]",
)
@click.option("--lang", default="en-US", show_default=True, help="Language code")
@click.option("--json-output", is_flag=True, default=False, help="Output raw JSON")
@click.pass_context
def cli(ctx, proxy, cookies_file, lang, json_output):
    """Twitter/X information retrieval CLI powered by twikit."""
    ctx.ensure_object(dict)
    ctx.obj.update(proxy=proxy, cookies_file=cookies_file, lang=lang, json_output=json_output)


# ─── Auth ─────────────────────────────────────────────────────────────────────


@cli.group()
def auth():
    """Authentication management."""


@auth.command("login")
@click.option("--username", prompt=True, help="Twitter username, email, or phone")
@click.option("--password", prompt=True, hide_input=True, help="Twitter password")
@click.option("--email", default=None, help="Secondary email (if required by Twitter)")
@click.pass_context
def auth_login(ctx, username, password, email):
    """Login with Twitter credentials and save cookies."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    cookies_file = ctx.obj["cookies_file"]
    client = make_client(ctx.obj["proxy"], ctx.obj["lang"])

    async def _run():
        with console.status("[cyan]Logging in…[/]"):
            await client.login(
                auth_info_1=username,
                auth_info_2=email,
                password=password,
                cookies_file=cookies_file,
            )
        console.print(f"[green]✓[/] Logged in! Cookies saved to [cyan]{cookies_file}[/]")

    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        sys.exit(130)
    except Exception as e:
        err_console.print(f"[red]Login failed:[/] {e}")
        sys.exit(1)


@auth.command("set-cookies")
@click.argument("cookies_path", type=click.Path(exists=True))
@click.pass_context
def auth_set_cookies(ctx, cookies_path):
    """Copy a browser-exported cookies file into the config directory."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    dest = ctx.obj["cookies_file"]
    shutil.copy2(cookies_path, dest)
    console.print(f"[green]✓[/] Cookies copied to [cyan]{dest}[/]")


# ─── Search ───────────────────────────────────────────────────────────────────


@cli.group()
def search():
    """Search tweets and users."""


@search.command("tweets")
@click.argument("query")
@click.option(
    "--type",
    "search_type",
    default="Latest",
    type=click.Choice(["Latest", "Top", "Media"]),
    show_default=True,
    help="Search type",
)
@click.option("--count", default=20, show_default=True, help="Number of results")
@click.pass_context
def search_tweets(ctx, query, search_type, count):
    """Search tweets by QUERY.

    \b
    Examples:
      twikit-cli search tweets "python programming"
      twikit-cli search tweets "#AI" --type Top --count 10
    """
    client = require_auth(ctx)

    async def _run():
        with console.status(f"[cyan]Searching '{query}'…[/]"):
            tweets = await client.search_tweet(query, search_type, count=count)

        tweet_list = list(tweets)

        if ctx.obj["json_output"]:
            from .formatters import tweet_to_dict
            results = [tweet_to_dict(t) for t in tweet_list]
            console.print_json(json.dumps(results, ensure_ascii=False))
            return

        table = Table(
            title=f"Search: [cyan]{query}[/] ({search_type})",
            box=box.ROUNDED,
            show_lines=True,
            expand=True,
        )
        table.add_column("Author", style="cyan", no_wrap=True, width=18)
        table.add_column("Tweet", ratio=3)
        table.add_column("Date", style="dim", width=11)
        table.add_column("❤", justify="right", style="red", width=7)
        table.add_column("🔁", justify="right", style="green", width=7)
        table.add_column("💬", justify="right", style="blue", width=7)

        for t in tweet_list:
            text = (t.full_text or t.text or "").replace("\n", " ")
            if len(text) > 200:
                text = text[:197] + "…"
            date = (t.created_at or "")[:10]
            table.add_row(
                f"@{t.user.screen_name}",
                text,
                date,
                fmt_num(t.favorite_count),
                fmt_num(t.retweet_count),
                fmt_num(t.reply_count),
            )

        console.print(table)
        console.print(f"[dim]{len(tweet_list)} results[/]")

    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled[/]")
        sys.exit(130)
    except Exception as e:
        err_console.print(f"[red]Error:[/] {e}")
        sys.exit(1)


@search.command("users")
@click.argument("query")
@click.option("--count", default=10, show_default=True, help="Number of results")
@click.pass_context
def search_users_cmd(ctx, query, count):
    """Search for Twitter users by QUERY.

    \b
    Example:
      twikit-cli search users "OpenAI"
    """
    client = require_auth(ctx)

    async def _run():
        with console.status(f"[cyan]Searching users '{query}'…[/]"):
            users = await client.search_user(query, count=count)

        user_list = list(users)

        if ctx.obj["json_output"]:
            from .formatters import user_to_dict
            results = [user_to_dict(u) for u in user_list]
            console.print_json(json.dumps(results, ensure_ascii=False))
            return

        table = Table(
            title=f"Users: [cyan]{query}[/]",
            box=box.ROUNDED,
            expand=True,
        )
        table.add_column("Name", style="bold cyan", width=20)
        table.add_column("@Handle", style="cyan", width=20)
        table.add_column("Bio", ratio=2)
        table.add_column("Followers", justify="right", style="green", width=10)
        table.add_column("✓", justify="center", width=3)

        for u in user_list:
            bio = (u.description or "").replace("\n", " ")
            if len(bio) > 100:
                bio = bio[:97] + "…"
            verified = "[blue]✓[/]" if u.is_blue_verified else ""
            table.add_row(
                u.name or "",
                f"@{u.screen_name}",
                bio,
                fmt_num(u.followers_count),
                verified,
            )

        console.print(table)

    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled[/]")
        sys.exit(130)
    except Exception as e:
        err_console.print(f"[red]Error:[/] {e}")
        sys.exit(1)


# ─── User ─────────────────────────────────────────────────────────────────────


@cli.group()
def user():
    """User profile and timeline operations."""


@user.command("info")
@click.argument("screen_name")
@click.pass_context
def user_info(ctx, screen_name):
    """Show profile for a user (leading @ is optional).

    \b
    Example:
      twikit-cli user info elonmusk
      twikit-cli user info @OpenAI
    """
    screen_name = screen_name.lstrip("@")
    client = require_auth(ctx)

    async def _run():
        with console.status(f"[cyan]Fetching @{screen_name}…[/]"):
            try:
                u = await client.get_user_by_screen_name(screen_name)
            except UserNotFound:
                err_console.print(f"[red]User @{screen_name} not found.[/]")
                raise SystemExit(1)

        if ctx.obj["json_output"]:
            from .formatters import user_to_dict
            data = user_to_dict(u)
            console.print_json(json.dumps(data, ensure_ascii=False))
            return

        verified = " [blue]✓[/]" if u.is_blue_verified else ""
        protected = " [yellow]🔒[/]" if u.protected else ""
        content = (
            f"[bold cyan]{u.name}[/]{verified}{protected}\n"
            f"[dim]@{u.screen_name}[/]  ·  ID: {u.id}\n\n"
            f"{u.description or '[dim]No bio[/]'}\n\n"
            f"[dim]📍 {u.location or 'N/A'}   🗓 Joined {(u.created_at or '')[:10]}[/]\n\n"
            f"[green]Followers:[/] {fmt_num(u.followers_count)}   "
            f"[cyan]Following:[/] {fmt_num(u.following_count)}   "
            f"[yellow]Tweets:[/] {fmt_num(u.statuses_count)}   "
            f"[red]Likes:[/] {fmt_num(u.favourites_count)}"
        )
        console.print(Panel(content, title="User Profile", border_style="cyan", expand=False))

    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled[/]")
        sys.exit(130)
    except SystemExit:
        raise
    except Exception as e:
        err_console.print(f"[red]Error:[/] {e}")
        sys.exit(1)


@user.command("tweets")
@click.argument("screen_name")
@click.option(
    "--type",
    "tweet_type",
    default="Tweets",
    type=click.Choice(["Tweets", "Replies", "Media", "Likes"]),
    show_default=True,
    help="Timeline type",
)
@click.option("--count", default=20, show_default=True, help="Number of tweets")
@click.pass_context
def user_tweets(ctx, screen_name, tweet_type, count):
    """Get a user's tweet timeline.

    \b
    Examples:
      twikit-cli user tweets elonmusk
      twikit-cli user tweets @OpenAI --type Media --count 10
    """
    screen_name = screen_name.lstrip("@")
    client = require_auth(ctx)

    async def _run():
        with console.status(f"[cyan]Fetching @{screen_name}…[/]"):
            try:
                u = await client.get_user_by_screen_name(screen_name)
            except UserNotFound:
                err_console.print(f"[red]User @{screen_name} not found.[/]")
                raise SystemExit(1)

        with console.status(f"[cyan]Loading {tweet_type}…[/]"):
            tweets = await client.get_user_tweets(u.id, tweet_type, count=count)

        tweet_list = list(tweets)

        if ctx.obj["json_output"]:
            from .formatters import tweet_to_dict
            results = [tweet_to_dict(t) for t in tweet_list]
            console.print_json(json.dumps(results, ensure_ascii=False))
            return

        table = Table(
            title=f"@{screen_name} — {tweet_type}",
            box=box.ROUNDED,
            show_lines=True,
            expand=True,
        )

        table.add_column("Date", style="dim", width=11)
        table.add_column("TweetID", style="cyan", width=20)
        table.add_column("Tweet", ratio=4)
        table.add_column("favorite", justify="right", style="red", width=7)
        table.add_column("repost", justify="right", style="green", width=7)
        table.add_column("reply", justify="right", style="blue", width=7)

        for t in tweet_list:
            text = (t.full_text or t.text or "").replace("\n", " ")
            if len(text) > 250:
                text = text[:247] + "…"
            table.add_row(
                (t.created_at or "")[:10],
                str(t.id or ""),
                text,
                fmt_num(t.favorite_count),
                fmt_num(t.retweet_count),
                fmt_num(t.reply_count),
            )

        console.print(table)
        console.print(f"[dim]{len(tweet_list)} tweets[/]")

    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled[/]")
        sys.exit(130)
    except SystemExit:
        raise
    except Exception as e:
        err_console.print(f"[red]Error:[/] {e}")
        sys.exit(1)


@user.command("followers")
@click.argument("screen_name")
@click.option("--count", default=20, show_default=True, help="Number of followers")
@click.pass_context
def user_followers(ctx, screen_name, count):
    """Get a user's followers list.

    \b
    Example:
      twikit-cli user followers elonmusk --count 20
    """
    screen_name = screen_name.lstrip("@")
    client = require_auth(ctx)

    async def _run():
        with console.status(f"[cyan]Fetching @{screen_name}…[/]"):
            try:
                u = await client.get_user_by_screen_name(screen_name)
            except UserNotFound:
                err_console.print(f"[red]User @{screen_name} not found.[/]")
                raise SystemExit(1)

        with console.status("[cyan]Loading followers…[/]"):
            followers = await client.get_user_followers(u.id, count=count)

        follower_list = list(followers)

        if ctx.obj["json_output"]:
            from .formatters import user_to_dict
            results = [user_to_dict(f) for f in follower_list]
            console.print_json(json.dumps(results, ensure_ascii=False))
            return

        table = Table(
            title=f"@{screen_name}'s Followers",
            box=box.ROUNDED,
            expand=True,
        )
        table.add_column("Name", style="bold cyan", width=20)
        table.add_column("@Handle", style="cyan", width=20)
        table.add_column("Bio", ratio=2)
        table.add_column("Followers", justify="right", style="green", width=10)

        for f in follower_list:
            bio = (f.description or "").replace("\n", " ")
            if len(bio) > 80:
                bio = bio[:77] + "…"
            table.add_row(
                f.name or "",
                f"@{f.screen_name}",
                bio,
                fmt_num(f.followers_count),
            )

        console.print(table)
        console.print(f"[dim]{len(follower_list)} followers shown[/]")

    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled[/]")
        sys.exit(130)
    except SystemExit:
        raise
    except Exception as e:
        err_console.print(f"[red]Error:[/] {e}")
        sys.exit(1)


# ─── Trends ───────────────────────────────────────────────────────────────────


@cli.command("trends")
@click.option(
    "--category",
    default="trending",
    type=click.Choice(["trending", "for-you", "news", "sports", "entertainment"]),
    show_default=True,
    help="Trend category",
)
@click.option("--count", default=20, show_default=True, help="Number of trends")
@click.pass_context
def trends_cmd(ctx, category, count):
    """Get trending topics.

    \b
    Examples:
      twikit-cli trends
      twikit-cli trends --category news
      twikit-cli trends --category sports --count 10
    """
    client = require_auth(ctx)

    async def _run():
        with console.status(f"[cyan]Fetching {category} trends…[/]"):
            trend_list = await client.get_trends(category, count=count)

        if ctx.obj["json_output"]:
            results = [
                {
                    "name": t.name,
                    "tweets_count": t.tweets_count,
                    "domain_context": t.domain_context,
                }
                for t in trend_list
            ]
            console.print_json(json.dumps(results, ensure_ascii=False))
            return

        table = Table(
            title=f"Trending — [cyan]{category.title()}[/]",
            box=box.ROUNDED,
        )
        table.add_column("#", style="dim", width=4, justify="right")
        table.add_column("Topic", style="bold cyan", min_width=25)
        table.add_column("Context", style="dim", min_width=20)
        table.add_column("Volume", justify="right", style="green", width=10)

        for i, t in enumerate(trend_list, 1):
            table.add_row(
                str(i),
                t.name,
                t.domain_context or "—",
                t.tweets_count or "—",
            )

        console.print(table)

    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled[/]")
        sys.exit(130)
    except Exception as e:
        err_console.print(f"[red]Error:[/] {e}")
        sys.exit(1)


# ─── Tweet ────────────────────────────────────────────────────────────────────


@cli.group()
def tweet():
    """Tweet retrieval operations."""


@tweet.command("get")
@click.argument("tweet_id")
@click.pass_context
def tweet_get(ctx, tweet_id):
    """Fetch and display a single tweet by ID.

    \b
    Example:
      twikit-cli tweet get 1234567890123456789
    """
    client = require_auth(ctx)

    async def _run():
        with console.status(f"[cyan]Fetching tweet {tweet_id}…[/]"):
            try:
                response = await client.gql.tweet_result_by_rest_id(tweet_id)
                tweet_result = response[0].get("data", {}).get("tweetResult", {}).get("result", {})

                # 提取article数据
                article_data = tweet_result.get("article", {})

                # 解析article内容
                if article_data:
                    from .article_parser import parse_article_content, print_article
                    article_info = parse_article_content(article_data)

                    if ctx.obj["json_output"]:
                        from .formatters import article_to_dict
                        article_json = article_to_dict(article_info)
                        console.print_json(json.dumps(article_json, ensure_ascii=False))
                        return

                    print_article(article_info)
                    return

                # 处理普通tweet
                legacy = tweet_result.get("legacy", {})
                user_result = tweet_result.get("core", {}).get("user_results", {}).get("result", {})
                user_legacy = user_result.get("legacy", {})

                if ctx.obj["json_output"]:
                    from .formatters import gql_tweet_to_dict
                    data = gql_tweet_to_dict(tweet_result, legacy, user_result, user_legacy)
                    console.print_json(json.dumps(data, ensure_ascii=False))
                    return

                text = legacy.get("full_text", "")
                user_name = user_legacy.get("name", "Unknown")
                screen_name = user_legacy.get("screen_name", "unknown")
                created_at = legacy.get("created_at", "")

                content = (
                    f"[bold cyan]{user_name}[/] [dim]@{screen_name}[/]\n"
                    f"[dim]{created_at}[/]\n\n"
                    f"{text}\n\n"
                    f"[red]❤ {fmt_num(legacy.get('favorite_count', 0))}[/]   "
                    f"[green]🔁 {fmt_num(legacy.get('retweet_count', 0))}[/]   "
                    f"[blue]💬 {fmt_num(legacy.get('reply_count', 0))}[/]   "
                    f"[yellow]🔖 {fmt_num(legacy.get('bookmark_count', 0))}[/]   "
                    f"[dim]👁 {fmt_num(tweet_result.get('views', {}).get('count', 0))}[/]"
                )

                media = legacy.get("entities", {}).get("media", [])
                if media:
                    media_types = [m.get("type", "unknown") for m in media]
                    content += f"\n[dim]Media: {', '.join(media_types)}[/]"

                console.print(Panel(content, title=f"Tweet {tweet_id}", border_style="cyan", expand=False))

            except TweetNotAvailable:
                err_console.print(f"[red]Tweet {tweet_id} not found or unavailable.[/]")
                raise SystemExit(1)

    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled[/]")
        sys.exit(130)
    except SystemExit:
        raise
    except Exception as e:
        err_console.print(f"[red]Error:[/] {e}")
        sys.exit(1)


# ─── Entry Point ──────────────────────────────────────────────────────────────


def main():
    try:
        cli(standalone_mode=True)
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled[/]")
        sys.exit(130)


if __name__ == "__main__":
    main()
