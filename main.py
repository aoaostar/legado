# -*- coding: utf-8 -*-
# +-------------------------------------------------------------------
# | Date: 2022/11/28
# +-------------------------------------------------------------------
# | Author: Pluto <i@aoaostar.com>
# +-------------------------------------------------------------------
import asyncio
import json
import os.path
import sys
import urllib.parse

from common import fetch, hash_util, async_util
from common.date_format import date_format
from common.file import save_str, read_str
from common.json_util import load_json

SOURCE_PATH = './source'
DATA_PATH = './data.json'
CONFIG_PATH = './config.json'
STORAGE_PATH = './data'
CACHE_PATH = './cache'

config = load_json(CONFIG_PATH)

config['repo_url'] = config['repo_url'].rstrip('/') + '/'

now = date_format()


def log(message, type_='info'):
    print(f"[{type_.upper()}]{message}")


def load_modify_time_dict():
    data = load_json(DATA_PATH)
    result = {}
    for d in data:
        if 'items' in d:
            for v in d['items']:
                result[v['sha1']] = v['modify_time']

    return result


async def process_source(item, key):
    if 'type' in item and item['type'] == 'local':
        url = f"{STORAGE_PATH}/{key}/{item['url']}"
        item['url'] = config['repo_url'] + url
    else:
        url = item['url']

    cache_filename = os.path.normpath(f"{CACHE_PATH}/{hash_util.sha1(url)}.json")

    def log_(message, type_='info'):
        log(f"[{item['title']}] {message} {url}", type_)

    log_('await')
    item['status'] = '同步失败'
    cache_sha1 = ''
    if os.path.exists(cache_filename):
        cache_sha1 = hash_util.sha1(read_str(cache_filename))
        modify_time_dict = load_modify_time_dict()
        if cache_sha1 in modify_time_dict:
            item['modify_time'] = modify_time_dict[cache_sha1]
            modify_time_dict.clear()
    try:
        if 'type' in item and item['type'] == 'local':
            dumps = read_str(f"{url}")
        else:
            async with fetch.get(url) as r:
                r_json_ = json.loads(await r.text())
                dumps = json.dumps(r_json_, ensure_ascii=False)
        hash_sha1 = hash_util.sha1(dumps)
        item['status'] = '同步成功'
        if cache_sha1 == hash_sha1:
            return

        cache_sha1 = hash_sha1
        save_str(filename=cache_filename, data=dumps)
    except Exception as e:
        item['status'] = '同步失败: ' + e.__str__()
        log_(e.__str__(), 'error')
    finally:
        item['filename'] = cache_filename
        item['sha1'] = cache_sha1
        item['update_time'] = now

        if 'modify_time' not in item:
            item['modify_time'] = now

        if '同步失败' in item['status']:
            log_(item['status'], 'error')
        else:
            log_(item['status'])
        return item


async def sync(listdir_source: list[str], update: bool = False):
    data = []
    statuses = []

    for source_filename in listdir_source:
        if source_filename.endswith('.json'):
            source = load_json(SOURCE_PATH + '/' + source_filename)
            source['key'] = os.path.basename(source_filename[:-len('.json')])
            tasks = []
            for item_key in range(len(source["items"])):
                item = source['items'][item_key]
                tasks.append(asyncio.create_task(process_source(item, source['key'])))

            results = await async_util.gather(tasks)
            source['items'] = []
            for result in results:
                statuses.append(result['status'])
                source['items'].append(result)
            data.append(source)

    if update:
        data.extend(load_json(DATA_PATH))

    save_str(filename="./data.json", data=json.dumps(data, ensure_ascii=False, indent=4))

    error_count = 0
    for status in statuses:
        if '失败' in status:
            error_count += 1

    log(f'同步成功, 共计 {len(statuses)} 条记录, 同步成功: {len(statuses) - error_count} 条, 同步失败: {error_count} 条')


def render_readme(data: dict):
    nav = '''
## 目录
    '''
    content = ''

    for source_name in config['source']:

        for v in data:
            k = v['key']
            if not source_name == k:
                continue
            nav += f'''
*   [{v['title']}[{k}]](#{v['title']}_{k})
            '''
            content += f'''
<h2 id="{v['title']}_{k}">{v['title']}[{k}]</h2>
            '''
            for i in range(len(v['items'])):
                item = v['items'][i]
                title = item['title']
                url = config['repo_url'] + urllib.parse.quote(item['filename'])
                if 'tag' in item:
                    for tag in item['tag']:
                        title += f" {tag}"
                one_click = ''
                if 'type' in v:
                    one_click = f'''
    + [一键导入](legado://import/{v['type']}?src={url})'''
                content += f'''
* {title}
    + [访问直链]({url}){one_click}
    + 上一次同步状态: {item['status']}
    + 更新时间: {item['modify_time']}
    + 同步时间: {item['update_time']}
'''
                if i + 1 < len(v['items']):
                    content += '\n****\n'

    header = read_str('header.md')
    footer = read_str('footer.md')

    markdown_content = header.strip() + "\n\n" + nav.strip() + "\n\n" + content.strip() + "\n\n" + footer.strip()
    import markdown2
    html_content = f'''
<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1">
<title>阅读APP源 - AOAOSTAR</title>
<meta name="keywords" content="阅读APP源,aoaostar" />
<meta name="description" content="阅读APP源" />
<link rel="shortcut icon" type="image/x-icon" href="//www.aoaostar.com/favicon.ico">
<link rel="stylesheet" href="/assets/css/style.css">
</head>
<body>
    <div class="container-lg px-3 my-5 markdown-body">
    {markdown2.markdown(markdown_content)}
    </div>
  </body>
</html>
'''
    save_str('./README.md', markdown_content)
    save_str('./index.html', html_content)
    log('输出[README.md、index.html]成功')


def all_in_one(data):
    all_ = {}
    for i in range(len(data)):
        d = data[i]
        if d['type'] == 'bookSource':
            for d_ in d['items']:
                d_json = load_json(d_['filename'])
                for d_item in d_json:
                    all_[hash_util.sha1(str(d_item))] = d_item

    all_ = all_.values()
    save_str(STORAGE_PATH + '/all/all.json', json.dumps(list(all_)))


if __name__ == '__main__':
    listdir = os.listdir(SOURCE_PATH)
    listdir.remove('all.json')

    async_util.run(sync(listdir))

    data = load_json(DATA_PATH)

    all_in_one(data)
    async_util.run(sync(['all.json'], True))

    data = load_json(DATA_PATH)

    render_readme(data)
