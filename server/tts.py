# import contextlib
import os
import typing
from base64 import b64decode
from hashlib import sha1

from base58 import b58decode
from diskcache import Index
from google.cloud import texttospeech
from google.cloud.texttospeech_v1 import SynthesizeSpeechResponse
from result import Ok, Err

AUTH_JSON = "/private/su6-news-service-account.json"


def to_str(bytes_or_string: str | bytes) -> str:
    if isinstance(bytes_or_string, str):
        return bytes_or_string
    elif isinstance(bytes_or_string, bytes):
        return bytes_or_string.decode()
    else:
        return str(bytes_or_string)


class TTSModel:
    def __init__(self) -> None:
        self.authenticate()

        self.client = texttospeech.TextToSpeechClient()
        self.voice = texttospeech.VoiceSelectionParams(
            language_code="nl-NL",
            name="nl-NL-Wavenet-D",
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
        )

        self.audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)

    def authenticate(self) -> None:
        # https://stackoverflow.com/questions/44328277/how-to-auth-to-google-cloud-using-service-account-in-python
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = AUTH_JSON

    def process(self, original_text: bytes | str) -> SynthesizeSpeechResponse:
        if to_str(original_text).startswith("<speak>"):
            synth_option = dict(ssml=original_text)
        else:
            synth_option = dict(text=original_text)

        # SynthesisInput is not typed properly so mypy think it expects a dict. So we use a dict and unpack it
        input_text = texttospeech.SynthesisInput(**synth_option)

        return self.client.synthesize_speech(
            request={
                "input": input_text,
                "voice": self.voice,
                "audio_config": self.audio_config,
            }
        )


def _synthesize_text(text: str | bytes) -> bytes:
    """Synthesizes speech from the input string of text."""
    tts_model = TTSModel()
    # Note: the voice can also be specified by name.
    # Names of voices can be retrieved with client.list_voices().
    response = tts_model.process(text)

    return response.audio_content


def simple_hash(string: str | bytes) -> str:
    # make sure string is converted to bytes so sha1 can handle it AND mypy is happy
    # string = AnyString but that confuses mypy for some reason
    _bytes: bytes = string.encode("UTF-8") if isinstance(string, str) else string

    return sha1(_bytes).hexdigest()


dc = Index("/tmp/diskcache-tts")

T = typing.TypeVar("T")  # type for success
E = typing.TypeVar("E")  # type for error


class Cached(Ok[T]):
    ...


class Fresh(Ok[T]):
    ...


class Empty(Err[E]):
    def __init__(self) -> None:
        # no value required on create,
        # will be just None thanks to this super call
        super().__init__(None)


# like result.Result but with the three options from above
CacheResult: typing.TypeAlias = Cached[T] | Fresh[T] | Empty[E]

EncodingOptions = typing.Literal["b58", "b64", "none"] | None

if typing.TYPE_CHECKING:

    @typing.overload
    def decode_from_encoding(possibly_encoded_text: str, encoding: typing.Literal["b58", "b64"]) -> bytes:
        """
        If an encoding is passed, bytes will be returned since possibly_encoded_text is an encoded string.
        """

    @typing.overload
    def decode_from_encoding(possibly_encoded_text: str, encoding: typing.Literal["none", None]) -> str:
        """
        If no encoding is passed, str will be returned since possibly_encoded_text is plain text
        (with _ replaced with ' ' because url reasons).
        """


def decode_from_encoding(possibly_encoded_text: str, encoding: EncodingOptions) -> bytes | str:
    match encoding:
        case "b64":
            return b64_decode_url(possibly_encoded_text)  # -> bytes
        case "b58":
            return b58decode(possibly_encoded_text)  # -> bytes
        case _:
            # allow both 'none' (str) and None (NoneType) to make mypy happier with the overload
            return possibly_encoded_text.replace("_", " ")  # -> str


def synthesize_text(text: bytes | str) -> CacheResult[bytes, None]:
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


def b64_decode_url(encoded_text: str) -> bytes:
    """
    URL-safe base64 variant
    """
    return b64decode(encoded_text.replace(".", "+").replace("_", "/").replace("-", "="))


# def guess_encoding(possibly_encoded: str, options: tuple):
#     if "b64" in options:
#         with contextlib.suppress(Exception):
#             return b64_decode_url(possibly_encoded)
#     if "b58" in options:
#         with contextlib.suppress(Exception):
#             return b58decode(possibly_encoded)
#
#     # no other option than string!
#     return possibly_encoded


def tts(
    possibly_encoded_text: str,
    encoding: EncodingOptions = None,
) -> CacheResult[bytes, None]:
    decoded = decode_from_encoding(possibly_encoded_text, encoding)

    return synthesize_text(decoded)
