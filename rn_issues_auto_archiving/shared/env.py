import os


class Env:
    # github action
    GITHUB_ACTIONS = "GITHUB_ACTIONS"
    ISSUE_STATE = "ISSUE_STATE"
    ISSUE_BODY = "ISSUE_BODY"
    MANUAL_ISSUE_NUMBER = "MANUAL_ISSUE_NUMBER"
    MANUAL_ISSUE_TITLE = "MANUAL_ISSUE_TITLE"
    MANUAL_ISSUE_STATE = "MANUAL_ISSUE_STATE"
    MANUAL_ISSUE_URL = "MANUAL_ISSUE_URL"
    MANUAL_COMMENTS_URL = "MANUAL_COMMENTS_URL"
    ISSUE_URL = "ISSUE_URL"
    COMMENTS_URL = "COMMENTS_URL"

    # gitlab ci
    GITLAB_CI = "GITLAB_CI"
    WEBHOOK_PAYLOAD = "WEBHOOK_PAYLOAD"
    GITLAB_HOST = "GITLAB_HOST"
    ARCHIVED_DOCUMENT_PATH = "ARCHIVED_DOCUMENT_PATH"
    WEBHOOK_OUTPUT_PATH = "WEBHOOK_OUTPUT_PATH"
    PROJECT_ID = "PROJECT_ID"
    API_BASE_URL = "API_BASE_URL"

    # 两侧均可直接读取的环境变量
    # 或者是放仓库变量的
    TOKEN = "TOKEN"
    ISSUE_OUTPUT_PATH = "ISSUE_OUTPUT_PATH"
    ISSUE_REPOSITORY = "ISSUE_REPOSITORY"
    CI_EVENT_TYPE = "CI_EVENT_TYPE"
    ARCHIVE_VERSION = "ARCHIVE_VERSION"
    INTRODUCED_VERSION = "INTRODUCED_VERSION"
    ISSUE_NUMBER = "ISSUE_NUMBER"
    ISSUE_TITLE = "ISSUE_TITLE"
    ISSUE_TYPE = "ISSUE_TYPE"
    TARGET_BRANCH = "TARGET_BRANCH"


def should_run_in_github_action() -> bool:
    return os.environ.get(Env.GITHUB_ACTIONS) == "true"


def should_run_in_gitlab_ci() -> bool:
    return os.environ.get(Env.GITLAB_CI) == "true"


def should_run_in_local() -> bool:
    return not should_run_in_github_action() and not should_run_in_gitlab_ci()
