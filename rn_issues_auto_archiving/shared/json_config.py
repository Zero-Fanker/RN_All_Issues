import os
from dataclasses import dataclass, field
from typing import TypedDict, TypeAlias

IssueType: TypeAlias = str


class ProcessingActionJson(TypedDict):
    add_prefix: str
    add_suffix: str
    remove_keyword: list[str]


class ArchivedDocumentJson(TypedDict):

    rjust_space_width: int
    rjust_character: str
    table_separator: str
    archive_template: str
    fill_issue_url_by_repository_type: list[str]
    action_name_to_repository_type_map: dict[str, str]
    issue_title_processing_rules: dict[IssueType,
                                       ProcessingActionJson]
    reopen_workflow_prefix_map: dict[str, str]


class IssueTypeJson(TypedDict):
    type_keyword: dict[str, str]
    need_introduced_version_issue_type: list[str]
    label_map: dict[str, str]


class ConfigJson(TypedDict):
    version_regex: str
    introduced_version_reges: list[str]
    issue_type: IssueType
    archive_version_reges_for_comments: list[str]
    archive_necessary_labels: list[str]
    archived_document: ArchivedDocumentJson


@dataclass
class Config():
    @dataclass
    class IssueType():
        type_keyword: dict[str, str] = field(
            default_factory=dict)
        need_introduced_version_issue_type: list[str] = field(
            default_factory=list)
        label_map: dict[str, str] = field(
            default_factory=dict)

    @dataclass
    class ArchivedDocument():

        rjust_space_width: int = 0
        rjust_character: str = str()
        table_separator: str = str()
        archive_template: str = str()
        fill_issue_url_by_repository_type: list[str] = field(
            default_factory=list)
        action_name_to_repository_type_map: dict[str, str] = field(
            default_factory=dict)
        issue_title_processing_rules: dict[IssueType,
                                           ProcessingActionJson] = field(
            default_factory=dict)
        reopen_workflow_prefix_map: dict[str, str] = field(
            default_factory=dict)

    # 从env读取
    token: str = str()
    issue_output_path: str = str()
    ci_event_type: str = str()
    archived_document_path: str = str()

    # 从命令行参数读取
    config_path: str = str()
    test_platform_type: str | None = None

    # 从配置文件json读取
    archive_necessary_labels: list[str] = field(
        default_factory=list)
    archive_version_reges_for_comments: list[str] = field(
        default_factory=list)
    skip_archived_reges_for_comments: list[str] = field(
        default_factory=list)
    version_regex: str = str()
    issue_type: IssueType = IssueType()
    introduced_version_reges: list[str] = field(
        default_factory=list)
    archived_document: ArchivedDocument = ArchivedDocument()

    @property
    def raw_archive_version_reges_for_comments(self) -> list[str]:
        return [regex.replace(self.version_regex, '{version_regex}')
                for regex in
                self.archive_version_reges_for_comments]
