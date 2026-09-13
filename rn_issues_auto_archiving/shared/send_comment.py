from app_config import config, join_hints
from shared.exception import ErrorMessage
from shared.http_request import http_request
from shared.log import Log


def format_comment(message: str, prefix: str) -> str:
    """给评论加上本脚本的标识前缀，前缀为空时不加（也不会多出一个空格）"""
    return f"{prefix} {message}" if prefix else message


def send_comment(
    comment_url: str,
    http_header: dict[str, str],
    message: str,
    prefix: str,
) -> None:
    """api结构详见：\n
    Github ： https://docs.github.com/zh/rest/issues/comments?apiVersion=2022-11-28#create-an-issue-comment \n
    Gitlab ： https://docs.gitlab.com/ee/api/notes.html#create-new-issue-note \n
    两边API创建评论所需的参数都是一致的
    """
    print(Log.sending_something.format(something=Log.issue_comment))
    http_request(
        method="POST",
        url=comment_url,
        headers=http_header,
        json_content={"body": format_comment(message, prefix)},
    )
    print(Log.sending_something_success.format(something=Log.issue_comment))


def build_error_comment(error_message: str) -> str:
    """在报错信息后追加“如何跳过归档流程”的提示，方便Issue作者自助处理"""
    return "{}\n\n{}".format(
        error_message,
        ErrorMessage.skip_archived_hint.format(
            hints=join_hints(config.skip_archived_reges_for_comments)
        ),
    )
