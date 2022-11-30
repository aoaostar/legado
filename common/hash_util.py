# -*- coding: utf-8 -*-
# +-------------------------------------------------------------------
# | Date: 2022/10/21
# +-------------------------------------------------------------------
# | Author: Pluto <i@aoaostar.com>
# +-------------------------------------------------------------------
import hashlib


def sha1(data: str):
    s = hashlib.sha1()
    s.update(data.encode('utf-8'))
    return s.hexdigest()


def file_sha1(filepath):
    s = hashlib.sha1()
    with open(filepath, "rb") as f:
        while True:
            b = f.read(2048)
            if not b:
                break
            s.update(b)
    return s.hexdigest()
