from shared.log import Log
from shared.http_request import http_request


def reopen_issue(
    http_header: dict[str, str],
    reopen_url: str,
    reopen_http_method: str,
    reopen_body: dict[str, str]
) -> None:
    '''api结构详见：
        https://docs.gitlab.com/ee/api/issues.html#edit-an-issue'''
    print(Log.reopen_issue_request)
    http_request(
        method=reopen_http_method,
        url=reopen_url,
        headers=http_header,
        json_content=reopen_body
    )
    print(Log.reopen_issue_request_success)
