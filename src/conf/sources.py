from common.constant import CONF_PATH
from conf import load_yml_config
from conf.models.Souces import (
    BookSource,
    HttpTTSSource,
    ReadConfig,
    ReplaceRule,
    Subscribe,
    Theme,
)

book_sources: list[BookSource] = [
    BookSource(**x) for x in load_yml_config(CONF_PATH / "book_sources.yml")
]

http_ttss: list[HttpTTSSource] = [
    HttpTTSSource(**x) for x in load_yml_config(CONF_PATH / "http_ttss.yml")
]
read_configs: list[ReadConfig] = [
    ReadConfig(**x) for x in load_yml_config(CONF_PATH / "read_configs.yml")
]
replace_rules: list[ReplaceRule] = [
    ReplaceRule(**x) for x in load_yml_config(CONF_PATH / "replace_rules.yml")
]
subscribes: list[Subscribe] = [
    Subscribe(**x) for x in load_yml_config(CONF_PATH / "subscribes.yml")
]
themes: list[Theme] = [Theme(**x) for x in load_yml_config(CONF_PATH / "themes.yml")]
