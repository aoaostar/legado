# -*- coding: utf-8 -*-
# +-------------------------------------------------------------------
# | Date: 2022/11/29
# +-------------------------------------------------------------------
# | Author: Pluto <i@aoaostar.com>
# +-------------------------------------------------------------------
import urllib.parse

from common import async_util


async def check_book(book_rule: dict):
    urlparse = urllib.parse.urlparse(book_rule['bookSourceUrl'])
    hostname = urlparse.hostname
    port = urlparse.port
    if hostname is None and 'searchUrl' in book_rule:
        urlparse2 = urllib.parse.urlparse(book_rule['searchUrl'])
        if urlparse2.hostname is not None:
            hostname = urlparse2.hostname
            port = urlparse2.port
    if hostname is None:
        return True, '无法获取到hostname'
    try:
        ping = await async_tcp_ping(host=hostname, port=port or 80, timeout=10)
        return True, f'{hostname} %.f ms' % ping
    except Exception as e:
        return False, f"{hostname} {e}"


async def async_tcp_ping(host, port, timeout=10):
    import asyncio
    import async_timeout
    from timeit import default_timer as timer
    time_start = timer()
    num = 3
    for i in range(num):
        try:
            async with async_timeout.timeout(delay=timeout):
                await asyncio.open_connection(host, port)
            break
        except Exception as e:
            if i == num:
                raise e
    time_end = timer()
    time_cost_milliseconds = (time_end - time_start) * 1000.0
    return time_cost_milliseconds


if __name__ == '__main__':
    print(async_util.run(check_book({
        "bookSourceUrl": "https://www.aoaostar.com",
    })))
