# import json
# import re
# from typing import TypedDict
# from pathlib import Path
# import datetime

# import json_repair

# from shared.log import Log
# from shared.json_dumps import json_dumps


# DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


# class FailedREcordJson(TypedDict):
#     issue_id: int
#     issue_title: int
#     issue_repository: str
#     '''内容 ： 外部Issue / 内部Issue'''
#     record_time: str
#     reason: str


# class FailedRecord():
#     '''在这个类里的读取的json内容以及函数
#     都（需要）考虑了json内容“不正常”的情况
#     因为无法容忍这个归档失败记录json的内容因为各种原因丢失
#     '''

#     def __init__(self, path: str):
#         self.__raw_path = path
#         print(Log.read_failed_recording
#               .format(failed_record_path=self.__raw_path))
#         self.__path = Path(path)
#         self.__records: list[FailedREcordJson] = []
#         if not self.__path.exists():
#             print(Log.create_failed_recording
#                   .format(failed_record_path=self.__raw_path))
#             self.__path.touch()
#             self.__path.write_text("[]")
#         self.__records = json_repair.repair_json(
#             self.__path.read_text(encoding="utf-8"),
#             ensure_ascii=False,
#             return_objects=True
#         )
#         # 如果json文件烂完了（json_repair都无法修复）
#         # 那么会json_repair.repair_json函数会返回一个空字符串
#         if self.__records == '':
#             print(Log.failed_record_json_broken
#                   .format(failed_record_path=self.__raw_path))
#             self.__records = []

#     def get_all_issue_id(self) -> list[int]:
#         result: list[int] = []
#         for record in self.__records:
#             issue_id: int | str = record['issue_id']
#             result.append(self.__parse_issue_id(issue_id))
#         return result

#     def __parse_issue_id(self, issue_id: int | str) -> int:
#         '''
#         由于不清楚issue_id是否可能因为json损坏的问题而
#         导致类型错乱或者有奇怪的内容混进来了
#         才有了这个在字符串中提取数字的处理方法
#         '''
#         default_id = 0
#         if isinstance(issue_id, int):
#             return issue_id
#         elif isinstance(issue_id, str):
#             if issue_id.isdigit():
#                 issue_id = int(issue_id)
#             else:
#                 digits = re.findall(
#                     r'\d+', issue_id
#                 )
#                 # 由于issue_id可能在修复json时被某些混进来的字符拆开了
#                 # 所以这里只能用字符串拼接的方式
#                 # 尝试把issue_id中能识别的数字提取出来
#                 if len(digits) > 0:
#                     issue_id = int("".join(digits))
#                 else:
#                     print(Log.unrecognized_issue_id)
#                     issue_id = default_id

#         else:
#             print(Log.unrecognized_issue_id)
#             issue_id = default_id
#         return issue_id

#     def remove_record(self, issue_id: int | str) -> None:
#         issue_id = self.__parse_issue_id(issue_id)
#         for record in self.__records:
#             if record['issue_id'] == issue_id:
#                 print(Log.remove_failed_record_item
#                       .format(record=json_dumps(
#                           record,
#                       )))

#                 self.__records.remove(record)

#                 print(Log.remove_failed_record_item_success
#                       .format(record=json_dumps(
#                           record,
#                       )))
#                 return
#         print(Log.failed_record_issue_id_not_found
#               .format(issue_id=issue_id))
#         return None

#     def add_record(self,
#                    issue_id: int,
#                    issue_title: str,
#                    issue_repository: str,
#                    reason: str
#                    ) -> None:
#         record = FailedREcordJson(
#             issue_id=issue_id,
#             issue_title=issue_title,
#             issue_repository=issue_repository,
#             record_time=datetime.datetime.now().strftime(DATETIME_FORMAT),
#             reason=reason
#         )
#         self.__records.append(record)

#     def save(self) -> None:
#         self.__path.write_text(
#             json_dumps(
#                 self.__records,
#             )
#             ,encoding="utf-8"
#         )
