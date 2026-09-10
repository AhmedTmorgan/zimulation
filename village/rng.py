"""تيارات عشوائية حتمية: نفس البذرة ⇒ نفس التاريخ بالحرف."""

import random
from zlib import crc32


class Streams:
    """مولّدات مستقلة لكل نظام، حتى لا يفسد ترتيب استدعاء نظامٍ نتائج غيره."""

    __slots__ = ("seed", "_cache")

    def __init__(self, seed: int):
        self.seed = seed
        self._cache = {}

    def get(self, name: str) -> random.Random:
        r = self._cache.get(name)
        if r is None:
            h = (self.seed * 2654435761 + crc32(name.encode("utf-8"))) & 0xFFFFFFFFFFFF
            r = random.Random(h)
            self._cache[name] = r
        return r
