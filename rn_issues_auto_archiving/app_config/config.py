"""归档流水线的配置。

原配置来源为 ``config/auto_archiving.json``，现改为直接在本文件中定义，
文件底部构造一个全局单例 ``config`` 供各脚本 import 使用。

字段含义见同目录下的 README.md。
"""

from dataclasses import dataclass, field
from typing import TypedDict, TypeAlias

from shared.env import Env
from utils.env import must_get_env

IssueTypeStr: TypeAlias = str


class ProcessingActionJson(TypedDict):
    add_prefix: str
    add_suffix: str
    remove_keyword: list[str]


@dataclass
class MatchRules:
    """一条匹配规则以及展示给人看的提示 :\n
    rules 是实际参与匹配的正则或关键字，
    hint 是归档失败时展示给Issue作者的帮助提示（默认空字符串，为空时不展示）
    """

    rules: str
    hint: str = ""


def join_hints(match_rules_list: list[MatchRules]) -> str:
    """把多条MatchRules里非空的hint拼成多行文本，方便评论里逐行阅读"""
    return "\n".join(
        f"- `{match_rules.hint}`"
        for match_rules in match_rules_list
        if match_rules.hint
    )


@dataclass
class Config:
    @dataclass
    class IssueType:
        type_keyword: dict[str, str]
        need_introduced_version_issue_type: list[str]
        label_map: dict[str, str]

    @dataclass
    class ArchivedDocument:
        rjust_space_width: int
        rjust_character: str
        table_separator: str
        archive_template: str
        fill_issue_url_by_repository_type: list[str]
        issue_title_processing_rules: dict[IssueTypeStr, ProcessingActionJson]

    @dataclass
    class FromEnv:
        # 从env读取，由 load_env_config 在运行时填充
        token: str = str()
        issue_output_path: str = str()
        ci_event_type: str = str()
        archived_document_path: str = str()

    # 以下为归档行为配置
    archive_necessary_labels: list[str]
    archive_version_reges_for_comments: list[MatchRules]
    archive_version_ignore_line_reges_for_comments: list[str]

    skip_archived_reges_for_comments: list[MatchRules]
    version_regex: str
    issue_type: "Config.IssueType"
    introduced_version_reges: list[str]
    archived_document: ArchivedDocument

    # 本脚本发送评论时统一加的前缀，用于识别“这是脚本自己发的评论”
    # 注意! 谨慎修改此值, 因为每个归档脚本报错评论已经会携带"跳过归档流程"关键字
    # 修改此值会导致脚本扫到以往的归档报错评论后真的跳过归档了
    post_comment_prefix: str = "【归档脚本消息】："

    # 构造时先塞一个空的，main 启动后调用 load_env_config 填充真实值
    from_env: FromEnv = field(default_factory=FromEnv)

    def load_env_config(self) -> None:
        """从环境变量读取配置。\n
        需要在 load_dotenv() 之后调用，
        否则本地开发时读不到 .env 里配置的值 \n
        缺失或为空的环境变量会抛出 ValueError
        """
        self.from_env = Config.FromEnv(
            token=must_get_env(Env.TOKEN),
            issue_output_path=must_get_env(Env.ISSUE_OUTPUT_PATH),
            ci_event_type=must_get_env(Env.CI_EVENT_TYPE),
            archived_document_path=must_get_env(Env.ARCHIVED_DOCUMENT_PATH),
        )


version_regex = r"(\d\.\d{2}\.\d{3}[a-zA-Z]?\d{0,2})"

config = Config(
    version_regex=version_regex,
    introduced_version_reges=[
        r"[【\[]发现版本号[】\]][：\:]([^\s\r\n【]+)",
    ],
    issue_type=Config.IssueType(
        type_keyword={
            "#Bug#": "Bug修复",
            "#BUG#": "Bug修复",
            "#bug#": "Bug修复",
            "#Bug修复#": "Bug修复",
            "#BUG修复#": "Bug修复",
            "#bug修复#": "Bug修复",
            "#BUG反馈#": "Bug修复",
            "#修复#": "Bug修复",
            "#建议反馈#": "设定调整",
            "#设定建议#": "设定调整",
            "#建议#": "设定调整",
            "#期望和反馈#": "设定调整",
            "#优化#": "设定调整",
            "#开发#": "设定引入",
            "#研发#": "设定引入",
            "#讨论#": "设定调整",
            "#功能增强#": "设定调整",
            "#功能需求#": "设定调整",
            "#功能性提议#": "设定调整",
            "#调整#": "设定调整",
            "#数据调整#": "设定调整",
            "#AI相关#": "设定调整",
            "#计划研讨#": "设定调整",
            "#工具需求#": "设定调整",
        },
        need_introduced_version_issue_type=[
            "Bug修复",
        ],
        label_map={
            "bug": "Bug修复",
            "enhancement 优化或建议": "设定调整",
            "task 任务": "设定引入",
        },
    ),
    archive_necessary_labels=[
        "resolved 已解决",
    ],
    archive_version_ignore_line_reges_for_comments=[
        r"^> ",
    ],
    # rules 引用了 version_regex，改动 version_regex 时这里的正则同步生效
    # hint 里出现的版本号只是示例，脚本自己发的评论会被跳过，不会误匹配
    archive_version_reges_for_comments=[
        MatchRules(rules=f"{version_regex} *测试通过", hint="0.99.918测试通过"),
        MatchRules(rules=f"测试通过 *{version_regex}", hint="测试通过0.99.918"),
        MatchRules(rules=f"{version_regex} *验证通过", hint="0.99.918验证通过"),
        MatchRules(rules=f"验证通过 *{version_regex}", hint="验证通过0.99.918"),
        # MatchRules(rules=f"{version_regex} *已通过", hint="0.99.918已通过"),
        # MatchRules(rules=f"{version_regex} *通过", hint="0.99.918通过"),
        # MatchRules(rules=f"{version_regex} *测试完成", hint="0.99.918测试完成"),
        # MatchRules(rules=f"{version_regex} *归档", hint="0.99.918归档"),
        # MatchRules(rules=f"^以{version_regex} *归档", hint="以0.99.918归档"),
        # MatchRules(rules=f"^请以{version_regex} *归档", hint="请以0.99.918归档"),
        # MatchRules(rules=f"{version_regex} *自动归档", hint="0.99.918自动归档"),
    ],
    skip_archived_reges_for_comments=[
        MatchRules(rules="跳过归档流程", hint="跳过归档流程"),
        MatchRules(rules="不进行归档流程", hint="不进行归档流程"),
    ],
    archived_document=Config.ArchivedDocument(
        rjust_space_width=60,
        rjust_character=" ",
        table_separator="|",
        # 占位符由 ArchiveDocument.archive_issue 的 format 填充，不能改成 f-string
        archive_template="|{table_id}|({issue_type}){issue_title}{rjust_space}[{issue_repository}#{issue_id}]{issue_url_parents} |{introduced_version}|{archive_version}|",
        fill_issue_url_by_repository_type=[
            "外部Issue",
            "内部Issue",
        ],
        issue_title_processing_rules={
            "Bug修复": {
                "add_prefix": "修复了",
                "add_suffix": "的Bug",
                "remove_keyword": [],
            }
        },
    ),
)
