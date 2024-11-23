

import os
import json
from pathlib import Path
import hashlib

import httpx

from shared.env import Env
from shared.log import Log
from shared.exception import ErrorMessage
from auto_archiving.send_comment import send_comment
from auto_archiving.reopen_issue import reopen_issue
from auto_archiving.http_request import http_request
from issue_processor.issue_platform import Gitlab
from shared.issue_info import IssueInfoJson
from shared.issue_state import IssueState


def get_issue_id_from_issue_info(webhook_path: str) -> int:
    try:
        payload: IssueInfoJson = json.loads(
            Path(webhook_path).read_text(encoding="utf-8")
        )
        return payload["issue_id"]
    except FileNotFoundError:
        print(Log.issue_output_not_found_skip_push)
        return -1


def should_no_change(
    local_sha256: str,
    remote_sha256: str,
) -> bool:
    return local_sha256 == remote_sha256


def get_file_sha256(
    file_path: str
) -> str:
    print(Log.get_local_file_sha256
          .format(file_path=file_path))
    # 不能直接把read_bytes的内容去计算sha256
    # 即使两边内容一样，read_bytes算出来的sha256与
    # 远端文件的sha256值还是不一致的
    # 用utf-8编码读取再用utf-8去解码就能和远端文件sha256值一致
    result = hashlib.sha256(
        string=Path(file_path).read_text(
            encoding="utf-8"
        ).encode("utf-8"),
        usedforsecurity=True
    ).hexdigest()
    print(Log.get_local_file_sha256_success
          .format(file_path=file_path, sha256=result),
          )
    return result


def get_remote_file_sha256(
    http_header: dict[str, str],
    gitlab_host: str,
    project_id: int,
    file_path: str,
    branch_name: str
) -> str:
    '''获取某仓库某分支下某文件的元数据：
    https://docs.gitlab.com/ee/api/repository_files.html#get-file-metadata-only'''
    print(Log.get_remote_file_sha256
          .format(file_path=file_path))

    response: httpx.Response = http_request(
        method="HEAD",
        url=f'https://{gitlab_host}/api/v4/projects/{project_id}/repository/files/{file_path}?ref={branch_name}',
        headers=http_header
    )
    result = response.headers.get("X-Gitlab-Content-Sha256")
    print(Log.get_remote_file_sha256_success
          .format(file_path=file_path,
                  sha256=result))
    return result


def push_document(
    http_header: dict[str, str],
    gitlab_host: str,
    project_id: int,
    file_path: str,
    file_content: str,
    branch_name: str,
    author_email: str,
    author_name: str,
    commit_message: str
) -> None:
    ''' 更新仓库内文件的文档：
    https://docs.gitlab.com/ee/api/repository_files.html#update-existing-file-in-repository 
    '''
    print(Log.pushing_document)
    http_request(
        headers=http_header,
        method="PUT",
        url=f'https://{gitlab_host}/api/v4/projects/{project_id}/repository/files/{file_path}',
        json_content={
            "branch": branch_name,
            "author_email": author_email,
            "author_name": author_name,
            "content": file_content,
            "commit_message": commit_message
        }
    )
    print(Log.pushing_document_success)


def main():
    issue_id = get_issue_id_from_issue_info(
        os.environ[Env.ISSUE_OUTPUT_PATH])
    if issue_id == -1:
        return

    archived_document_path = os.environ[Env.ARCHIVED_DOCUMENT_PATH]
    gitlab_host = os.environ[Env.GITLAB_HOST]
    project_id = int(os.environ[Env.PROJECT_ID])
    token = os.environ[Env.TOKEN]
    http_header = Gitlab.create_http_header(token)

    try:

        local_sha256 = get_file_sha256(
            archived_document_path
        )
        remote_sha256 = get_remote_file_sha256(
            http_header,
            gitlab_host,
            project_id,
            archived_document_path,
            os.environ["branch"]
        )
        if should_no_change(local_sha256, remote_sha256):
            print(Log.not_need_to_push_document
                  .format(file_path=archived_document_path))
            return
        else:
            print(Log.need_to_push_document
                  .format(file_path=archived_document_path))

        push_document(
            http_header,
            gitlab_host,
            project_id,
            archived_document_path,
            Path(archived_document_path).read_text("utf-8"),
            os.environ["branch"],
            os.environ["author_email"],
            os.environ["author_name"],
            os.environ["commit_message"].format(
                issue_id=issue_id
            )
        )
    except Exception as exc:
        print(Log.push_document_failed
              .format(exc=str(exc)))
        base_url = f"https://{gitlab_host}/api/v4/projects/{project_id}/issues/{issue_id}"
        reopen_issue(
            http_header=http_header,
            reopen_url=base_url,
            reopen_http_method="PUT",
            reopen_body={
                "state_event": "reopen"
            }
        )
        send_comment(
            http_header=http_header,
            comment_url=f'{base_url}/notes',
            message=ErrorMessage.push_document_failed
            .format(exc=str(exc))
        )
        raise


if __name__ == "__main__":
    main()
