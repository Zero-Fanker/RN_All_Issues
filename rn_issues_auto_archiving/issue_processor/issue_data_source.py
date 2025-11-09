import os
from abc import ABC, abstractmethod
import json

from shared.issue_info import IssueInfo, AUTO_ISSUE_TYPE
from shared.ci_event_type import CiEventType
from shared.env import Env
from shared.log import Log
from shared.issue_state import parse_issue_state
from shared.json_dumps import json_dumps
from shared.exception import MissingIssueNumber, WebhookPayloadError
from shared.api_path import ApiPath


def issue_number_to_int(issue_number: str):
    if not issue_number.isdigit():
        raise ValueError(
            Log.invalid_issue_number.format(issues_number_var=issue_number)
        )
    return int(issue_number.strip())


class IssusDataSource(ABC):
    @abstractmethod
    def load(self, issue_info: IssueInfo) -> None:
        pass


class GithubIssueDataSource(IssusDataSource):
    def load(self, issue_info: IssueInfo) -> None:
        print(Log.loading_something.format(something=Log.env))

        issue_info.ci_event_type = ci_event_type = os.environ[Env.CI_EVENT_TYPE]
        issue_info.issue_repository = os.environ[Env.ISSUE_REPOSITORY]

        # 手动触发流水线时应该读取的环境变量
        if ci_event_type in CiEventType.manual:
            issue_info.issue_id = issue_number_to_int(
                os.environ[Env.MANUAL_ISSUE_NUMBER]
            )
            issue_info.issue_title = os.environ[Env.MANUAL_ISSUE_TITLE].strip()
            issue_info.issue_state = parse_issue_state(
                os.environ[Env.MANUAL_ISSUE_STATE]
            )
            issue_info.issue_body = ""
            issue_info.issue_labels = []
            issue_info.introduced_version = os.environ[Env.INTRODUCED_VERSION].strip()
            issue_info.archive_version = os.environ[Env.ARCHIVE_VERSION].strip()
            issue_info.issue_type = os.environ[Env.ISSUE_TYPE]
            issue_info.links.issue_url = os.environ[Env.MANUAL_ISSUE_URL]
            issue_info.links.comment_url = os.environ[Env.MANUAL_COMMENTS_URL]

            print(
                Log.print_input_variables.format(
                    input_variables=json_dumps(
                        {
                            "issue_number": issue_info.issue_id,
                            "issue_title": issue_info.issue_title,
                            "issue_type": issue_info.issue_type,
                            "introduced_version": issue_info.introduced_version,
                            "archive_version": issue_info.archive_version,
                        }
                    )
                )
            )

        # 自动触发流水线时应该读取的环境变量
        else:
            issue_info.issue_id = int(os.environ[Env.ISSUE_NUMBER])
            issue_info.issue_title = os.environ[Env.ISSUE_TITLE]
            issue_info.issue_state = parse_issue_state(os.environ[Env.ISSUE_STATE])
            issue_info.issue_body = os.environ[Env.ISSUE_BODY]
            issue_info.issue_labels = []
            issue_info.introduced_version = ""
            issue_info.archive_version = ""
            issue_info.issue_type = AUTO_ISSUE_TYPE
            issue_info.links.issue_url = os.environ[Env.ISSUE_URL]
            issue_info.links.comment_url = os.environ[Env.COMMENTS_URL]

        print(Log.loading_something_success.format(something=Log.env))


class GitlabIssueDataSource(IssusDataSource):
    @staticmethod
    def build_issue_url(issue_id: int, api_base_url: str) -> str:
        return f"{api_base_url}{ApiPath.issues}/{issue_id}"

    def load(self, issue_info: IssueInfo) -> None:
        print(Log.loading_something.format(something=Log.env))

        issue_info.ci_event_type = ci_event_type = os.environ[Env.CI_EVENT_TYPE]
        issue_info.issue_repository = os.environ[Env.ISSUE_REPOSITORY]

        # 手动触发流水线时应该读取的环境变量
        issue_id: int
        if ci_event_type in CiEventType.manual:
            issue_id_str = os.environ.get(Env.ISSUE_NUMBER, None)
            if issue_id_str is None or issue_id_str == "":
                raise MissingIssueNumber(
                    Log.missing_issue_number.format(issues_number_var=Env.ISSUE_NUMBER)
                )
            issue_info.issue_id = issue_id = issue_number_to_int(issue_id_str)
            issue_info.issue_title = os.environ.get(Env.ISSUE_TITLE, "").strip()
            issue_info.issue_state = parse_issue_state(os.environ[Env.ISSUE_STATE])
            issue_info.issue_body = ""
            issue_info.issue_labels = []
            issue_info.introduced_version = os.environ.get(
                Env.INTRODUCED_VERSION, ""
            ).strip()
            issue_info.archive_version = os.environ.get(Env.ARCHIVE_VERSION, "").strip()
            issue_info.issue_type = os.environ.get(
                Env.ISSUE_TYPE, AUTO_ISSUE_TYPE
            ).strip()

            print(
                Log.print_input_variables.format(
                    input_variables=json_dumps(
                        {
                            "issue_id": issue_info.issue_id,
                            "issue_title": issue_info.issue_title,
                            "introduced_version": issue_info.introduced_version,
                            "archive_version": issue_info.archive_version,
                            "issue_type": issue_info.issue_type,
                        }
                    )
                )
            )

        # 自动触发流水线时应该读取的环境变量
        else:
            try:
                webhook_payload = json.loads(os.environ[Env.WEBHOOK_PAYLOAD])
            except Exception:
                print(Log.webhook_payload_not_found)
                raise WebhookPayloadError(Log.webhook_payload_not_found)

            # webhook里是json，iid一定是int
            issue_info.issue_id = issue_id = webhook_payload["object_attributes"]["iid"]
            issue_info.issue_title = webhook_payload["object_attributes"]["title"]
            issue_info.issue_state = parse_issue_state(
                webhook_payload["object_attributes"]["action"]
            )
            issue_info.issue_body = webhook_payload["object_attributes"]["description"]
            issue_info.issue_labels = [
                label_json["title"]
                for label_json in webhook_payload["object_attributes"]["labels"]
            ]
            issue_info.introduced_version = ""
            issue_info.archive_version = ""
            issue_info.issue_type = AUTO_ISSUE_TYPE

        issue_url = self.build_issue_url(issue_id, os.environ[Env.API_BASE_URL])
        issue_info.links.issue_url = issue_url
        issue_info.links.comment_url = issue_url + "/" + ApiPath.notes

        print(Log.loading_something_success.format(something=Log.env))
