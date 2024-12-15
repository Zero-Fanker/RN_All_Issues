from shared.json_config import IssueType, ProcessingActionJson
from shared.log import Log


class ArchiveDocument():
    def __init__(self):
        self.__path: str
        self.__lines: list[str] = []
        self.__new_lines: list[str] = []
        self.__reverse_lines: list[str] = []
        self.__lines_set: set[str] = set()

    def file_load(self, path: str):
        print(Log.getting_something_from
              .format(another=path,
                      something=Log.archive_document_content))
        self.__path = path
        with open(path, 'r', encoding="utf-8") as file:
            self.__lines = file.readlines()
            self.__reverse_lines = self.__lines[::-1]
            self.__lines_set = set(self.__lines)
        print(Log.getting_something_from_success
              .format(another=path,
                      something=Log.archive_document_content))

    def show_new_line(self) -> list[str]:
        return self.__new_lines.copy()

    def show_lines(self) -> list[str]:
        return self.__lines.copy()

    def add_new_line(self, line: str) -> None:
        '''不建议直接使用此方法，建议使用archive_issue来格式化issue内容'''
        self.__add_line(line)

    def __add_line(self, line: str) -> None:
        print(Log.add_new_line)
        self.__new_lines.append(line)

    def __replace_line(self, index: int, line: str) -> None:
        print(Log.replaced_line_index
              .format(line_index=index,
                      ))
        self.__lines[index] = line

    def __get_table_last_line_index(self) -> int:
        # 后面的写入到归档文件函数会把归档序号+1，所以这里得0
        line_index = 0
        for index, line in enumerate(self.__reverse_lines, 1):
            if line.strip():
                line_index = index
                break
        return len(self.__lines) - line_index

    @staticmethod
    def __find_table_number_in_line(
        line: str,
        table_separator: str
    ) -> int:
        result = 0
        start = line.find(table_separator)
        end = line.find(table_separator, start+1)
        if (temp := line[start+1:end]).isdigit():
            print(Log.got_archive_number
                  .format(
                      archive_number=temp
                  ))
            result = int(temp)
        else:
            print(Log.unexpected_archive_number
                  .format(
                      default_number=result + 1,
                      line=line
                  ))
        return result

    def __get_last_table_number(
        self,
        table_separator: str
    ) -> int:
        return self.__get_table_number_by_line_index(
            self.__get_table_last_line_index(),
            table_separator
        )

    @staticmethod
    def __parse_issue_title(
        issue_title: str,
        issue_type: str,
        issue_title_processing_rules: dict[
            IssueType,
            ProcessingActionJson
        ]
    ) -> str:
        action_map = issue_title_processing_rules.get(
            issue_type)
        if action_map is None:
            return issue_title
        else:
            result = issue_title
            for keyword in action_map["remove_keyword"]:
                result = result.replace(keyword, '')
            result = ''.join(
                [action_map["add_prefix"],
                 result,
                 action_map["add_suffix"]]
            )
            return result

    def should_issue_record_exists(
        self,
        issue_repository: str,
        issue_id: int,
    ) -> bool:
        sub_string = f'{issue_repository}#{issue_id}]'
        for line in self.__lines_set:
            if sub_string in line:
                print(
                    Log.issue_id_found_in_archive_record
                    .format(issue_id=issue_id)
                )
                return True
        print(
            Log.issue_id_not_found_in_archive_record
            .format(issue_id=issue_id)
        )
        return False

    def __get_table_number_by_line_index(
        self,
        line_index: int,
        table_separator: str
    ) -> int:
        return self.__find_table_number_in_line(
            self.__lines[line_index],
            table_separator
        )

    def __find_line_index_by_issue_id(
            self,
            issue_id: int,
            issue_repository: str
    ) -> int:
        '''O(n)查询速度去根据记录中匹配issue_id的行号
        查不到会返回 -1
        '''
        # 虽然这里是 O(n) 的查询速度
        # 但是我相信归档文件不会有10万行的内容的
        sub_string = f'{issue_repository}#{issue_id}'
        for index, line in enumerate(self.__lines):
            if sub_string in line:
                print(Log.issue_id_found_in_archive_record
                      .format(issue_id=issue_id))
                return index
        print(Log.issue_id_not_found_in_archive_record
              .format(issue_id=issue_id))
        return -1

    def archive_issue(self,
                      rjust_space_width: int,
                      rjust_character: str,
                      table_separator: str,
                      archive_template: str,
                      fill_issue_url_by_repository_type: list[str],
                      issue_title_processing_rules: dict[
                          IssueType,
                          ProcessingActionJson
                      ],
                      issue_id: int,
                      issue_type: str,
                      issue_title: str,
                      issue_repository: str,
                      issue_url: str,
                      introduced_version: str,
                      archive_version: str,
                      replace_mode: bool = False,
                      ) -> None:
        print(Log.format_issue_content)

        if replace_mode:
            print(Log.enable_replace_mode)

        table_id: int = 0
        line_index: int = -1
        if (replace_mode
                and (line_index := self.__find_line_index_by_issue_id(
                    issue_id, issue_repository
                )) != -1):
            print(Log.replace_old_issue_record
                  .format(
                      issue_id=issue_id,
                      issue_repository=issue_repository
                  ))
            table_id = self.__find_table_number_in_line(
                self.__lines[line_index],
                table_separator
            )
        else:
            table_id = self.__get_last_table_number(
                table_separator) + 1

        issue_url_parents = ""
        if issue_repository in fill_issue_url_by_repository_type:
            issue_url_parents = f'({issue_url})'
        else:
            issue_url = ""

        new_content = archive_template.format(
            table_id=table_id,
            issue_type=issue_type,
            issue_title=self.__parse_issue_title(
                issue_title,
                issue_type,
                issue_title_processing_rules
            ),
            rjust_space=((rjust_space_width
                          - len(issue_title))
                         * rjust_character),
            issue_repository=issue_repository,
            issue_id=issue_id,
            issue_url=issue_url,
            issue_url_parents=issue_url_parents,
            introduced_version=introduced_version,
            archive_version=archive_version
        )
        print(Log.format_issue_content_success)

        if "\n" not in new_content:
            new_content += "\n"

        if replace_mode and line_index != -1:
            self.__replace_line(
                line_index,
                new_content
            )
        else:
            self.__add_line(new_content)

    def save(self) -> None:
        print(Log.write_content_to_document)
        if not self.__lines[-1].endswith('\n'):
            self.__lines[-1] += "\n"
        if len(self.__new_lines) != 0:
            self.__lines.insert(
                self.__get_table_last_line_index() + 1,
                *self.__new_lines
            )
        with open(self.__path, 'w', encoding="utf-8") as file:
            file.writelines(self.__lines)
        print(Log.write_content_to_document_success)
