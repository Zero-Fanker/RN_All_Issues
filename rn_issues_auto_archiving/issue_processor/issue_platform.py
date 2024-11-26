import os
import re
import json
from dataclasses import dataclass, asdict
from abc import abstractmethod, ABC
from http import HTTPStatus

import httpx

from shared.log import Log
from shared.env import Env
from shared.exception import *
from shared.issue_info import IssueInfoJson
from shared.issue_state import IssueState, parse_issue_state
from shared.ci_event_type import CiEventType
from shared.json_dumps import json_dumps

AUTO_ISSUE_TYPE = "自动判断"


@dataclass()
class Urls():
    issue_url: str
    comments_url: str

    class ApiPath():
        base = "api/v4"
        projects = "projects"
        issues = "issues"
        notes = "notes"


@dataclass()
class Comment():
    author: str
    body: str


@dataclass()
class Issue():
    id: int
    title: str
    state: str
    body: str
    labels: list[str]
    introduced_version: str = ""
    archive_version: str = ""
    issue_type: str = AUTO_ISSUE_TYPE


@dataclass()
class PlatformEnvironments():
    token: str
    issue_number: int
    issue_title: str
    issue_state: str
    issue_body: str
    issue_url: str
    comments_url: str


class Platform(ABC):
    @staticmethod
    def issue_number_to_int(issue_number: str):
        if not issue_number.isdigit():
            raise ValueError(
                Log.invalid_issue_number
                .format(issues_number_var=issue_number))
        return int(issue_number.strip())

    @abstractmethod
    def _get_labels_from_platform(self) -> list[str]:
        pass

    @abstractmethod
    def _get_comments_from_platform(
        self,
        http: httpx.Client,
        url: str,
    ) -> list[Comment]:
        pass

    @abstractmethod
    def reopen_issue(self) -> None:
        pass

    @abstractmethod
    def close_issue(self) -> None:
        pass

    @abstractmethod
    def close(self):
        pass

    @abstractmethod
    def _read_platform_environments(self) -> None:
        pass

    @abstractmethod
    def _init_http_client(self) -> None:
        pass

    @abstractmethod
    def get_issue_info_from_platform(self) -> Issue:
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

    @property
    def introduced_version(self) -> str:
        return self._issue.introduced_version

    @property
    def archive_version(self) -> str:
        return self._issue.archive_version

    @property
    def should_issue_state_open(self) -> bool:
        return self._issue.state == IssueState.open

    @property
    def should_issue_state_update(self) -> bool:
        return self._issue.state == IssueState.update

    @property
    def should_ci_running_in_manual(self) -> bool:
        return self._ci_event_type in CiEventType.manual

    @property
    def should_ci_running_in_issue_event(self) -> bool:
        return self._ci_event_type in CiEventType.issue_event

    @property
    def should_archived_version_input(self) -> bool:
        return self._issue.archive_version != ""

    @property
    def should_introduced_version_input(self) -> bool:
        return self._issue.introduced_version != ""

    @property
    def should_issue_type_auto_detect(self) -> bool:
        return self._issue.issue_type == AUTO_ISSUE_TYPE

    @property
    def archived_version(self) -> str:
        return self._issue.archive_version

    @property
    def introduced_version(self) -> str:
        return self._issue.introduced_version

    @property
    def issue_type(self) -> str:
        return self._issue.issue_type

    def __init__(self):
        self._token: str
        self._issue: Issue
        self._urls: Urls
        self._comments: list[Comment]
        self._output_path: str
        self._http_header: dict[str, str]
        self._http_client: httpx.Client
        self._ci_event_type: str
        self._platform_type: str

    def http_request(
        self,
        url: str,
        method: str = "GET",
        params: dict[str, str] = None,
        json_content: dict[str, str] = None,
        retry_times: int = 3,
    ) -> httpx.Response:
        error = None
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
                print(Log.http_status_error
                      .format(
                          reason=json_dumps(
                              response.json(),
                          ),
                      ))
                raise
            except Exception as e:
                error = e
        raise error

    def init_issue_info_from_platform(
        self
    ) -> None:

        self._comments = self._get_comments_from_platform(
            self._http_client,
            self._urls.comments_url
        )

        if self.should_ci_running_in_manual:
            # 手动触发流水线的情况
            # 以防可选项为空，需要打一个请请求获取issue信息
            issue_info = self.get_issue_info_from_platform()
            self._issue.labels = issue_info.labels
            self._issue.state = issue_info.state
            if self._issue.title == "":
                self._issue.title = issue_info.title
            if self._issue.body == "":
                self._issue.body = issue_info.body

        else:
            # issue事件触发流水线的情况
            # 至于为什么要留着_get_labels_from_platform
            # 因为gitlab的webhook载荷里有标签了，没必要在打一次请求
            self._issue.labels = self._get_labels_from_platform()

    def get_introduced_version_from_description(
        self,
        issue_type: str,
        introduced_version_reges: list[str],
        need_introduced_version_issue_type: list[str]
    ) -> str:
        print(Log.getting_something_from
              .format(another=Log.issue_description, something=Log.introduced_version))
        introduced_versions: list[str] = []
        for regex in introduced_version_reges:
            introduced_versions.extend(
                re.findall(
                    regex,
                    self._issue.body
                )
            )
        introduced_versions = [item.strip() for item in introduced_versions]
        if len(introduced_versions) == 0:
            if any([issue_type == target_issue_type
                    for target_issue_type in need_introduced_version_issue_type]):
                print(Log.introduced_version_not_found)
                raise IntroducedVersionError(
                    ErrorMessage.missing_introduced_version
                )
            else:
                print(Log.introduced_version_not_found)
                return ""

        elif len(introduced_versions) >= 2:
            print(Log.too_many_introduced_version)
            raise IntroducedVersionError(
                ErrorMessage.too_many_introduced_version
                .format(versions=[i for i in introduced_versions])
            )
        print(Log.getting_something_from_success
              .format(another=Log.issue_description, something=Log.introduced_version))
        return introduced_versions[0]

    def get_labels(self) -> list[str]:
        return self._issue.labels

    def get_archive_version(
        self,
        comment_reges: list[str]
    ) -> list[str]:
        print(Log.getting_something_from
              .format(another=Log.issue_comment, something=Log.archive_version))
        result: list[str] = []
        for comment in self._comments:
            for comment_regex in comment_reges:
                if len(archive_version := re.findall(
                        comment_regex, comment.body)) > 0:
                    result.extend(archive_version)

        return result

    def send_comment(self, comment_body: str) -> None:
        ''' api结构详见：\n
        Github ： https://docs.github.com/zh/rest/issues/comments?apiVersion=2022-11-28#create-an-issue-comment \n
        Gitlab ： https://docs.gitlab.com/ee/api/notes.html#create-new-issue-note \n
        两边API创建评论所需的参数都是一致的
        '''
        print(Log.sending_something.format(
            something=Log.announcement_comment))
        self.http_request(
            method="POST",
            url=self._urls.comments_url,
            json_content={
                "body": comment_body
            }
        )
        print(Log.sending_something_success
              .format(something=Log.announcement_comment))

    def should_archive_issue(
        self,
        issue_type: str,
        label_map: dict[str, str],
        archive_version: list[str],
        issue_labels: list[str],
        target_labels: list[str],
        check_labels: bool = True,
        check_archive_version: bool = True
    ) -> bool:

        if (should_not_match_archive_version := (
                len(archive_version) == 0)
                and check_archive_version):
            print(Log.archive_version_not_found)
        else:
            print(Log.archive_version_found)

        # issue所挂标签必须匹配所有白名单标签
        if (should_label_not_in_target := (
                set(issue_labels) & set(target_labels)
                != set(target_labels))
                and check_labels):
            print(Log.target_labels_not_found)
        else:
            print(Log.target_labels_found)

        # 未匹配到归档关键字应则不进行归档流程
        # 因为这有可能是用户自行关闭的issue或者无需归档的issue
        if all([should_label_not_in_target,
                should_not_match_archive_version,
                check_labels,
                check_archive_version]):
            return False

        if (should_label_not_in_target
                and check_labels):
            raise ArchiveLabelError(
                ErrorMessage.missing_archive_labels
                .format(labels=target_labels)
            )

        if (should_not_match_archive_version
                and check_archive_version):
            raise ArchiveVersionError(
                ErrorMessage.missing_archive_version
            )

        if issue_type == "":
            raise IssueTypeError(
                ErrorMessage.missing_issue_type_from_label
                .format(issue_type=list(label_map.keys()))
            )

        return True

    def get_issue_type_from_title(
        self,
        type_keyword: dict[str, str]
    ) -> str:
        print(Log.getting_something_from
              .format(another=Log.issue_title, something=Log.issue_type))
        for keyword, type in type_keyword.items():
            if keyword in self._issue.title:
                print(Log.getting_something_from_success
                      .format(another=Log.issue_title,
                              something=Log.issue_type))
                return type

        print(Log.issue_type_not_found)
        raise IssueTypeError(
            ErrorMessage.missing_issue_type_from_title
            .format(issue_type=list(type_keyword.keys()))
        )

    def get_issue_type_from_labels(
            self,
            label_map: dict[str, str]
    ) -> str:
        print(Log.getting_something_from
              .format(another=Log.issue_label, something=Log.issue_type))
        for label_name, type in label_map.items():
            if label_name in self._issue.labels:
                print(Log.getting_something_from_success
                      .format(another=Log.issue_label,
                              something=Log.issue_type))
                return type

        print(Log.issue_type_not_found)
        return ""

    def remove_type_in_issue_title(
            self,
            type_keyword: dict[str, str]
    ) -> None:
        title = self._issue.title
        # 这里不打算考虑issue标题中
        # 匹配多个issue类型关键字的情况
        # 因为这种情况下脚本完全无法判断
        # issue的真实类型是什么
        for key in type_keyword.keys():
            if key in title:
                self._issue.title = title.replace(
                    key, '').strip()
                break

    def parse_archive_version(
        self,
        archive_version: list[str]
    ) -> str:
        if len(archive_version) >= 2:
            print(Log.too_many_archive_version)
            raise ArchiveVersionError(
                ErrorMessage.too_many_archive_version
                .format(versions=[i for i in archive_version])
            )
        print(Log.getting_something_from_success
              .format(another=Log.issue_comment, something=Log.archive_version))
        return archive_version[0]

    def issue_content_to_json(
        self,
        archive_version: str,
        introduced_version: str,
        issue_type: str
    ) -> None:
        json_path = self._output_path
        issue_json = IssueInfoJson(
            issue_id=self._issue.id,
            issue_type=issue_type,
            issue_title=self._issue.title,
            issue_state=self._issue.state,
            introduced_version=introduced_version,
            archive_version=archive_version,
            ci_event_type=self._ci_event_type,
            platform_type=self._platform_type,
            reopen_info=IssueInfoJson.ReopenInfo(
                http_header=self._http_header,
                reopen_url=self._urls.issue_url,
                reopen_http_method=self.reopen_issue_method,
                reopen_body=self.reopen_issue_body,
                comment_url=self._urls.comments_url,
            )
        )

        print(Log.print_issue_json
              .format(
                  issue_json=json_dumps(
                      IssueInfoJson.remove_sensitive_info(
                          issue_json)
                  ),
              ))
        print(Log.save_issue_content_to_file
              .format(output_path=json_path))

        with open(json_path,
                  "w",
                  encoding="utf-8") as file:
            json.dump(
                issue_json,
                file,
                ensure_ascii=False,
                indent=4
            )
        print(Log.save_issue_content_to_file_success
              .format(output_path=json_path))


