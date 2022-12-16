# -*- coding: utf-8 -*-
# +-------------------------------------------------------------------
# | Date: 2022/10/22
# +-------------------------------------------------------------------
# | Author: Pluto <i@aoaostar.com>
# +-------------------------------------------------------------------

retry = 3
asyncio = {
    "semaphore": 5,
    "sleep": 0,
}

http = {

    "headers": {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 '
                      'Safari/537.36 '
    },
    "timeout": 10,
    "proxy": '',
    "http_proxy": '',
}
