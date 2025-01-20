from collections import OrderedDict
from typing import ClassVar

import markdown2

import settings
from common.constant import ROOT_PATH, TEMP_SOURCES_PATH
from conf.models.BaseSouce import BaseSource
from conf.models.Souces import (
    BookSource,
    HttpTTSSource,
    ReadConfig,
    ReplaceRule,
    Subscribe,
    Theme,
)
from models.sync import SyncResult, SyncStatus

header = """
# [「阅读」APP 源](https://legado.aoaostar.com)

[![GitHub license](https://img.shields.io/badge/license-AGPL--3.0-orange?style=flat-square&color=0f6adb&logo=github)](https://github.com/aoaostar/legado/)
[![GitHub Star](https://img.shields.io/github/stars/aoaostar/legado.svg?style=flat-square&label=Star&color=0f6adb&logo=github)](https://github.com/aoaostar/legado/)
[![GitHub Fork](https://img.shields.io/github/forks/aoaostar/legado.svg?style=flat-square&label=Fork&color=0f6adb&logo=github)](https://github.com/aoaostar/legado/)
[![Pluto's Blog](https://img.shields.io/badge/%E5%8D%9A%E5%AE%A2-Pluto's%20Blog-d7b1bf?logo=Blogger&color=0f6adb)](https://blog.aoaostar.com)

📚 一些「阅读」小说书源、订阅源、主题、排版配置  
Git仓库不支持一键导入, 请前往 [legado.aoaostar.com](https://legado.aoaostar.com)  

> 阅读 APP [官方下载地址](https://github.com/gedoor/legado/releases)、[酷安下载地址[推荐]](https://www.coolapk.com/apk/256030)

****
""".strip()

footer = """
****

Thanks for stopping by! 😁
""".strip()

html_content_template = f"""
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
     #main_content#
    </div>
  </body>
</html>
"""


class RenderService:
    render_sources_map: ClassVar[dict[type[BaseSource], str]] = OrderedDict(
        {
            BookSource: "书源",
            Subscribe: "订阅源",
            ReplaceRule: "净化规则",
            ReadConfig: "阅读排版",
            Theme: "主题",
            HttpTTSSource: "在线朗读引擎",
        }
    )
    markdown_output_path = ROOT_PATH / "README.md"
    html_output_path = ROOT_PATH / "index.html"

    def __init__(self):
        self.render_sources_data: dict[type[BaseSource], list[SyncResult]] = (
            OrderedDict()
        )
        for k in self.render_sources_map:
            self.render_sources_data[k] = []

    @staticmethod
    def __translate_legado_url(source_result: SyncResult) -> tuple[str, str]:
        src_url = f"{settings.repo_url}/sources/{source_result.output_path.relative_to(TEMP_SOURCES_PATH)}"

        match source_result.source:
            case HttpTTSSource():
                legado_url = f"legado://import/httpTTS?src={src_url}"
            case ReadConfig():
                legado_url = f"legado://import/readConfig?src={src_url}"
            case ReplaceRule():
                legado_url = f"legado://import/replaceRule?src={src_url}"
            case Subscribe():
                legado_url = f"legado://import/rssSource?src={src_url}"
            case Theme():
                legado_url = f"legado://import/theme?src={src_url}"
            case _:
                legado_url = f"legado://import/bookSource?src={src_url}"

        return src_url, legado_url

    async def execute(self, sources: list[SyncResult]):
        for s in sources:
            self.render_sources_data[s.source.__class__].append(s)

        navs = []
        contents = []
        for index, (clazz, ss) in zip(
            range(len(self.render_sources_data)),
            self.render_sources_data.items(),
            strict=False,
        ):
            title = self.render_sources_map.get(clazz)
            navs.append(
                f"""
                *   [{title}](#id_{index})
                 """.strip()
            )
            sub_contents = []

            for i, s in enumerate(ss):
                src_url, legado_url = self.__translate_legado_url(s)
                sync_status = (
                    "同步成功"
                    if s.status == SyncStatus.Success
                    else f"同步失败, {s.message}"
                )
                sub_contents.append(
                    f"""
* {s.source.title} {"、".join(s.source.tags)}

    + [访问直链]({src_url})
    + [一键导入]({legado_url})
    + 上一次同步状态: {sync_status}, 共 {s.count} 条
    + 更新时间: {s.update_time}
    + 同步时间: {s.sync_time}
""".strip(),
                )
                if i < len(ss) - 1:
                    sub_contents.append("****")

            contents.extend(
                [
                    f"""
<h2 id="id_{index}">{title}</h2>
<details>
<summary style="cursor: pointer">点击展开</summary>
""".strip(),
                    *sub_contents,
                    "</details>",
                ]
            )

        final_contents = [header, *navs, *contents, footer]

        markdown_content = "\n\n".join(final_contents)

        html_content = html_content_template.replace(
            "#main_content#", markdown2.markdown(markdown_content)
        )

        self.markdown_output_path.write_text(
            markdown_content,
            encoding="utf-8",
        )
        self.html_output_path.write_text(html_content, encoding="utf-8")