class Github(Platform):
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

    def _read_platform_environments(self) -> None:
        print(Log.loading_something.format(something=Log.env))

        self._token = os.environ[Env.TOKEN]
        self._output_path = os.environ[Env.ISSUE_OUTPUT_PATH]

        self._ci_event_type = os.environ[Env.CI_EVENT_TYPE]
        if self.should_ci_running_in_manual:
            self._issue = Issue(
                id=Platform.issue_number_to_int(
                    os.environ[Env.MANUAL_ISSUE_NUMBER]),
                title=os.environ[Env.MANUAL_ISSUE_TITLE].strip(),
                state=parse_issue_state(os.environ[Env.MANUAL_ISSUE_STATE]),
                body="",
                labels=[],
                introduced_version=os.environ[
                    Env.INTRODUCED_VERSION].strip(),
                archive_version=os.environ[
                    Env.ARCHIVE_VERSION].strip(),
                issue_type=os.environ[Env.ISSUE_TYPE],
            )
            print(Log.print_input_variables
                  .format(input_variables=json_dumps(
                      asdict(self._issue),
                  )))
            self._urls = Urls(
                os.environ[Env.MANUAL_ISSUE_URL],
                os.environ[Env.MANUAL_COMMENTS_URL],
            )

        else:
            self._issue = Issue(
                id=int(os.environ[Env.ISSUE_NUMBER]),
                title=os.environ[Env.ISSUE_TITLE],
                state=parse_issue_state(os.environ[Env.ISSUE_STATE]),
                body=os.environ[Env.ISSUE_BODY],
                labels=[],
                introduced_version="",
                archive_version="",
                issue_type=AUTO_ISSUE_TYPE
            )
            self._urls = Urls(
                os.environ[Env.ISSUE_URL],
                os.environ[Env.COMMENTS_URL],
            )

        print(Log.loading_something_success
              .format(something=Log.env))

    def _get_labels_from_platform(self) -> list[str]:
        ''' 所需http header结构详见：
        https://docs.github.com/zh/rest/issues/issues?apiVersion=2022-11-28#get-an-issue'''
        print(Log.getting_something.
              format(something=Log.issue_label))
        response = self.http_request(
            url=self._urls.issue_url,
            method="GET"
        )
        print(Log.getting_something_success.
              format(something=Log.issue_label))
        return [label["name"]
                for label in response.json()["labels"]]

    def _init_http_client(self) -> None:
        self._http_header = self.create_http_header(self._token)
        self._http_client = httpx.Client(
            headers=self._http_header
        )

    def __init__(self):
        super().__init__()
        self._platform_type = Github.name
        self._read_platform_environments()
        self._init_http_client()

    def _get_comments_from_platform(
        self,
        http: httpx.Client,
        url: str,
    ) -> list[Comment]:
        ''' api结构详见：
        https://docs.github.com/zh/rest/issues/comments?apiVersion=2022-11-28#create-an-issue-comment'''
        print(Log.getting_something.format(something=Log.issue_comment))
        comments: list[Comment] = []
        page = 1
        while True:
            response: httpx.Response = self.http_request(
                url=url,
                params={"page": page}
            )
            raw_json: list[dict[str, str]] = response.json()
            if len(raw_json) == 0:
                break
            comments.extend(
                [Comment(author=comment["user"]["login"],
                         body=comment["body"])
                 for comment in raw_json])
            page += 1

        print(Log.getting_something_success.
              format(something=Log.issue_comment))
        return comments

    def get_issue_info_from_platform(self) -> Issue:
        ''' 所需http header结构详见：
        https://docs.github.com/zh/rest/issues/issues?apiVersion=2022-11-28#get-an-issue'''
        print(Log.getting_issue_info)
        response = self.http_request(
            url=self._urls.issue_url,
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
        )

    def reopen_issue(self) -> None:
        ''' api结构详见：
        https://docs.github.com/zh/rest/issues/issues?apiVersion=2022-11-28#update-an-issue'''
        url = self._urls.issue_url
        print(Log.reopen_issue
              .format(issue_number=self._issue.id))
        self.http_request(
            method=self.reopen_issue_method,
            url=url,
            json_content=self.reopen_issue_body
        )
        print(Log.reopen_issue_success
              .format(issue_number=self._issue.id)
              )

    def close_issue(self) -> None:
        ''' api结构详见：
        https://docs.github.com/zh/rest/issues/issues?apiVersion=2022-11-28#update-an-issue'''
        url = self._urls.issue_url
        print(Log.close_issue
              .format(issue_number=self._issue.id))
        self.http_request(
            method=self.close_issue_method,
            url=url,
            json_content=self.close_issue_body
        )
        print(Log.close_issue_success
              .format(issue_number=self._issue.id)
              )

    def close(self):
        self._http_client.close()


