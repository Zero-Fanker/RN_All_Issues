import os
import json
from dataclasses import dataclass
from abc import abstractmethod, ABC
from http import HTTPStatus

import httpx

from .github_response_json import GithubCommentJson
from .gitlab_response_json import GitlabCommentJson
from shared.log import Log
from shared.env import Env
from shared.exception import *
from shared.issue_info import AUTO_ISSUE_TYPE, IssueInfo
from shared.issue_state import parse_issue_state
from shared.ci_event_type import CiEventType
from shared.json_dumps import json_dumps
from shared.api_path import ApiPath
from shared.json_config import Config


def get_issue_id_from_url(url: str) -> int:
    return int(url.split("/")[-1])


@dataclass()
class Issue():
    id: int
    title: str
    state: str
    body: str
    labels: list[str]
    issue_web_url: str


@dataclass()
class PlatformEnvironments():
    token: str
    issue_number: int
    issue_title: str
    issue_state: str
    issue_body: str
    issue_url: str
    comments_url: str


class GitServiceClient(ABC):

    @abstractmethod
    def _get_comments_from_platform(
        self,
        url: str,
    ) -> list[IssueInfo.Comment]:
        pass

    @abstractmethod
    def reopen_issue(self, issue_url: str) -> None:
        pass

    @abstractmethod
    def close_issue(self, issue_url: str) -> None:
        pass

    @abstractmethod
    def close(self):
        pass

    @abstractmethod
    def _init_http_client(self) -> None:
        pass

    @abstractmethod
    def _get_issue_info_from_platform(self, issue_url: str) -> Issue:
        pass

    @property
    @abstractmethod
    def reopen_issue_method(self) -> str:
        pass

    @property
    @abstractmethod
    def reopen_issue_body(self) -> dict[str, str]:
        pass

    @property
    @abstractmethod
    def close_issue_method(self) -> str:
        pass

    @property
    @abstractmethod
    def close_issue_body(self) -> dict[str, str]:
        pass

    def __init__(self,
                 token: str,
                 ):
        self._token: str = token
        self._platform_type: str
        self._http_header: dict[str, str]
        self._http_client: httpx.Client

    def http_request(
        self,
        url: str,
        method: str = "GET",
        params: dict[str, str] | None = None,
        json_content: dict[str, str] | None = None,
        retry_times: int = 3,
    ) -> httpx.Response:
        error: Exception = Exception()
        for _ in range(retry_times):
            try:
                response = self._http_client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_content,
                    follow_redirects=True,
                )
                if response.status_code == HTTPStatus.NOT_FOUND:
                    print(Log.http_404_not_found)
                response.raise_for_status()
                return response
            except httpx.HTTPStatusError:
                reason = Log.unknown
                try:
                    reason = json_dumps(
                        response.json(),
                    )
                except Exception:
                    pass
                print(Log.http_status_error
                      .format(
                          reason=reason,
                      ))
                raise
            except Exception as e:
                error = e
        raise error

    def enrich_missing_issue_info(
        self,
        issue_info: IssueInfo
    ) -> None:

        issue_info.issue_comments = self._get_comments_from_platform(
            issue_info.links.comment_url
        )
        new_issue_info = self._get_issue_info_from_platform(
            issue_info.links.issue_url
        )
        issue_info.issue_labels = new_issue_info.labels
        issue_info.links.issue_web_url = new_issue_info.issue_web_url
        if CiEventType.should_ci_running_in_manual():
            issue_info.issue_state = new_issue_info.state
            if issue_info.issue_title == "":
                issue_info.issue_title = new_issue_info.title
            if issue_info.issue_body == "":
                issue_info.issue_body = new_issue_info.body

    def send_comment(
            self,
            comment_url: str,
            comment_body: str) -> None:
        ''' api结构详见：\n
        Github ： https://docs.github.com/zh/rest/issues/comments?apiVersion=2022-11-28#create-an-issue-comment \n
        Gitlab ： https://docs.gitlab.com/ee/api/notes.html#create-new-issue-note \n
        两边API创建评论所需的参数都是一致的
        '''
        print(Log.sending_something.format(
            something=Log.announcement_comment))
        self.http_request(
            method="POST",
            url=comment_url,
            json_content={
                "body": comment_body
            }
        )
        print(Log.sending_something_success
              .format(something=Log.announcement_comment))


