# -*- coding: utf-8 -*-
# +-------------------------------------------------------------------
# | Date: 2022/10/21
# +-------------------------------------------------------------------
# | Author: Pluto <i@aoaostar.com>
# +-------------------------------------------------------------------
import os


def save(filename, data):
    path_dirname = os.path.dirname(filename)
    if not os.path.exists(path_dirname):
        os.makedirs(path_dirname, 755)

    with open(filename, 'wb') as f:
        f.write(data)
        f.flush()


def save_str(filename, data, encoding='utf-8'):
    path_dirname = os.path.dirname(filename)
    if not os.path.isdir(path_dirname):
        os.makedirs(path_dirname, 755)

    with open(filename, 'w', encoding=encoding) as f:
        f.write(data)
        f.flush()


def read_str(filename,  encoding='utf-8'):

    with open(filename, 'r', encoding=encoding) as f:
        return f.read()
