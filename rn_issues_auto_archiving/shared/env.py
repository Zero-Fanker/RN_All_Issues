from utils.env import get_env


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
    COMMIT_TITLE = "COMMIT_TITLE"

    # gitlab ci
    GITLAB_CI = "GITLAB_CI"
    WEBHOOK_PAYLOAD = "WEBHOOK_PAYLOAD"
    GITLAB_HOST = "GITLAB_HOST"
    ARCHIVED_DOCUMENT_PATH = "ARCHIVED_DOCUMENT_PATH"
    WEBHOOK_OUTPUT_PATH = "WEBHOOK_OUTPUT_PATH"
    PROJECT_ID = "PROJECT_ID"
    API_BASE_URL = "API_BASE_URL"
    TOKEN_TTL_DAYS = "TOKEN_TTL_DAYS"
    TARGET_VARIABLE_NAME = "TARGET_VARIABLE_NAME"

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

    # push_document 提交归档文件时使用
    AUTHOR_EMAIL = "author_email"
    AUTHOR_NAME = "author_name"
    COMMIT_MESSAGE = "commit_message"


def should_run_in_github_action() -> bool:
    return get_env(Env.GITHUB_ACTIONS, bool, False)


def should_run_in_gitlab_ci() -> bool:
    return get_env(Env.GITLAB_CI, bool, False)


def should_run_in_local() -> bool:
    return not should_run_in_github_action() and not should_run_in_gitlab_ci()
