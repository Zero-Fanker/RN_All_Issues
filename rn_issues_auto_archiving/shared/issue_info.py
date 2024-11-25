from typing import TypedDict
from dataclasses import dataclass


class IssueInfoJson(TypedDict):
    
    class ReopenInfo(TypedDict):
        http_header: dict[str, str]
        reopen_url: str
        reopen_http_method: str
        reopen_body: dict[str, str]
        comment_url: str

    issue_id: int
    issue_type: str
    issue_title: str
    issue_state: str
    '''值只可能为 open 或 closed'''
    introduced_version: str
    archive_version: str
    ci_event_type: str
    reopen_info: ReopenInfo
    
    
    @staticmethod
    def remove_sensitive_info(issue_info:dict) -> dict:
        '''移除issue_info的敏感信息，函数不会修改传入的字典'''
        result = issue_info.copy()
        result.pop("reopen_info")
        return result
        

@dataclass()
class IssueInfo():
    @dataclass()
    class ReopenInfo():
        http_header: dict[str, str]
        reopen_url: str
        reopen_http_method: str
        reopen_body: dict[str, str]
        comment_url: str

    issue_id: int
    issue_type: str
    issue_title: str
    issue_state: str
    '''值只可能为 open 或 closed'''
    introduced_version: str
    archive_version: str
    ci_event_type:str
    reopen_info: ReopenInfo
    
