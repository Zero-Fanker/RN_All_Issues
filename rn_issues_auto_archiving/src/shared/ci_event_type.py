
class CiEventType():
    '''流水线触发类型 :\n
    github:https://docs.github.com/zh/actions/writing-workflows/choosing-when-your-workflow-runs/events-that-trigger-workflows#about-events-that-trigger-workflows
    gitlab:https://docs.gitlab.com/ee/ci/jobs/job_rules.html#ci_pipeline_source-predefined-variable'''
    manual = ["web", "workflow_dispatch"]
    issue_event = ["trigger", "issues"]