import re
from typing import TypedDict, Any
from dataclasses import dataclass, asdict, field
from pathlib import Path
import json

from shared.json_dumps import json_dumps
from shared.log import Log
from shared.exception import *


AUTO_ISSUE_TYPE = "自动判断"
ISSUE_NOTE_REGEX = r"[\[（]注释[\]）][\:：].*"  # 匹配 issue 描述里的注释


class LinksJson(TypedDict):
    issue_url: str
    issue_web_url: str
    comment_url: str


class CommentJson(TypedDict):
    author: str
    body: str


class IssueInfoJson(TypedDict):
    issue_id: int
    issue_type: str
    issue_title: str
    issue_state: str
    """值只可能为 open 或 closed"""
    issue_body: str
    issue_labels: list[str]
    issue_comments: list[CommentJson]
    introduced_version: str
    archive_version: str
    ci_event_type: str
    platform_type: str
    http_header: dict[str, str]
    reopen_http_method: str
    reopen_body: dict[str, str]
    archived_success: bool
    links: LinksJson


@dataclass()
class IssueInfo:
    @dataclass()
    class Links:
        issue_url: str = str()
        issue_web_url: str = str()
        comment_url: str = str()

    @dataclass()
    class Comment:
        author: str = str()
        body: str = str()

    issue_id: int = -1
    issue_type: str = AUTO_ISSUE_TYPE
    issue_title: str = str()
    issue_state: str = str()
    """值只可能为 open 或 closed"""
    issue_body: str = str()
    issue_labels: list[str] = field(default_factory=list)
    issue_comments: list[Comment] = field(default_factory=list)
    introduced_version: str = str()
    archive_version: str = str()
    ci_event_type: str = str()
    platform_type: str = str()
    issue_repository: str = str()
    http_header: dict[str, str] = field(default_factory=dict)
    reopen_http_method: str = str()
    reopen_body: dict[str, str] = field(default_factory=dict)
    archived_success: bool = False
    links: Links = field(default_factory=Links)

    @staticmethod
    def remove_sensitive_info(issue_info: dict[str, Any]) -> dict[str, Any]:
        """移除issue_info的敏感信息，函数不会修改传入的字典"""
        result = issue_info.copy()
        result.pop("http_header")
        return result

    def to_print_string(self) -> str:
        result = IssueInfo.remove_sensitive_info(asdict(self))
        result.pop("issue_comments")
        return json_dumps(result)

    def to_dict(self) -> IssueInfoJson:
        return IssueInfoJson(**asdict(self))

    def json_dump(self, json_path: str) -> None:
        json.dump(
            self.to_dict(),
            Path(json_path).open("w", encoding="utf-8"),
            indent=4,
            ensure_ascii=False,
        )

    def json_load(self, json_path: str) -> None:
        json_data: IssueInfoJson = json.loads(
            Path(json_path).read_text(encoding="utf-8")
        )
        self.from_dict(json_data)

    def from_dict(self, issue_info: IssueInfoJson) -> None:
        links = issue_info.get("links")
        self.__dict__.update(issue_info)
        self.links = self.Links(**links)

    def update(self, **kwargs) -> None:
        self.__dict__.update(kwargs)

    def should_skip_archived_process(
        self,
        skip_archived_reges_for_comments: list[str],
    ):
        comments = self.issue_comments
        for comment in comments:
            for skip_regex in skip_archived_reges_for_comments:
                if len(re.findall(skip_regex, comment.body)) > 0:
                    return True
        return False

    def get_introduced_version_from_description(
        self,
        introduced_version_reges: list[str],
        need_introduced_version_issue_type: list[str],
    ) -> str:
        print(
            Log.getting_something_from.format(
                another=Log.issue_description, something=Log.introduced_version
            )
        )

        issue_body = self.remove_useless_notes_in_description(self.issue_body)
        issue_type = self.issue_type
        introduced_versions: list[str] = []
        for regex in introduced_version_reges:
            introduced_versions.extend(re.findall(regex, issue_body))
        introduced_versions = [item.strip() for item in introduced_versions]
        if len(introduced_versions) >= 2:
            print(Log.too_many_introduced_version)
            raise IntroducedVersionError(
                ErrorMessage.too_many_introduced_version.format(
                    versions=[i for i in introduced_versions]
                )
            )

        if len(introduced_versions) == 0:
            if any(
                [
                    issue_type == target_issue_type
                    for target_issue_type in need_introduced_version_issue_type
                ]
            ):
                print(Log.introduced_version_not_found)
                raise IntroducedVersionError(ErrorMessage.missing_introduced_version)
            else:
                print(Log.introduced_version_not_found)
                return ""
        print(
            Log.getting_something_from_success.format(
                another=Log.issue_description, something=Log.introduced_version
            )
        )
        return introduced_versions[0]

    def get_archive_version_from_comments(self, comment_reges: list[str]) -> str:
        """匹配不到归档版本号会返回一个空字符串"""
        print(
            Log.getting_something_from.format(
                another=Log.issue_comment, something=Log.archive_version
            )
        )

        issue_comments = self.issue_comments
        archive_versions: set[str] = set()
        for comment in issue_comments:
            for comment_regex in comment_reges:
                if len(match_result := re.findall(comment_regex, comment.body)) > 0:
                    archive_versions.update(match_result)
        if len(archive_versions) >= 2:
            print(Log.too_many_archive_version)
            raise ArchiveVersionError(
                ErrorMessage.too_many_archive_version.format(
                    versions=[i for i in archive_versions]
                )
            )
        elif len(archive_versions) == 0:
            return ""
        elif len(archive_versions) == 1:
            print(
                Log.getting_something_from_success.format(
                    another=Log.issue_comment, something=Log.archive_version
                )
            )
        return archive_versions.pop()

    def get_issue_type_from_labels(self, label_map: dict[str, str]) -> str:
        print(
            Log.getting_something_from.format(
                another=Log.issue_label, something=Log.issue_type
            )
        )

        issue_labels = self.issue_labels
        result = []
        for label_name, type in label_map.items():
            if label_name in issue_labels:
                result.append(type)

        if len(result) == 0:
            print(Log.issue_type_not_found)
            raise IssueTypeError(
                ErrorMessage.missing_issue_type_from_label.format(
                    issue_type=list(label_map.keys())
                )
            )
        if len(result) > 1:
            print(Log.too_many_issue_type)
            raise IssueTypeError(ErrorMessage.too_many_issue_type.format(labels=result))
        if len(result) == 1:
            print(
                Log.getting_something_from_success.format(
                    another=Log.issue_label, something=Log.issue_type
                )
            )
        return result[0]

    def should_archive_issue(
        self,
        archive_version_reges_for_comments: list[str],
        raw_archive_version_reges_for_comments: list[str],
        archive_necessary_labels: list[str],
        check_labels: bool = True,
        check_archive_version: bool = True,
    ) -> bool:
        """should_archive_issue会检查当前issue是否是应该被归档的对象，\n
        以及判断当前issue如果是归档的对象，是否符合归档条件 \n
        函数区分了上述三种情况且会产生不同的行为：\n
        - 若issue不是归档对象，则直接返回False \n
        - 若issue是归档对象，但是不满足归档条件（缺少归档关键信息），则抛出相应错误 \n
        - 若issue是归档对象，并且满足归档条件，则返回True \n
        """
        issue_labels = self.issue_labels
        archive_version = self.get_archive_version_from_comments(
            archive_version_reges_for_comments
        )
        if (
            should_not_match_archive_version := (archive_version == "")
            and check_archive_version
        ):
            print(Log.archive_version_not_found)
        else:
            print(Log.archive_version_found)

        # issue必须包含某些归档所需标签，否则不进行归档流程
        if (
            should_label_not_in_target := (
                set(issue_labels) & set(archive_necessary_labels)
                != set(archive_necessary_labels)
            )
            and check_labels
        ):
            print(Log.target_labels_not_found)
        else:
            print(Log.target_labels_found)

        # 未匹配到归档关键字应则不进行归档流程
        # 因为这有可能是用户自行关闭的issue或者无需归档的issue
        if all(
            [
                should_label_not_in_target,
                should_not_match_archive_version,
                check_labels,
                check_archive_version,
            ]
        ):
            return False

        if should_label_not_in_target and check_labels:
            raise ArchiveLabelError(
                ErrorMessage.missing_archive_labels.format(
                    labels=archive_necessary_labels
                )
            )

        if should_not_match_archive_version and check_archive_version:
            raise ArchiveVersionError(
                ErrorMessage.missing_archive_version.format(
                    keywords=raw_archive_version_reges_for_comments
                )
            )

        return True

    def remove_useless_notes_in_description(self, description: str) -> str:
        return re.sub(ISSUE_NOTE_REGEX, "", description)

    def remove_issue_type_in_issue_title(self, type_keyword: dict[str, str]) -> str:
        title = self.issue_title
        # 这里不打算考虑issue标题中
        # 匹配多个issue类型关键字的情况
        # 因为这种情况下脚本完全无法判断
        # issue的真实类型是什么
        for key in type_keyword.keys():
            if key in title:
                title = title.replace(key, "").strip()
                break
        return title

    def set_archived_success(self) -> None:
        self.archived_success = True

    def should_archived_success(self) -> bool:
        return self.archived_success
