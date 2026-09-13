from shared.env import Env
from utils.env import get_env


class CiEventType:
    """流水线触发类型 :\n
    github:https://docs.github.com/zh/actions/writing-workflows/choosing-when-your-workflow-runs/events-that-trigger-workflows#about-events-that-trigger-workflows
    gitlab:https://docs.gitlab.com/ee/ci/jobs/job_rules.html#ci_pipeline_source-predefined-variable"""

    manual = ["web", "workflow_dispatch"]
    issue_event = ["trigger", "issues"]

    @staticmethod
    def should_ci_running_in_manual() -> bool:
        return get_env(Env.CI_EVENT_TYPE) in CiEventType.manual

    @staticmethod
    def should_ci_running_in_issue_event() -> bool:
        return get_env(Env.CI_EVENT_TYPE) in CiEventType.issue_event
