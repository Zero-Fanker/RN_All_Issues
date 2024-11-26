import os

from issue_processor.issue_platform import (Platform,
                                            Github,
                                            Gitlab,
                                            )
from shared.ci_event_type import CiEventType
from issue_processor.json_config import Config
from shared.env import Env
from shared.log import Log
from shared.env import (should_run_in_github_action,
                        should_run_in_gitlab_ci,
                        should_run_in_local)
from shared.get_args import get_value_from_args
from shared.exception import *


# TODO
# 虽然配置文件里有black list的配置项，但是由于暂时用不到
# 所以并没有实现黑名单的功能


def main() -> None:
    if os.environ[Env.CI_EVENT_TYPE] in CiEventType.manual:
        print(Log.running_ci_by_manual)
    else:
        print(Log.running_ci_by_automated)
    config = Config(get_value_from_args(
        short_arg="-c",
        long_arg="--config",
    ))
    platform: Platform

    if should_run_in_local():
        print(Log.non_platform_action_env)
        from dotenv import load_dotenv
        load_dotenv()

    if not Gitlab.should_issue_type_webhook():
        return

    test_platform_type = get_value_from_args(
        short_arg="-pt",
        long_arg="--platform-type",
    )
    if test_platform_type is None:
        if should_run_in_github_action():
            platform = Github()
        elif should_run_in_gitlab_ci():
            platform = Gitlab()
        # 这里特意没写else，如果本地手动执行脚本的时候
        # 没有添加--platform-type或-pt参数
        # 就会跑到这里的else语句了
        # 且不需要else已经足够判断生产环境了
    else:
        print(Log.get_test_platform_type
              .format(test_platform_type=test_platform_type))
        if test_platform_type == Github.name:
            platform = Github()
        elif test_platform_type == Gitlab.name:
            try:
                platform = Gitlab()
            except WebhookPayloadError:
                return
        else:
            print(Log.unexpected_platform_type
                  .format(
                      platform_type=test_platform_type
                  ))

    try:
        # gitlab的issue webhook是会相应issue reopen事件的
        # gitlab的reopen issue事件应该被跳过
        # 而手动触发的流水线有可能目标Issue是还没被closed的
        if (not platform.should_ci_running_in_manual
                and platform.should_issue_state_open):
            print(Log.issue_state_is_open)
            return

        if platform.should_issue_state_update:
            print(Log.issue_state_is_update)
            return

        platform.init_issue_info_from_platform()

        issue_type: str = ""
        if platform.should_issue_type_auto_detect:
            issue_type = platform.get_issue_type_from_labels(
                config.issue_type.label_map
            )
        else:
            issue_type = platform.issue_type

        # 自动触发流水线必须从描述中获取引入版本号
        # 手动触发流水线如果没有填引入版本号，
        # 那么还得从描述里获取引入版本号
        introduced_version: str = ""
        if not platform.should_introduced_version_input:
            introduced_version = platform.get_introduced_version_from_description(
                issue_type,
                config.introduced_version_reges,
                config.issue_type.need_introduced_version_issue_type
            )
        else:
            introduced_version = platform.introduced_version

        archive_version: str = ""
        # 手动流水线的情况
        if platform.should_ci_running_in_manual:
            if not platform.should_archived_version_input:
                archive_version_list = platform.get_archive_version(
                    config.white_list.comments
                )
                if not platform.should_archive_issue(
                    issue_type,
                    config.issue_type.label_map,
                    archive_version_list,
                    platform.get_labels(),
                    config.white_list.labels
                ):
                    raise MissingArchiveVersionAndArchiveLabel(
                        ErrorMessage.missing_labels_and_archive_version
                    )
                archive_version = platform.parse_archive_version(
                    archive_version_list
                )
            else:
                archive_version = platform.archive_version
        # 自动流水线要判断是否是非归档issue被正常关闭了
        # 例如格式错误的issue被创建者手动关闭了
        else:
            archive_version_list = platform.get_archive_version(
                config.white_list.comments
            )
            if not platform.should_archive_issue(
                issue_type,
                config.issue_type.label_map,
                archive_version_list,
                platform.get_labels(),
                config.white_list.labels
            ):
                print(Log.not_archive_issue)
                return
            archive_version = platform.parse_archive_version(
                archive_version_list
            )

        platform.remove_type_in_issue_title(
            config.issue_type.type_keyword
        )

        platform.issue_content_to_json(
            archive_version,
            introduced_version,
            issue_type
        )

        if (platform.should_ci_running_in_manual
                and platform.should_issue_state_open):
            platform.close_issue()
        print(Log.job_done)
    except (
        ArchiveBaseError
    ) as exc:
        print(Log.archiving_condition_not_satisfied)
        platform.reopen_issue()
        platform.send_comment(str(exc))
        raise
    finally:
        platform.close()


if __name__ == "__main__":
    main()
