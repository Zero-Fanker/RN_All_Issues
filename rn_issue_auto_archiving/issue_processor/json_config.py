import json
from dataclasses import dataclass
from typing import TypedDict, Callable

from shared.log import Log

FORMAT_MAP_BLACK_LIST = [
    "version_regex",
    "introduced_version_reges"
]


class PlaceHolderDict(TypedDict):
    version_regex: str


class ConfigJson(TypedDict):
    class Shared(TypedDict):
        labels: list[str]
        comments: list[str]

    class IssueType(TypedDict):
        type_keyword: dict[str, str]
        need_introduced_version_issue_type: list[str]
        label_map : dict[str,str]

    version_regex: str
    introduced_version_reges: list[str]
    issue_type: IssueType
    white_list: Shared
    black_list: Shared


def apply_place_holder(obj: dict,
                       place_holder: PlaceHolderDict
                       ):
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


class Config():

    class Shared():
        def __init__(self):
            self.labels: list[str] = []
            self.comments: list[str] = []

    class LabelConditions():
        handlers: list[Callable[[list[str]], bool]] = []

    class BlackList(Shared):
        pass

    class WhiteList(Shared):
        pass

    class IssueType():
        def __init__(self):
            self.type_keyword: dict[str, str] = {}
            self.need_introduced_version_issue_type: list[str] = []
            self.label_map : dict[str,str] = {}

    @staticmethod
    def register_condition_handler(func: Callable[[list[str]], bool]) -> None:
            Config.LabelConditions.handlers.append(func)
    @staticmethod
    def get_condition_handlers():
        return Config.LabelConditions.handlers

    def __init__(self, config_path: str):
        self.raw_json: ConfigJson
        self.labels: list[str]
        self.comments: list[str]
        self.version_regex: str
        self.white_list: Config.WhiteList
        self.black_list: Config.BlackList
        self.issue_type: Config.IssueType
        self.introduced_version_reges: list[str]

        print(Log.loading_something
              .format(something=config_path))

        file = open(config_path, 'r', encoding='utf-8')
        raw_json: ConfigJson = json.load(file)
        file.close()
        apply_place_holder(
            obj=raw_json,
            place_holder=raw_json
        )
        self.raw_json = raw_json
        self.__dict__.update(self.raw_json)
        self.white_list: Config.WhiteList = Config.WhiteList()
        self.black_list: Config.BlackList = Config.BlackList()
        self.issue_type: Config.IssueType = Config.IssueType()
        self.white_list.comments = self.raw_json['white_list']['comments']
        self.white_list.labels = self.raw_json['white_list']['labels']
        self.black_list.comments = self.raw_json['black_list']['comments']
        self.black_list.labels = self.raw_json['black_list']['labels']
        self.issue_type.type_keyword = self.raw_json['issue_type']['type_keyword']
        self.issue_type.label_map = self.raw_json['issue_type']['label_map']
        self.issue_type.need_introduced_version_issue_type = self.raw_json[
            'issue_type']['need_introduced_version_issue_type']
        print(Log.loading_something_success
              .format(something=config_path))
