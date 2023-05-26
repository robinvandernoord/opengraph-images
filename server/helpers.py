# re-used code
import hashlib


def simple_hash(string: str | bytes) -> str:
    # make sure string is converted to bytes so sha1 can handle it AND mypy is happy
    # string = AnyString but that confuses mypy for some reason
    _bytes: bytes = string.encode("UTF-8") if isinstance(string, str) else string

    _hash = hashlib.new("sha1", usedforsecurity=False)  # only for file storing, NO SECURITY REASON!!

    return _hash.hexdigest()
