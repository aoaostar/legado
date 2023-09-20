# -*- coding: utf-8 -*-
# +-------------------------------------------------------------------
# | Date: 2022/10/21
# +-------------------------------------------------------------------
# | Author: Pluto <i@aoaostar.com>
# +-------------------------------------------------------------------
import asyncio

from aiohttp import ClientResponse, ClientTimeout

from common import config

from aiohttp_retry import RetryClient, ClientSession


class Request:

    def __init__(self, *args, **kwargs):
        self.client_session = ClientSession()
        self.retry_client = RetryClient(client_session=self.client_session)
        self.request = self.retry_client.request(*args, **kwargs)

    async def __aenter__(self) -> ClientResponse:
        return await self.request

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client_session.close()
        await self.retry_client.close()


def get(url, params=None, headers=None):
    if headers is None:
        headers = {}
    if params is None:
        params = {}
    return request("GET", url, params=params, headers={
        **config.http['headers'], **headers
    })


def request(method, url, params=None, headers=None, data=None):
    if headers is None:
        headers = {}
    if params is None:
        params = {}
    if data is None:
        data = {}

    return Request(
        method, config.http['http_proxy'] + url,
        params=params, proxy=config.http['proxy'],
        headers={**config.http['headers'], **headers},
        data=data, ssl=False,
        allow_redirects=True,
        timeout=ClientTimeout(total=config.http['timeout']))


def post(url, data=None, headers=None):
    if headers is None:
        headers = {}
    if data is None:
        data = {}
    return request("POST", url, data=data, headers={
        **config.http['headers'], **headers
    })


if __name__ == '__main__':
    async def test():
        for i in range(1):
            async with request("GET", "https://www.baidu.com") as r:
                print(r.status)


    asyncio.get_event_loop().run_until_complete(test())
