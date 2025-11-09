class ErrorMessage:
    """自定义异常信息"""

    missing_introduced_version = """Issue描述中找不到引入版本号，请确保Issue描述格式正确且包含“发现版本号”等版本号关键字。补全必要信息后请再次关闭Issue重新触发归档流程。
    """

    too_many_introduced_version = """Issue描述中匹配到多个引入版本号，请确保Issue描述格式正确且只包含一个版本号。补全必要信息后请再次关闭Issue重新触发归档流程。
    匹配到的版本号有：{versions}
    """

    missing_archive_version = """Issue评论中找不到归档版本号关键字，请确保Issue评论中归档关键字格式正确且包含归档版本号。补全必要信息后请再次关闭Issue重新触发归档流程。
    归档关键字格式有：{keywords}
    """

    too_many_archive_version = """Issue评论中匹配到多个版本号关键字，请确保Issue评论中归档关键字格式正确且只包含一个格式的归档关键字。补全必要信息后请再次关闭Issue重新触发归档流程。
    匹配到的版本号有：{versions}
    """

    too_many_issue_type = """Issue标签中匹配到多个Issue类型标签，请确保Issue标签中只包含一个格式的Issue类型标签。请移除多余的Issue类型标签后再次关闭Issue重新触发归档流程。
    匹配到的Issue类型标签有：{labels}
    """

    missing_archive_labels = """Issue标签中找不到归档所需标签，请给Issue打上归档所需标签。补全必要信息后请再次关闭Issue重新触发归档流程。
    归档所需标签有：{labels}
    """

    missing_issue_type_from_title = """Issue标题中找不到Issue关键字，请根据标准Issue格式在标题中补上Issue类型信息。补全必要信息后请再次关闭Issue重新触发归档流程。
    可匹配的Issue类型关键字有：{issue_type}
    """

    missing_issue_type_from_label = """Issue标签中找不到Issue类型标签，请给Issue打上Issue类型标签。补全必要信息后请再次关闭Issue重新触发归档流程。
    可匹配的Issue类型标签有：{issue_type}
    """
    missing_labels_and_archive_version = """手动归档流水线试图归档此Issue，但并未手动填写归档版本号且未在Issue信息中获取到有效的归档版本号和归档所需标签，请重新执行手动归档流水线并输入归档版本号且为此Issue打上Issue归档所需标签。
    """

    unknown_action_name = """未知的action类型：{action_name}，无法找到与之对应的issue仓库类型
    """

    archiving_failed = """处理流程发生异常，归档失败，错误信息：{exc}
    """

    reopen_issue_failed = """Reopen Issue失败，错误信息：{exc}。
    """

    send_comment_failed = """发送告警评论失败，错误信息：{exc}。
    """

    load_issue_info_failed = """读取 {issue_output_path} 失败，无法回溯Issue状态和记录失败内容，请检查相关代码，错误信息：{exc}"""

    aggregation_error = """抛出聚合错误："""

    push_document_failed = """提交归档文档失败，错误信息：{exc}"""


class ArchiveBaseError(Exception):
    "归档错误的基类"


class ArchiveVersionError(ArchiveBaseError):
    """issue评论中找不到归档关键字，缺少归档版本号等"""

    pass


class IntroducedVersionError(ArchiveBaseError):
    """issue描述中缺少声明引入版本号的格式文本，缺少引入版本号等"""

    pass


class ArchiveLabelError(ArchiveBaseError):
    """缺少关键的归档标签等"""

    pass


class IssueTypeError(ArchiveBaseError):
    """issue标题中缺少issue类型声明关键字等"""


class InBlackList(ArchiveBaseError):
    """匹配到无法继续执行归档任务的黑名单内容"""

    pass


class MissingArchiveVersionAndArchiveLabel(ArchiveBaseError):
    """Issue Archive Version和关键的归档标签都缺失"""

    pass


class WebhookPayloadError(Exception):
    """webhook payload为空"""

    pass


class IssueInfoMissing(Exception):
    """找不到IssueInfo文件"""


class MissingIssueNumber(Exception):
    """Issue Number为空"""

    pass


class UnexpectedPlatform(Exception):
    """未识别的流水线环境"""

    pass
