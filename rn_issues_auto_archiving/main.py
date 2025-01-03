import os
import time

from issue_processor.git_service_client import (
    GitlabClient,
)
from issue_processor.issues_processor import IssueProcessor
from auto_archiving.archive_document import ArchiveDocument
from shared.config_manager import ConfigManager
from shared.config_data_source import EnvConfigDataSource, JsonConfigDataSource
from shared.ci_event_type import CiEventType
from shared.env import Env
from shared.log import Log
from shared.env import should_run_in_local
from shared.get_args import get_value_from_args
from shared.exception import *


def main() -> None:
    start_time = time.time()

    if os.environ[Env.CI_EVENT_TYPE] in CiEventType.manual:
        print(Log.running_ci_by_manual)
    else:
        print(Log.running_ci_by_automated)

    if should_run_in_local():
        print(Log.non_platform_action_env)
        from dotenv import load_dotenv
        load_dotenv()

    test_platform_type = get_value_from_args(
        short_arg="-pt",
        long_arg="--platform-type",
    )
    config_path = get_value_from_args(
        short_arg="-c",
        long_arg="--config",
    )

    if config_path is None:
        print(Log.config_path_not_found)
        return

    if not GitlabClient.should_issue_type_webhook():
        return

    config = IssueProcessor.init_config(
        ConfigManager([
            EnvConfigDataSource(),
            JsonConfigDataSource(config_path)
        ])
    )

    platform = IssueProcessor.init_git_service_client(
        test_platform_type,
        config
    )

    try:
        issue_info = IssueProcessor.init_issue_info(platform)
    except WebhookPayloadError:
        return

    try:
        platform.enrich_missing_issue_info(issue_info)
        
        if IssueProcessor.should_skip_archived_process(
            issue_info, 
            config.skip_archived_reges_for_comments
        ):
            print(Log.manually_skip_archived_process)
            IssueProcessor.close_issue_if_not_closed(
                issue_info,
                platform
            )
            return

        if IssueProcessor.verify_not_archived_object(
            issue_info, config
        ):
            return

        IssueProcessor.update_issue_info_with_gather_info(
            issue_info,
            IssueProcessor.gather_info_from_issue(
                issue_info,
                config
            )
        )
        IssueProcessor.parse_issue_info_for_archived(
            issue_info,
            config
        )
        IssueProcessor.close_issue_if_not_closed(
            issue_info,
            platform
        )

        # 将issue内容写入归档文件
        archive_document = ArchiveDocument()
        archive_document.file_load(config.archived_document_path)

        if (CiEventType.should_ci_running_in_issue_event()
                and archive_document.should_issue_record_exists(
                    issue_info.issue_repository,
                    issue_info.issue_id
        )):
            comment_message = (Log.issue_already_archived
                               .format(issue_id=issue_info.issue_id,
                                       issue_repository=issue_info.issue_repository))
            print(comment_message)
            platform.send_comment(
                issue_info.links.comment_url,
                comment_message
            )
            return

        archive_document.archive_issue(
            # 归档内容格式规则
            rjust_space_width=config.archived_document.rjust_space_width,
            rjust_character=config.archived_document.rjust_character,
            table_separator=config.archived_document.table_separator,
            archive_template=config.archived_document.archive_template,
            fill_issue_url_by_repository_type=config.archived_document.fill_issue_url_by_repository_type,
            issue_title_processing_rules=config.archived_document.issue_title_processing_rules,

            # 归档所需issue数据
            issue_id=issue_info.issue_id,
            issue_type=issue_info.issue_type,
            issue_title=issue_info.issue_title,
            issue_repository=issue_info.issue_repository,
            introduced_version=issue_info.introduced_version,
            issue_url=issue_info.links.issue_web_url,
            archive_version=issue_info.archive_version,

            replace_mode=(
                issue_info.ci_event_type in CiEventType.manual
            )
        )
        issue_info.set_archived_success()

        # 为了后续推送文档和发送归档成功评论的脚本
        # 而将issue信息输出一个json文件
        issue_info.json_dump(
            config.issue_output_path
        )

    except (
        ArchiveBaseError
    ) as exc:
        print(Log.archiving_condition_not_satisfied)
        platform.reopen_issue(
            issue_info.links.issue_url
        )
        platform.send_comment(
            issue_info.links.comment_url,
            str(exc)
        )
        raise
    finally:
        platform.close()
        try:
            archive_document.save()
        except Exception:
            pass

        print(Log.time_used.format(
            time="{:.4f}".format(
                time.time() - start_time)
        ))

        print(Log.job_done)


if __name__ == "__main__":
    main()
