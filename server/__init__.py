from flask import Flask, request, abort, Response

from .opengraph import _generate
from .tts import tts, Fresh, Cached

app = Flask(__name__)
app.url_map.strict_slashes = False


#######################
#      OPENGRAPH      #
#######################


@app.route("/", methods=["GET"])
def home():
    return "Possible Routes: /generate, /demo ; /tts"


@app.route("/demo", methods=["GET"])
def demo():
    return _generate(
        {
            "title": "Door deze ontdekking gaat je telefoon straks tot twee keer zo lang mee",
            "icon": "https://news.su6.nl/static/icons/nu.svg",
            "img": "https://media.nu.nl/m/zh2x98aada6s_sqr256.jpg/door-deze-ontdekking-gaat-je-telefoon-straks-tot-twee-keer-zo-lang-mee.jpg",
        }
    )


@app.route("/", methods=["POST"])
def generate():
    data = request.get_json()

    return _generate(data)


#######################
#         TTS         #
#######################


@app.route("/tts", methods=["GET", "POST"])
def home_tts():
    return (
        "Please give plain text (separated by _ instead of spaces) "
        "or base64 (with '+' replaced with '.', '/' replaced with '_' and '=' replaced with '-') "
        "or base58 "
        "to this endpoint. "
        "Example: /tts/hi, /tts/b64/aGk-, /tts/b58/8wr",
        400,
    )


def _tts(possibly_encoded_text, encoding):
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
        raise abort(400, "Invalid Request!") from e
    return response


# @app.route("/tts/<possibly_encoded_text>", methods=["GET", "POST"])
# def generate_tts(possibly_encoded_text):
#     return _tts(possibly_encoded_text)


@app.route("/tts/<text>", methods=["GET", "POST"])
def generate_tts_raw(text):
    return _tts(text, encoding=None)


@app.route("/tts/b64/<encoded_text>", methods=["GET", "POST"])
def generate_tts_b64(encoded_text):
    return _tts(encoded_text, encoding="b64")


@app.route("/tts/b58/<encoded_text>", methods=["GET", "POST"])
def generate_tts_b58(encoded_text):
    return _tts(encoded_text, encoding="b58")
