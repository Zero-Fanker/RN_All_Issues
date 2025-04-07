from dataclasses import dataclass

from issue_processor.git_service_client import GitServiceClient
from issue_processor.issue_data_source import GithubIssueDataSource, GitlabIssueDataSource
from issue_processor.git_service_client import GithubClient, GitlabClient
from shared.ci_event_type import CiEventType
from shared.config_manager import ConfigManager
from shared.env import should_run_in_github_action, should_run_in_gitlab_ci
from shared.issue_state import IssueState
from shared.exception import ErrorMessage, MissingArchiveVersionAndArchiveLabel
from shared.issue_info import AUTO_ISSUE_TYPE, IssueInfo
from shared.json_config import Config
from shared.log import Log
from shared.exception import UnexpectedPlatform


class IssueProcessor():

    @dataclass
    class GatherInfo():
        introduced_version: str = str()
        archive_version: str = str()
        issue_type: str = str()

    @staticmethod
    def init_config(config_manager: ConfigManager) -> Config:
        config = Config()
        try:
            config_manager.load_all(config)
        except Exception as exc:
            print(Log.parse_config_failed
                  .format(exc=exc))
            raise
        return config

    @staticmethod
    def init_git_service_client(
        test_platform_type: str | None,
        config: Config
    ) -> GithubClient | GitlabClient:
        service_client: GithubClient | GitlabClient
        if test_platform_type is not None:
            print(Log.get_test_platform_type
                  .format(test_platform_type=test_platform_type))
        if (test_platform_type == GithubClient.name
                or should_run_in_github_action()):
            service_client = GithubClient(
                token=config.token
            )
        elif (test_platform_type == GitlabClient.name
              or should_run_in_gitlab_ci()):
            service_client = GitlabClient(
                token=config.token
            )
        else:
            raise UnexpectedPlatform(
                Log.unexpected_platform_type
                .format(
                    platform_type=test_platform_type
                ))
        return service_client

    @staticmethod
    def init_issue_info(
        platform: GitServiceClient,
    ) -> IssueInfo:
        issue_info = IssueInfo()

        if isinstance(platform, GithubClient):
            GithubIssueDataSource().load(issue_info)
            issue_info.update(
                platform_type=platform.name
            )
        elif isinstance(platform, GitlabClient):
            GitlabIssueDataSource().load(issue_info)
            issue_info.update(
                platform_type=platform.name
            )
        else:
            raise UnexpectedPlatform(
                Log.unexpected_platform_type
                .format(
                    platform_type=type(platform)
                ))
        return issue_info

    @staticmethod
    def should_skip_archived_process(
        issue_info: IssueInfo,
        skip_archived_reges_for_comments: list[str],
    ) -> bool:
        return issue_info.should_skip_archived_process(
            skip_archived_reges_for_comments
        )

    @staticmethod
    def verify_not_archived_object(
        issue_info: IssueInfo,
        config: Config
    ) -> bool:
        # gitlab的issue webhook是会响应issue reopen事件的
        # gitlab的reopen issue事件应该被跳过
        # 而手动触发的流水线有可能目标Issue是还没被closed的
        if (CiEventType.should_ci_running_in_issue_event()
                and (issue_info.issue_state
                     == IssueState.open)
            ):
            print(Log.issue_state_is_open)
            return True

        # gitlab的issue webhook还会响应issue update事件
        if (issue_info.issue_state
                == IssueState.update):
            print(Log.issue_state_is_update)
            return True

        running_in_manual = CiEventType.should_ci_running_in_manual()
        not_input_archive_version = (
            issue_info.archive_version == "")
        if ((running_in_manual and not_input_archive_version)
                or not running_in_manual):
            not_archived_issue = not issue_info.should_archive_issue(
                config.archive_version_reges_for_comments,
                config.raw_archive_version_reges_for_comments,
                config.archive_necessary_labels,
            )
            if not running_in_manual and not_archived_issue:
                print(Log.not_archive_issue)
                return True
            elif ((running_in_manual and not_input_archive_version)
                  and not_archived_issue):
                raise MissingArchiveVersionAndArchiveLabel(
                    ErrorMessage.missing_labels_and_archive_version
                )

        return False

    @staticmethod
    def gather_info_from_issue(
        issue_info: IssueInfo,
        config: Config
    ) -> GatherInfo:
        gather_info = IssueProcessor.GatherInfo(
            issue_type=issue_info.issue_type,
            introduced_version=issue_info.introduced_version
        )
        if issue_info.issue_type == AUTO_ISSUE_TYPE:
            gather_info.issue_type = issue_info.get_issue_type_from_labels(
                config.issue_type.label_map
            )

        # 自动触发流水线必须从描述中获取引入版本号
        # 手动触发流水线如果没有填引入版本号，
        # 那么还得从描述里获取引入版本号
        if issue_info.introduced_version == "":
            gather_info.introduced_version = issue_info.get_introduced_version_from_description(
                config.introduced_version_reges,
                config.issue_type.need_introduced_version_issue_type

            )

        gather_info.archive_version = issue_info.get_archive_version_from_comments(
            config.archive_version_reges_for_comments
        )

        return gather_info

    @staticmethod
    def update_issue_info_with_gather_info(
        issue_info: IssueInfo,
        gather_info: GatherInfo
    ) -> None:
        issue_info.update(
            issue_type=gather_info.issue_type,
            introduced_version=gather_info.introduced_version,
            archive_version=gather_info.archive_version
        )

    @staticmethod
    def parse_issue_info_for_archived(
        issue_info: IssueInfo,
        config: Config
    ) -> None:
        issue_info.update(
            issue_title=issue_info.remove_issue_type_in_issue_title(
                config.issue_type.type_keyword
            )
        )

    @staticmethod
    def close_issue_if_not_closed(
        issue_info: IssueInfo,
        platform: GitServiceClient,
    ) -> None:
        if (CiEventType.should_ci_running_in_manual()
                and (issue_info.issue_state
                     == IssueState.open)
            ):
            platform.close_issue(
                issue_info.links.issue_url
            )
