import collections
import json
import os
import time
import typing
from hashlib import sha1

import imgkit
import yatl
from flask import Response
from typing_extensions import NotRequired


class Context(typing.TypedDict):
    icon: str
    title: str
    img: str

    template: NotRequired[str]


OG_WIDTH = 1200
OG_HEIGHT = 630


def generate_image(ctx: Context):
    options = {
        "format": "png",
        # opengraph image size is 1200x630:
        "width": OG_WIDTH,
        "height": OG_HEIGHT,
        "crop-w": OG_WIDTH,
        "crop-h": OG_HEIGHT,
        "encoding": "UTF-8",
    }

    with open(ctx.get("template", "template.html")) as f:
        rendered = yatl.render(stream=f, context=ctx, delimiters="[[ ]]")

    return imgkit.from_string(rendered, False, options=options)


def demo():
    img = generate_image(
        dict(
            img="https://news.su6.nl/static/icons/nu.svg",
            title="Door deze ontdekking gaat je telefoon straks tot twee keer zo lang mee",
            icon="https://media.nu.nl/m/zh2x98aada6s_sqr256.jpg/door-deze-ontdekking-gaat-je-telefoon-straks-tot-twee-keer-zo-lang-mee.jpg",
        )
    )

    with open("temp.png", "wb") as f:
        f.write(img)


if __name__ == "__main__":
    demo()


A_DAY = 60 * 60 * 24


def remove_old_tmp():
    for f in os.listdir("/tmp"):
        print("checking", f)
        if (
            f.startswith("__cached__")
            and os.path.getmtime(os.path.join("/tmp", f)) < time.time() - A_DAY
        ):
            print("removing", f)
            os.remove(os.path.join("/tmp", f))
            continue


def remove_all_existing_tmp():
    print("Removing all old")
    # sources (according to copilot):
    #   https://stackoverflow.com/a/185941 and https://stackoverflow.com/a/185936
    for f in os.listdir("/tmp"):
        if f.startswith("__cached__"):
            os.remove(os.path.join("/tmp", f))


remove_all_existing_tmp()


def get_path(hash):
    return os.path.join("/tmp", f"__cached__{hash}.png")


def ctx_to_hash(ctx: Context):
    ctx_str = json.dumps(collections.OrderedDict(sorted(ctx.items())))
    ctx_bytes = ctx_str.encode()
    ctx_hash = sha1(ctx_bytes)

    return ctx_hash.hexdigest()


def ctx_to_hash_path(ctx: Context):
    ctx_hex = ctx_to_hash(ctx)

    return get_path(ctx_hex)


def _cache_generate(ctx: Context):
    # cron: docker-compose restart nightly to empty old cache

    hash_path = ctx_to_hash_path(ctx)

    if os.path.exists(hash_path):
        with open(hash_path, "rb") as f:
            return f.read()

    img = generate_image(ctx)

    with open(hash_path, "wb") as f:
        f.write(img)

    # cleanup disk:
    remove_old_tmp()

    return img


def _generate(ctx: Context):
    resp = Response(_cache_generate(ctx))
    resp.headers["Content-Type"] = "image/png"
    return resp
