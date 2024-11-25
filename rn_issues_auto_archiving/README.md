# 流水线脚本源代码

- 归档流水线的所有功能代码全在这里

- issue_processor
    - 流水线的第一步处理，大致主要功能如下
        - 判断issue（事件）是否是需要被归档的
        - 判断issue（信息）是否满足归档条件
        - 获取并格式化issue信息输出成json以供下一步处理
        - 若手动触发流水线，则判断issue是否被关闭，没有被关闭则关闭对应issue
        - issue不符合归档条件时（或处理时发生异常），发送告警评论并重新打开issue
- auto_archiving
    - 流水线的第二步，大致功能有：
        - 读取第一步处理的issue信息，并格式化成归档文件的格式将内容写入归档文件
        - 归档内容处理和写入时发生异常，发送告警评论并重新打开issue
- push_document
    - 流水线的第三步，大致功能有：
        - 判断归档文件是否有新内容，如果有则将上一步处理好的归档文件推送到文档仓库


- 由于gitlab ci配置git和ssh过于繁琐，gitlab ci 流水线使用了RESTful API来提交归档文件，所以github和gitlab流水线的推送流程使用了不同的脚本
    - github 流水线使用 [push_document.sh](./push_document.sh) 脚本来提交归档文件
    - gitlab 流水线使用 [push_document.py](./push_document.py) 脚本来提交归档文件