class GithubClient(GitServiceClient):
    name = "github"

    @staticmethod
    def create_http_header(token: str) -> dict[str, str]:
        ''' 所需http header结构详见：
        https://docs.github.com/zh/rest/using-the-rest-api/getting-started-with-the-rest-api?apiVersion=2022-11-28#example-request-using-query-parameters'''
        return {
            "Authorization": f'Bearer {token}',
            "Accept": "application/vnd.github+json"
        }

    @property
    def reopen_issue_method(self) -> str:
        return "PATCH"

    @property
    def reopen_issue_body(self) -> dict[str, str]:
        return {
            "state": "open"
        }

    @property
    def close_issue_method(self) -> str:
        return self.reopen_issue_method

    @property
    def close_issue_body(self) -> dict[str, str]:
        return {
            "state": "closed"
        }

    def _init_http_client(self) -> None:
        self._http_header = self.create_http_header(self._token)
        self._http_client = httpx.Client(
            headers=self._http_header
        )

    def __init__(self, token: str):
        super().__init__(token)
        self._platform_type = GithubClient.name
        self._init_http_client()

    def _get_comments_from_platform(
        self,
        url: str,
    ) -> list[IssueInfo.Comment]:
        ''' api结构详见：
        https://docs.github.com/en/rest/issues/comments?apiVersion=2022-11-28#list-issue-comments-for-a-repository'''
        print(Log.getting_something.format(something=Log.issue_comment))
        comments: list[IssueInfo.Comment] = []
        page = 1
        while True:
            response: httpx.Response = self.http_request(
                url=url,
                params={"page": str(page)}
            )
            raw_json: list[GithubCommentJson
                           ] = response.json()
            if len(raw_json) == 0:
                break
            comments.extend(
                [IssueInfo.Comment(author=comment["user"]["login"],
                                   body=comment["body"])
                 for comment in raw_json])
            page += 1

        print(Log.getting_something_success.
              format(something=Log.issue_comment))
        return comments

    def _get_issue_info_from_platform(self, issue_url: str) -> Issue:
        ''' 所需http header结构详见：
        https://docs.github.com/zh/rest/issues/issues?apiVersion=2022-11-28#get-an-issue'''
        print(Log.getting_issue_info)
        response = self.http_request(
            url=issue_url,
            method="GET"
        )
        print(Log.getting_issue_info_success)
        raw_json = response.json()
        return Issue(
            id=raw_json["id"],
            title=raw_json["title"],
            state=parse_issue_state(raw_json["state"]),
            body=raw_json["body"],
            labels=[label["name"]
                    for label in raw_json["labels"]],
            issue_web_url=raw_json["html_url"],
        )

    def reopen_issue(self, issue_url: str) -> None:
        ''' api结构详见：
        https://docs.github.com/zh/rest/issues/issues?apiVersion=2022-11-28#update-an-issue'''
        url = issue_url
        print(Log.reopen_issue
              .format(issue_number=get_issue_id_from_url(
                  issue_url)))
        self.http_request(
            method=self.reopen_issue_method,
            url=url,
            json_content=self.reopen_issue_body
        )
        print(Log.reopen_issue_success
              .format(issue_number=get_issue_id_from_url(
                  issue_url))
              )

    def close_issue(self, issue_url: str) -> None:
        ''' api结构详见：
        https://docs.github.com/zh/rest/issues/issues?apiVersion=2022-11-28#update-an-issue'''
        url = issue_url
        print(Log.close_issue
              .format(issue_number=get_issue_id_from_url(
                  issue_url)))
        self.http_request(
            method=self.close_issue_method,
            url=url,
            json_content=self.close_issue_body
        )
        print(Log.close_issue_success
              .format(issue_number=get_issue_id_from_url(
                  issue_url))
              )

    def close(self):
        self._http_client.close()


