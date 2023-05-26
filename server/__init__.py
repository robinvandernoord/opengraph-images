import sys
import typing

from flask import Flask, Response, abort, request

from .opengraph import _generate
from .tts import Cached, EncodingOptions, Fresh, tts

app = Flask(__name__)
app.url_map.strict_slashes = False


#######################
#      OPENGRAPH      #
#######################


@app.route("/", methods=["GET"])
def home() -> str:
    return "Possible Routes: /generate, /demo ; /tts"


@app.route("/demo", methods=["GET"])
def demo() -> Response:
    return _generate(
        {
            "title": "Door deze ontdekking gaat je telefoon straks tot twee keer zo lang mee",
            "icon": "https://news.su6.nl/static/icons/nu.svg",
            "img": "https://media.nu.nl/m/zh2x98aada6s_sqr256.jpg/door-deze-ontdekking-gaat-je-telefoon-straks-tot-twee-keer-zo-lang-mee.jpg",
        }
    )


@app.route("/", methods=["POST"])
def generate() -> Response:
    data = request.get_json()

    return _generate(data)


#######################
#         TTS         #
#######################


@app.route("/tts", methods=["GET", "POST"])
def home_tts() -> tuple[str, int]:
    return (
        "Please give plain text (separated by _ instead of spaces) "
        "or base64 (with '+' replaced with '.', '/' replaced with '_' and '=' replaced with '-') "
        "or base58 "
        "to this endpoint. "
        "Example: /tts/raw/hi, /tts/b64/aGk-, /tts/b58/8wr",
        400,
    )


def _tts(possibly_encoded_text: str, encoding: EncodingOptions) -> Response | typing.Never:
    try:
        if not possibly_encoded_text:
            raise abort(404, "Missing Text!")

        result = tts(possibly_encoded_text, encoding)

        match result:
            case Fresh(content):
                x_status = "fresh"
            case Cached(content):
                x_status = "cached"
            case _:
                # Empty(_)
                raise ValueError("No Content!")

        response = Response(content, content_type="audio/mp3")

        response.headers["Content-Type"] = "audio/mp3"
        # fix duration:
        response.headers["Accept-Ranges"] = "bytes"
        response.headers["Content-Range"] = "bytes 0-"
        response.headers["Content-Disposition"] = "inline; filename=" + "tts.wav"
        response.headers["X-Status"] = x_status
    except Exception as e:
        print(e, file=sys.stderr)
        raise abort(400, "Invalid Request!") from e
    return response


@app.route("/tts/<_>", methods=["GET", "POST"])
def generate_tts(_: str) -> typing.Never:
    print("Received:", _, file=sys.stderr)
    abort(400, "you NEED to specify encoding type! (raw, b58 or b53")


# @app.route("/tts/<text_or_b58>", methods=["GET", "POST"])
# def generate_tts_guess(text_or_b58):
#     decoded = guess_encoding(text_or_b58, options=('b58', None))
#     return _tts(decoded, encoding=None)


@app.route("/tts/raw/<text>", methods=["GET", "POST"])
def generate_tts_raw(text: str) -> Response:
    return _tts(text, encoding=None)


@app.route("/tts/b64/<encoded_text>", methods=["GET", "POST"])
def generate_tts_b64(encoded_text: str) -> Response:
    return _tts(encoded_text, encoding="b64")


@app.route("/tts/b58/<encoded_text>", methods=["GET", "POST"])
def generate_tts_b58(encoded_text: str) -> Response:
    return _tts(encoded_text, encoding="b58")