class Gitlab(Platform):
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

    def issue_web_url_to_issue_api_url(self,
                                       web_url: str,
                                       project_id: int) -> str:
        project_name_index = -4
        owner_name_index = 3

        # api样例：https://{gitlab_host}/api/v4/projects/{project_id}/issues/{issues_id}
        # web_url样例：https://{gitlab_host}/｛owner｝/{project_name}/-/issues/{issues_id}

        # ['https:', '', '{gitlab_host}', '｛owner｝', '{project_name}', '-', 'issues', '1']

        url_split = web_url.split("/")
        url_split.pop(project_name_index)  # 删掉project_name
        url_split.pop(owner_name_index)  # 删掉project_name
        url_split.remove('-')

        # ['https:', '', '{gitlab_host}', 'issues', '1']

        url_split.insert(3, Urls.ApiPath.base)
        url_split.insert(4, Urls.ApiPath.projects)
        url_split.insert(5, str(project_id))

        # ['https:', '', '{gitlab_host}', 'api/v4', 'projects', '｛project_id｝', 'issues', '1']

        return '/'.join(url_split)

    def _get_labels_from_platform(self) -> list[str]:
        # ''' 所需http header结构详见：
        # https://docs.gitlab.com/ee/api/issues.html#single-issue'''
        # gitlab webhook的payload携带了label了
        print(Log.getting_something.
              format(something=Log.issue_label))
        print(Log.getting_something_success.
              format(something=Log.issue_label))
        return self._issue.labels

    def _read_platform_environments(self) -> None:
        print(Log.loading_something.format(something=Log.env))

        self._token = os.environ[Env.TOKEN]
        self._ci_event_type = os.environ[Env.CI_EVENT_TYPE]
        self._output_path = os.environ[Env.ISSUE_OUTPUT_PATH]

        if self.should_ci_running_in_manual:
            issue_id = os.environ.get(Env.ISSUE_NUMBER, "")
            if issue_id == "":
                raise MissingIssueNumber(
                    Log.missing_issue_number
                    .format(issues_number_var=Env.ISSUE_NUMBER))
            self._issue = Issue(
                id=Platform.issue_number_to_int(issue_id),
                title=os.environ.get(Env.ISSUE_TITLE, "").strip(),
                state=parse_issue_state(
                    os.environ[Env.ISSUE_STATE]),
                body="",
                labels=[],
                introduced_version=os.environ.get(
                    Env.INTRODUCED_VERSION, "").strip(),
                archive_version=os.environ.get(
                    Env.ARCHIVE_VERSION, "").strip(),
                issue_type=os.environ.get(Env.ISSUE_TYPE,
                                          AUTO_ISSUE_TYPE).strip(),
            )
            print(Log.print_input_variables
                  .format(input_variables=json_dumps(
                      asdict(self._issue),
                  )))
            issue_url = f'{os.environ[Env.API_BASE_URL]}{Urls.ApiPath.issues}/{issue_id}'
            self._urls = Urls(
                issue_url=issue_url,
                comments_url=issue_url + '/' + Urls.ApiPath.notes,
            )

        else:
            try:
                webhook_payload = json.loads(
                    os.environ[Env.WEBHOOK_PAYLOAD])
                self._token = os.environ[Env.TOKEN]
            except Exception:
                print(Log.webhook_payload_not_found)
                raise WebhookPayloadError(Log.webhook_payload_not_found)

            issue_id: int = webhook_payload["object_attributes"]["iid"]
            self._issue = Issue(
                # webhook里是json，iid一定是int
                id=issue_id,
                title=webhook_payload["object_attributes"]["title"],
                state=parse_issue_state(
                    webhook_payload["object_attributes"]["action"]),
                body=webhook_payload["object_attributes"]["description"],
                labels=[
                    label_json["title"]
                    for label_json in
                    webhook_payload["object_attributes"]["labels"]],
                introduced_version="",
                archive_version="",
                issue_type=AUTO_ISSUE_TYPE
            )

            issue_url = f'{os.environ[Env.API_BASE_URL]}{Urls.ApiPath.issues}/{issue_id}'
            self._urls = Urls(
                issue_url=issue_url,
                comments_url=issue_url + '/' + Urls.ApiPath.notes,
            )

        print(Log.loading_something_success
              .format(something=Log.env))

    def _init_http_client(self) -> None:
        self._http_header = self.create_http_header(self._token)
        self._http_client = httpx.Client(
            headers=self._http_header
        )

    def __init__(self):
        super().__init__()
        self._platform_type = Gitlab.name
        self._read_platform_environments()
        self._init_http_client()

    def _get_comments_from_platform(
        self,
        http: httpx.Client,
        url: str,
    ) -> list[Comment]:
        ''' api结构详见：
        https://docs.gitlab.com/ee/api/notes.html#list-project-issue-notes\n
        page参数：
        https://docs.gitlab.com/ee/api/rest/index.html#pagination
        '''
        print(Log.getting_something.format(something=Log.issue_comment))
        comments: list[Comment] = []
        page = 1
        while True:
            response: httpx.Response = self.http_request(
                url=url,
                params={"page": page}
            )
            raw_json: list[dict[str, str]] = response.json()
            if len(raw_json) == 0:
                break
            comments.extend(
                [Comment(author=comment["author"]["username"],
                         body=comment["body"])
                 for comment in raw_json])
            page += 1
        print(Log.getting_something_success.
              format(something=Log.issue_comment))
        return comments

    def get_issue_info_from_platform(self) -> Issue:
        ''' 所需http header结构详见：
        https://docs.gitlab.com/ee/api/issues.html#single-issue'''
        print(Log.getting_issue_info)
        response = self.http_request(
            method="GET",
            url=self._urls.issue_url
        )
        print(Log.getting_issue_info_success)
        raw_json = response.json()
        return Issue(
            id=raw_json["iid"],
            title=raw_json["title"],
            state=parse_issue_state(raw_json["state"]),
            body=raw_json["description"],
            labels=raw_json["labels"],
            introduced_version="",
            archive_version=""
        )

    def reopen_issue(self) -> None:
        ''' api结构详见：
        https://docs.gitlab.com/ee/api/issues.html#edit-an-issue'''
        url = self._urls.issue_url
        print(Log.reopen_issue
              .format(issue_number=self._issue.id))
        self.http_request(
            method=self.reopen_issue_method,
            url=url,
            json_content=self.reopen_issue_body
        )
        print(Log.reopen_issue_success
              .format(issue_number=self._issue.id)
              )

    def close_issue(self) -> None:
        ''' api结构详见：
        https://docs.gitlab.com/ee/api/issues.html#edit-an-issue'''
        url = self._urls.issue_url
        print(Log.close_issue
              .format(issue_number=self._issue.id))
        self.http_request(
            method=self.close_issue_method,
            url=url,
            json_content=self.close_issue_body
        )
        print(Log.close_issue_success
              .format(issue_number=self._issue.id)
              )

    def close(self):
        self._http_client.close()
