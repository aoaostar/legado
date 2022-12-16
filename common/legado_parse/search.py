# -*- coding: utf-8 -*-
# +-------------------------------------------------------------------
# | Date: 2022/12/16
# +-------------------------------------------------------------------
# | Author: Pluto <i@aoaostar.com>
# +-------------------------------------------------------------------
from urllib.parse import urlparse, urlencode, parse_qs, urlunparse, urljoin

from LegadoParser2.RuleJs.JS import EvalJs
from LegadoParser2.RuleUrl.BodyType import Body
from LegadoParser2.RuleUrl.Url import getContent as getContent2
from LegadoParser2.Search import parseSearchUrl, getSearchResult

from common import fetch


async def search(compiledBookSource, key, page=1):
    evalJS = EvalJs(compiledBookSource)
    searchObj = parseSearchUrl(compiledBookSource, key, page, evalJS)
    content, redirected = await getContent(searchObj)
    # content, redirected =  getContent2(searchObj)
    return getSearchResult(compiledBookSource, searchObj, content, evalJS)


async def getContent(urlObj):
    method = urlObj['method']
    # if urlObj['method'] == 'GET':
    #     method = 0
    # elif urlObj['method'] == 'POST':
    #     method = 1
    redirected = False
    charset = urlObj['charset']
    bodyType = urlObj['bodytype']
    body = urlObj['body']
    url = urlparse(urlObj['url'])
    url = url._replace(query=urlencode(
        parse_qs(url.query, keep_blank_values=True), doseq=True, encoding=charset, errors='ignore'))
    url = urlunparse(url)
    response = None

    if body and bodyType == Body.FORM:
        body = urlencode(parse_qs(body, keep_blank_values=True), doseq=True, encoding=charset)
    elif body:
        body = body.encode(charset)

    async with fetch.request(method, url, headers=urlObj['headers'],
                             data=body) as r:
        response = r
        if urlObj['type']:
            # zip数据转换为hex
            content = (await r.content.read()).decode().hex()
        else:
            content = await r.text()

        if response:
            urlObj['finalurl'] = str(response.url)

        if urlObj['allFontFaceUrl']:
            for fontFaceUrl in urlObj['allFontFaceUrl']:
                if 'srcList' in fontFaceUrl:
                    for urlDict in fontFaceUrl['srcList']:
                        urlDict['url'] = urljoin(urlObj['finalurl'], urlDict['url'])

        if response and response.history:
            urlObj['redirected'] = True
        else:
            urlObj['redirected'] = False

        # 重定向到了详情页
        if response and response.history:
            redirected = True
            return content, redirected
        else:
            return content, redirected
