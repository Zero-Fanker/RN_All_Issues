import httpx

from shared.log import Log
from auto_archiving.http_request import http_request


def send_comment(
        comment_url: str,
        http_header: str,
        message: str
) -> None:
    ''' api结构详见：\n
        Github ： https://docs.github.com/zh/rest/issues/comments?apiVersion=2022-11-28#create-an-issue-comment \n
        Gitlab ： https://docs.gitlab.com/ee/api/notes.html#create-new-issue-note \n
        两边API创建评论所需的参数都是一致的
        '''
    print(Log.sending_something
          .format(
              something=Log.issue_comment
          ))
    http_request(
        method="POST",
        url=comment_url,
        headers=http_header,
        json_content={
            "body": message
        },
    )
    print(Log.sending_something_success
          .format(
              something=Log.issue_comment
          ))
