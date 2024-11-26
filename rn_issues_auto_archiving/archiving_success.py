import json
import os
from pathlib import Path

from shared.log import Log
from shared.issue_info import IssueInfo
from shared.get_args import get_value_from_args
from shared.issue_info import IssueInfoJson
from shared.json_dumps import json_dumps
from shared.env import (Env,
                        should_run_in_local
                        )
from auto_archiving.send_comment import send_comment
from issue_processor.issue_platform import Gitlab, Github


def main():
    if should_run_in_local():
        print(Log.non_platform_action_env)
        from dotenv import load_dotenv
        load_dotenv()

    output_path = os.environ[Env.ISSUE_OUTPUT_PATH]
    issue_repository = os.environ[Env.ISSUE_REPOSITORY]
    token = os.environ[Env.TOKEN]
    
    issue_info_json: IssueInfoJson
    issue_info: IssueInfo
    try:
        issue_info_json = json.loads(
            Path(output_path
                 ).read_text(encoding="utf-8")
        )
        print(Log.print_issue_info
              .format(issue_info=json_dumps(
                  IssueInfoJson.remove_sensitive_info(issue_info_json)
              )))
        issue_info = IssueInfo(
            reopen_info=IssueInfo.ReopenInfo(
                **issue_info_json.pop("reopen_info")
            ),
            **issue_info_json
        )
    except FileNotFoundError:
        print(Log.issue_output_not_found)
        return

    http_header: dict[str, str]
    if issue_info.platform_type == Github.name:
        http_header = Github.create_http_header(
            token=token
        )
    elif issue_info.platform_type == Gitlab.name:
        http_header = Gitlab.create_http_header(
            token=token
        )
    else:
        raise ValueError(
            Log.unknown_platform_type
            .format(
                platform_type=issue_info.platform_type
            ))
    try:
        send_comment(
            comment_url=issue_info.reopen_info.comment_url,
            http_header=http_header,
            message=Log.issue_archived_success.format(
                issue_id=issue_info.issue_id,
                issue_repository=issue_repository
            )
        )
    except Exception as exc:
        # 归档成功评论发送失败并不重要，失败就失败了
        # 如果是一开始流水线就有权限或者是链路问题，
        # 那么前面的流程就会报错
        # 也不会执行到这里
        print(Log.send_comment_failed
              .format(
                  exc=str(exc)
              ))
    print(Log.job_done)


if __name__ == "__main__":
    main()
