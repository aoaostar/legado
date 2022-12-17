# -*- coding: utf-8 -*-
# +-------------------------------------------------------------------
# | Date: 2022/12/16
# +-------------------------------------------------------------------
# | Author: Pluto <i@aoaostar.com>
# +-------------------------------------------------------------------
from urllib.parse import urlparse, urlencode, parse_qs, urlunparse, urljoin

import aiohttp
from LegadoParser2.RuleJs.JS import EvalJs
from LegadoParser2.RuleUrl.BodyType import Body
from LegadoParser2.Search import parseSearchUrl, getSearchResult

from common import fetch


async def search(compiled_book_source, key, page=1):
    evalJS = EvalJs(compiled_book_source)
    searchObj = parseSearchUrl(compiled_book_source, key, page, evalJS)
    if searchObj['webView']:
        return None, "webView"

    content, skip = await get_content(searchObj)
    if skip is not False:
        return None, skip
    return getSearchResult(compiled_book_source, searchObj, content, evalJS), False


async def get_content(url_obj):
    method = url_obj['method']
    charset = url_obj['charset']
    bodyType = url_obj['bodytype']
    body = url_obj['body']
    url = urlparse(url_obj['url'])
    url = url._replace(query=urlencode(
        parse_qs(url.query, keep_blank_values=True), doseq=True, encoding=charset, errors='ignore'))
    url = urlunparse(url)

    if body and bodyType == Body.FORM:
        body = urlencode(parse_qs(body, keep_blank_values=True), doseq=True, encoding=charset)
    elif body:
        body = body.encode(charset)

    async with fetch.request(method, url, headers=url_obj['headers'],
                             data=body) as r:
        response = r
        if url_obj['type']:
            # zip数据转换为hex
            content = (await r.content.read()).decode().hex()
        else:
            content = await r.text()

    if response:
        url_obj['finalurl'] = str(response.url)

    if url_obj['allFontFaceUrl']:
        for fontFaceUrl in url_obj['allFontFaceUrl']:
            if 'srcList' in fontFaceUrl:
                for urlDict in fontFaceUrl['srcList']:
                    urlDict['url'] = urljoin(url_obj['finalurl'], urlDict['url'])

    if response and response.history:
        url_obj['redirected'] = True
    else:
        url_obj['redirected'] = False

    # 重定向到了详情页
    if response and response.history:
        return content, "重定向到了详情页"
    else:
        return content, False
