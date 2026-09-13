import time

from app_config import config
from issue_processor.git_service_client import (
    GitlabClient,
)
from issue_processor.issues_processor import IssueProcessor
from auto_archiving.archive_document import ArchiveDocument
from shared.ci_event_type import CiEventType
from shared.env import Env
from shared.log import Log
from shared.env import should_run_in_local
from shared.get_args import get_value_from_args
from shared.exception import *  # noqa: F403
from shared.send_comment import build_error_comment
from utils.env import get_env


def main() -> None:
    start_time = time.time()

    if should_run_in_local():
        print(Log.non_platform_action_env)
        from dotenv import load_dotenv

        load_dotenv()

    config.load_env_config()

    if get_env(Env.CI_EVENT_TYPE) in CiEventType.manual:
        print(Log.running_ci_by_manual)
    else:
        print(Log.running_ci_by_automated)

    test_platform_type = get_value_from_args(
        short_arg="-pt",
        long_arg="--platform-type",
    )

    if not GitlabClient.should_issue_type_webhook():
        return

    platform = IssueProcessor.init_git_service_client(test_platform_type, config)

    try:
        issue_info = IssueProcessor.init_issue_info(platform)
    except WebhookPayloadError:
        # gitlab的webhook无法像github那样按事件类型订阅，
        # 非Issue事件（例如push事件）也会把本流水线拉起来，
        # 这种情况下读不到webhook payload，属于“无关事件”而不是错误，
        # 所以静默return：不reopen issue、不发告警评论，也不让流水线失败
        return

    try:
        platform.enrich_missing_issue_info(issue_info)

        if IssueProcessor.should_skip_archived_process(issue_info, config):
            print(Log.manually_skip_archived_process)
            IssueProcessor.close_issue_if_not_closed(issue_info, platform)
            return

        if IssueProcessor.verify_not_archived_object(issue_info, config):
            return

        IssueProcessor.update_issue_info_with_gather_info(
            issue_info, IssueProcessor.gather_info_from_issue(issue_info, config)
        )
        IssueProcessor.parse_issue_info_for_archived(issue_info, config)
        IssueProcessor.close_issue_if_not_closed(issue_info, platform)

        # 将issue内容写入归档文件
        archive_document = ArchiveDocument()
        archive_document.file_load(config.from_env.archived_document_path)

        if (
            CiEventType.should_ci_running_in_issue_event()
            and archive_document.should_issue_record_exists(
                issue_info.issue_repository, issue_info.issue_id
            )
        ):
            comment_message = Log.issue_already_archived.format(
                issue_id=issue_info.issue_id,
                issue_repository=issue_info.issue_repository,
            )
            print(comment_message)
            platform.send_comment(
                issue_info.links.comment_url,
                comment_message,
                config.post_comment_prefix,
            )
            return

        archive_document.archive_issue(config.archived_document, issue_info)
        issue_info.set_archived_success()

        # 为了后续推送文档和发送归档成功评论的脚本
        # 而将issue信息输出一个json文件
        issue_info.json_dump(config.from_env.issue_output_path)

    except ArchiveBaseError as exc:
        print(Log.archiving_condition_not_satisfied)
        platform.reopen_issue(issue_info.links.issue_url)
        platform.send_comment(
            issue_info.links.comment_url,
            build_error_comment(str(exc)),
            config.post_comment_prefix,
        )
        raise
    finally:
        platform.close()
        try:
            archive_document.save()
        except Exception:
            pass

        print(Log.time_used.format(time="{:.4f}".format(time.time() - start_time)))

        print(Log.job_done)


if __name__ == "__main__":
    main()
