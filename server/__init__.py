import os

from flask import Flask, Response, request

from .lib.create import generate_image, Context

if False:
    from ..create import generate_image, Context

app = Flask(__name__)


def _generate(ctx: Context):
    resp = Response(generate_image(ctx))
    resp.headers['Content-Type'] = 'image/png'
    return resp


@app.route('/', methods=["GET"])
def home():
    return _generate({
        "icon": "https://news.su6.nl/static/icons/nu.svg",
        "title": "Door deze ontdekking gaat je telefoon straks tot twee keer zo lang mee",
        "img": "https://media.nu.nl/m/zh2x98aada6s_sqr256.jpg/door-deze-ontdekking-gaat-je-telefoon-straks-tot-twee-keer-zo-lang-mee.jpg",
    })


@app.route("/", methods=["POST"])
def generate():
    data = request.get_json()

    return _generate(data)
