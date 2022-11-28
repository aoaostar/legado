# -*- coding: utf-8 -*-
# +-------------------------------------------------------------------
# | Date: 2022/11/28
# +-------------------------------------------------------------------
# | Author: Pluto <i@aoaostar.com>
# +-------------------------------------------------------------------
import os
import shutil


def del_file(path_data):
    if os.path.isfile(path_data):
        os.remove(path_data)
    else:
        shutil.rmtree(path_data)


if __name__ == '__main__':
    listdir = os.listdir('./')

    for d in listdir:
        if d not in ['cache', 'index.html', 'README.md', 'CNAME', 'LISENCE', '.git']:
            del_file(d)
