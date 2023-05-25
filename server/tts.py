import os
import typing
from base64 import b64decode
from dataclasses import dataclass
from hashlib import sha1

from base58 import b58decode
from diskcache import Index
from google.cloud import texttospeech

AUTH_JSON = "/private/su6-news-service-account.json"


def to_str(bytes_or_string):
    if isinstance(bytes_or_string, str):
        return bytes_or_string
    elif isinstance(bytes_or_string, bytes):
        return bytes_or_string.decode()
    else:
        return str(bytes_or_string)


class TTSModel:
    def __init__(self):
        self.authenticate()

        self.client = texttospeech.TextToSpeechClient()
        self.voice = texttospeech.VoiceSelectionParams(
            language_code="nl-NL",
            name="nl-NL-Wavenet-D",
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
        )

        self.audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )

    def authenticate(self):
        # https://stackoverflow.com/questions/44328277/how-to-auth-to-google-cloud-using-service-account-in-python
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = AUTH_JSON

    def process(self, original_text):
        if to_str(original_text).startswith("<speak>"):
            input_text = texttospeech.SynthesisInput(ssml=original_text)
        else:
            input_text = texttospeech.SynthesisInput(text=original_text)

        return self.client.synthesize_speech(
            request={
                "input": input_text,
                "voice": self.voice,
                "audio_config": self.audio_config,
            }
        )


def _synthesize_text(text):
    """Synthesizes speech from the input string of text."""
    tts = TTSModel()
    # Note: the voice can also be specified by name.
    # Names of voices can be retrieved with client.list_voices().

    return tts.process(text).audio_content


def simple_hash(string):
    if isinstance(string, str):
        string = string.encode("UTF-8")
    return sha1(string).hexdigest()


dc = Index("/tmp/diskcache-tts")

T = typing.TypeVar("T")


@dataclass
class Result(typing.Generic[T]):
    value: T = None


class Cached(Result):
    ...


class Fresh(Result):
    ...


class Empty(Result):
    ...


def synthesize_text(text: bytes | str) -> Result[bytes]:
    if not text:
        return Empty()

    text_hash = simple_hash(text)
    print(f"hashed: {text_hash}")
    if cached := dc.get(text_hash):
        return Cached(cached)

    print("fresh!")
    content = _synthesize_text(text)

    dc[text_hash] = content

    return Fresh(content)


def tts(
    possibly_encoded_text: bytes | str,
    encoding: typing.Literal["b58", "b64", None] = None,
):
    text: bytes | str | None = None
    match encoding:
        case "b64":
            text: bytes = b64decode(
                possibly_encoded_text.replace(".", "+")
                .replace("_", "/")
                .replace("-", "=")
            )
        case "b58":
            text: bytes = b58decode(possibly_encoded_text)
        case None:
            text: str = possibly_encoded_text.replace("_", " ")

    return synthesize_text(text)