class GitlabClient(GitServiceClient):
    name = "gitlab"

    @staticmethod
    def should_issue_type_webhook() -> bool:
        '''Gitlab流水线通过webhook触发流水线，
        且无法在流水线测区分webhook事件，
        可能会遇到非Issue事件触发的webhook触发了自动归档流水线
        （例如push事件webhook触发的自动部署流水线）
        gitlab webhook事件类型详见：
        https://docs.gitlab.com/ee/user/project/integrations/webhook_events.html#push-events
        '''
        try:
            webhook_payload = json.loads(
                os.environ[Env.WEBHOOK_PAYLOAD])
            if webhook_payload["event_name"] == "issue":
                print(Log.issue_type_webhook_detected)
                return True
            else:
                print(Log.other_type_webhook_detected)
                return False
        except KeyError:
            # 如果读取不到环境变量，说明是github流水线环境
            return True

    @staticmethod
    def create_http_header(token: str) -> dict[str, str]:
        ''' 所需http header结构详见：
        https://docs.gitlab.com/ee/api/rest/index.html#request-payload'''
        return {
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json"
        }

    @property
    def reopen_issue_method(self) -> str:
        return "PUT"

    @property
    def reopen_issue_body(self) -> dict[str, str]:
        return {
            "state_event": "reopen"
        }

    @property
    def close_issue_method(self) -> str:
        return self.reopen_issue_method

    @property
    def close_issue_body(self) -> dict[str, str]:
        return {
            "state_event": "close"
        }

    def _init_http_client(self) -> None:
        self._http_header = self.create_http_header(self._token)
        self._http_client = httpx.Client(
            headers=self._http_header
        )

    def __init__(self, token: str):
        super().__init__(token)
        self._platform_type = GitlabClient.name
        self._init_http_client()

    def _get_comments_from_platform(
        self,
        url: str,
    ) -> list[IssueInfo.Comment]:
        ''' api结构详见：
        https://docs.gitlab.com/ee/api/notes.html#list-project-issue-notes\n
        page参数：
        https://docs.gitlab.com/ee/api/rest/index.html#pagination
        '''
        print(Log.getting_something.format(something=Log.issue_comment))
        comments: list[IssueInfo.Comment] = []
        page = 1
        while True:
            response: httpx.Response = self.http_request(
                url=url,
                params={"page": str(page)}
            )
            raw_json: list[GitlabCommentJson
                           ] = response.json()
            if len(raw_json) == 0:
                break
            comments.extend(
                [IssueInfo.Comment(author=comment["author"]["username"],
                                   body=comment["body"])
                 for comment in raw_json])
            page += 1
        print(Log.getting_something_success.
              format(something=Log.issue_comment))
        return comments

    def _get_issue_info_from_platform(self, issue_url: str) -> Issue:
        ''' 所需http header结构详见：
        https://docs.gitlab.com/ee/api/issues.html#single-issue'''
        print(Log.getting_issue_info)
        response = self.http_request(
            method="GET",
            url=issue_url
        )
        print(Log.getting_issue_info_success)
        raw_json = response.json()
        return Issue(
            id=raw_json["iid"],
            title=raw_json["title"],
            state=parse_issue_state(raw_json["state"]),
            body=raw_json["description"],
            labels=raw_json["labels"],
            issue_web_url=raw_json["web_url"],
        )

    def reopen_issue(self, issue_url: str) -> None:
        ''' api结构详见：
        https://docs.gitlab.com/ee/api/issues.html#edit-an-issue'''
        url = issue_url
        print(Log.reopen_issue
              .format(issue_number=get_issue_id_from_url(
                  issue_url)))
        self.http_request(
            method=self.reopen_issue_method,
            url=url,
            json_content=self.reopen_issue_body
        )
        print(Log.reopen_issue_success
              .format(issue_number=get_issue_id_from_url(
                  issue_url))
              )

    def close_issue(self, issue_url: str) -> None:
        ''' api结构详见：
        https://docs.gitlab.com/ee/api/issues.html#edit-an-issue'''
        url = issue_url
        print(Log.close_issue
              .format(issue_number=get_issue_id_from_url(
                  issue_url)))
        self.http_request(
            method=self.close_issue_method,
            url=url,
            json_content=self.close_issue_body
        )
        print(Log.close_issue_success
              .format(issue_number=get_issue_id_from_url(
                  issue_url))
              )

    def close(self):
        self._http_client.close()
