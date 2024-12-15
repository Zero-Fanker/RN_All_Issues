import os
import json
from dataclasses import asdict, replace
from pathlib import Path

from shared.log import Log
from shared.data_source import DataSource
from shared.env import Env
from shared.json_config import Config

FORMAT_MAP_BLACK_LIST = [
    "version_regex",
    "introduced_version_reges",
    "archive_template"
]


def apply_place_holder(obj: dict,
                       place_holder: dict
                       ):
    '''为了能让某些value中能使用前面已经定义的value，
    用来将替换{}语法字符串替换成真正的value \n
    example:  \n
    "{version_regex}测试通过" 中花括号的内容，会被替换成 "version_regex" 的value
    '''
    for key, value in obj.items():
        # version_regex 为了判断版本号，用了正则的花括号语法
        # 这会导致format_map报错
        if key in FORMAT_MAP_BLACK_LIST:
            continue
        if isinstance(value, dict):
            apply_place_holder(value, place_holder)
        elif isinstance(value, str):
            obj[key] = value.format_map(place_holder)
        elif isinstance(value, list):
            obj[key] = [item.format_map(place_holder)
                        for item in value
                        if isinstance(item, str)
                        ]


class EnvConfigDataSource(DataSource):
    def load(self, config: Config) -> None:
        config.token = os.environ[Env.TOKEN]
        config.issue_output_path = os.environ[Env.ISSUE_OUTPUT_PATH]
        config.ci_event_type = os.environ[Env.CI_EVENT_TYPE]
        config.archived_document_path = os.environ[Env.ARCHIVED_DOCUMENT_PATH]


class JsonConfigDataSource(DataSource):
    def __init__(self, json_path: str):
        super().__init__()
        self.json_path = json_path

    def load(
            self,
            config: Config
    ) -> None:
        config_path = self.json_path

        print(Log.loading_something
              .format(something=config_path))

        raw_json: dict = dict(
            json.loads(
                Path(config_path
                     ).read_text(encoding="utf-8")
            )
        )
        print(Log.loading_something_success
              .format(something=config_path))

        apply_place_holder(
            obj=raw_json,
            place_holder=raw_json
        )

        issue_type = Config.IssueType(
            **raw_json.pop("issue_type"))
        archived_document = Config.ArchivedDocument(
            **raw_json.pop("archived_document"))
        config.__dict__.update(**raw_json)
        config.issue_type = issue_type
        config.archived_document = archived_document
