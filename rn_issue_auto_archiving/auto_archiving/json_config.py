import json
import os
from dataclasses import dataclass
from typing import TypedDict, TypeAlias
from pathlib import Path

from shared.log import Log

IssueType: TypeAlias = str


class ConfigJson(TypedDict):
    class ProcessingAction(TypedDict):
        add_prefix: str
        add_suffix: str
        remove_keyword: list[str]

    rjust_space_width: int
    rjust_character: str
    table_separator: str
    archive_template: str
    action_name_map: dict[str, str]
    issue_title_processing_rules: dict[IssueType,
                                       ProcessingAction]
    reopen_workflow_prefix_map : dict[str,str]


class Config():

    def __init__(self, config_path: str):
        print(Log.loading_something.format(something=config_path))
        self.rjust_space_width: int
        self.rjust_character: str
        self.archive_template: str
        self.archive_template: str
        self.table_separator: str
        self.action_name_map: dict[str, str]
        self.reopen_workflow_prefix_map: dict[str, str]
        self.issue_title_processing_rules: dict[IssueType,
                                                ConfigJson.ProcessingAction]
        self.raw_json: ConfigJson = json.loads(
            Path(config_path).read_text(encoding="utf-8")
        )
        self.__dict__.update(self.raw_json)
        print(Log.loading_something_success.format(something=config_path))

