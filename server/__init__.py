import collections
import json
import os
import time
from hashlib import sha1

from flask import Flask, Response, request

from .lib.create import generate_image, Context

if False:
    from ..create import generate_image, Context

app = Flask(__name__)

A_DAY = 60 * 60 * 24


def remove_old_tmp():
    for f in os.listdir("/tmp"):
        print("checking", f)
        if f.startswith("__cached__"):
            if os.path.getmtime(os.path.join("/tmp", f)) < time.time() - A_DAY:
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
    return os.path.join(f"/tmp", f"__cached__{hash}.png")


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
    resp.headers['Content-Type'] = 'image/png'
    return resp


@app.route('/', methods=["GET"])
def home():
    return _generate({
        "title": "Door deze ontdekking gaat je telefoon straks tot twee keer zo lang mee",
        "icon": "https://news.su6.nl/static/icons/nu.svg",
        "img": "https://media.nu.nl/m/zh2x98aada6s_sqr256.jpg/door-deze-ontdekking-gaat-je-telefoon-straks-tot-twee-keer-zo-lang-mee.jpg",
    })


@app.route("/", methods=["POST"])
def generate():
    data = request.get_json()

    return _generate(data)
