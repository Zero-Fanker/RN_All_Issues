import os
import time
import json
from pathlib import Path

from exceptiongroup import ExceptionGroup

from shared.exception import ErrorMessage, IssueInfoMissing
from shared.env import Env, should_run_in_github_action,should_run_in_gitlab_ci
from shared.log import Log
from shared.issue_info import (IssueInfo, IssueInfoJson)
from shared.ci_event_type import CiEventType
from shared.json_dumps import json_dumps
# from auto_archiving.failed_record import FailedRecord
from auto_archiving.archive_document import ArchiveDocument
from auto_archiving.json_config import Config
from auto_archiving.send_comment import send_comment
from auto_archiving.reopen_issue import reopen_issue
from shared.get_args import get_value_from_args

def load_local_env() -> None:
    print(Log.non_github_action_env)
    from dotenv import load_dotenv
    load_dotenv()

def main():
    start_time = time.time()
    if (not should_run_in_github_action()
        and not should_run_in_gitlab_ci()):
        load_local_env()

    # 因为暂时用不到，禁用 failed_record 本机记录功能
    # failed_record = FailedRecord(get_value_from_args(
    #     short_arg="-fr",
    #     long_arg="--failed-record"
    # ))
    output_path = os.environ[Env.ISSUE_OUTPUT_PATH]
    issue_repository = os.environ[Env.ISSUE_REPOSITORY]
    comment_message: str = Log.uninitialized_message
    enable_send_comment = True
    issue_info_json: IssueInfoJson
    exceptions = []
    try:
        issue_info_json = json.loads(
            Path(output_path
                 ).read_text(encoding="utf-8")
        )
        print(Log.print_issue_info
              .format(issue_info=json_dumps(
                  IssueInfoJson.remove_sensitive_info(issue_info_json)
              )))
    except FileNotFoundError:
        print(Log.issue_output_not_found)
        return
    try:
        issue_info = IssueInfo(
            reopen_info=IssueInfo.ReopenInfo(
                **issue_info_json.pop("reopen_info")
            ),
            **issue_info_json
        )

        config = Config(get_value_from_args(
            short_arg="-c",
            long_arg="--config"
        ))

        archive_document = ArchiveDocument(
            config.archive_document_path
        )
        # 因为暂时用不到，禁用 failed_record 本机记录功能
        # for issue_id in failed_record.get_all_issue_id():
        #     if archive_document.should_issue_archived(
        #         issue_id,
        #         issue_repository
        #     ):
        #         failed_record.remove_record(issue_id)

        if (issue_info.ci_event_type in CiEventType.issue_event
                and archive_document.should_issue_archived(
                    issue_info.issue_id,
                    issue_repository
                )
            ):
            message = (Log.issue_already_archived
                       .format(issue_id=issue_info.issue_id,
                               issue_repository=issue_repository))
            print(message)
            comment_message = message
            return

        archive_document.archive_issue(
            rjust_character=config.rjust_character,
            rjust_space_width=config.rjust_space_width,
            table_separator=config.table_separator,
            archive_template=config.archive_template,
            issue_title_processing_rules=config.issue_title_processing_rules,
            issue_id=issue_info.issue_id,
            issue_type=issue_info.issue_type,
            issue_title=issue_info.issue_title,
            issue_repository=issue_repository,
            introduced_version=issue_info.introduced_version,
            archive_version=issue_info.archive_version,
            replace_mode=(
                issue_info.ci_event_type in CiEventType.manual
            )
        )

        comment_message = Log.issue_archived_success.format(
            issue_id=issue_info.issue_id,
            issue_repository=issue_repository
        )
    except Exception as exc:
        exceptions.append(exc)
        comment_message = ErrorMessage.archiving_failed.format(
            exc=str(exc)
        )
        print(ErrorMessage.archiving_failed.format(
            exc=str(exc)
        ))
        try:
            issue_info
        except NameError as exc_:
            raise IssueInfoMissing(
                ErrorMessage.load_issue_info_failed
                .format(
                    output_path=output_path,
                    exc=str(exc_)
                )
            )
        # 因为暂时用不到，禁用 failed_record 本机记录功能
        # failed_record.add_record(
        #     issue_id=issue_info.issue_id,
        #     issue_title=issue_info.issue_title,
        #     issue_repository=issue_repository,
        #     reason=str(exc)
        # )
        try:
            reopen_issue(
                http_header=issue_info.reopen_info.http_header,
                reopen_url=issue_info.reopen_info.reopen_url,
                reopen_http_method=issue_info.reopen_info.reopen_http_method,
                reopen_body=issue_info.reopen_info.reopen_body
            )
        except Exception as exc_:
            exceptions.append(exc_)
            print(ErrorMessage.reopen_issue_failed
                  .format(exc=str(exc_)
                          ))

        raise ExceptionGroup(
            ErrorMessage.aggregation_error,
            exceptions
        )
    finally:
        if enable_send_comment:
            try:
                send_comment(
                    http_header=issue_info.reopen_info.http_header,
                    comment_url=issue_info.reopen_info.comment_url,
                    message=comment_message
                )

            except Exception as exc_:
                exceptions.append(exc_)
                print(ErrorMessage.send_comment_failed
                      .format(exc=str(exc_)
                              ))
        try:
            archive_document.save()
            archive_document.close()
        except Exception:
            pass
        # 因为暂时用不到，禁用 failed_record 本机记录功能
        # failed_record.save()
        print(Log.time_used.format(
            time="{:.4f}".format(
                time.time() - start_time)
        ))
        print(Log.job_down)


if __name__ == "__main__":
    main()
