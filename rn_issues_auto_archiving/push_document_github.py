from shared.env import Env
from shared.log import Log
from utils.cmd import cmd_run
from utils.env import get_env, must_get_env


def main():
    archived_document_path = must_get_env(Env.ARCHIVED_DOCUMENT_PATH)
    target_branch = must_get_env(Env.TARGET_BRANCH)

    cmd_run(["git", "config", "user.name", "github-actions[bot]"])
    cmd_run(
        [
            "git",
            "config",
            "user.email",
            "41898282+github-actions[bot]@users.noreply.github.com",
        ]
    )
    cmd_run(["git", "add", archived_document_path])

    if cmd_run(["git", "diff", "--cached"]) == "":
        print(Log.archived_document_no_change)
        return

    print(Log.archived_document_has_change)
    # 自动触发流水线时MANUAL_ISSUE_NUMBER为空，
    # 手动触发流水线时ISSUE_NUMBER为空
    commit_message = "{}{}{}".format(
        get_env(Env.COMMIT_TITLE, str, ""),
        get_env(Env.ISSUE_NUMBER, str, ""),
        get_env(Env.MANUAL_ISSUE_NUMBER, str, ""),
    )
    cmd_run(["git", "commit", "-m", commit_message])
    cmd_run(["git", "push", "origin", target_branch])


if __name__ == "__main__":
    main()
