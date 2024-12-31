class Log():
    '''日志信息'''
    # issue_processor
    env = "环境变量"
    issue_comment = "Issue评论"
    issue_description = "Issue描述"
    introduced_version = "引入版本号"
    archive_version = "归档版本号"
    announcement_comment = "告警评论"
    issue_archived_comment = "归档成功评论"
    issue_title = "Issue标题"
    issue_type = "Issue类型"
    issue_label = "Issue标签"
    dispatch_request = "工作流调度请求"
    uninitialized_message = "未初始化的信息"
    unknown = "Unknown"

    getting_something = '''获取 {something} 中'''
    getting_something_from = '''正在从 {another} 中获取 {something}'''
    parse_something = '''处理 {something} 中'''
    loading_something = '''加载 {something} 中'''
    config_path_not_found = '''未在命令行参数中获取到配置文件路径 , 请正确使用"-c"或"--config"参数传入配置文件路径'''
    parse_config_failed = '''读取配置相关内容时发生错误 , 错误信息  :  {exc}'''
    getting_issue_info = '''正在请求并获取Issue相关信息'''
    non_platform_action_env = '''未检测到流水线环境 , 将读取".env"文件'''
    get_test_platform_type = '''从命令行参数中读取到测试平台类型 , 将执行 {test_platform_type} 平台流程'''
    sending_something = '''正在发送 {something}'''
    archiving_condition_not_satisfied = '''归档条件不满足 , 无法继续进行归档流程'''
    reopen_issue = '''正在重新打开Issue#{issue_number}'''
    close_issue = '''正在关闭Issue#{issue_number}'''
    archive_version_not_found = '''未在 评论 中找到 归档关键字/归档版本号'''
    introduced_version_not_found = '''未在 Issue描述 中找到 引入版本号'''
    target_labels_not_found = '''未在 Issue 中找到 归档所需标签'''
    too_many_introduced_version = '''匹配到多个引入版本号'''
    too_many_archive_version = '''匹配到多个 归档关键字/归档版本号'''
    too_many_issue_type = '''匹配到多个Issue类型标签 : {labels}'''
    issue_type_not_found = '''未在 Issue标题 中找到 Issue类型关键字'''
    not_archive_issue = '''未满足归档Issue条件 , 不对此Issue进行归档处理'''
    print_input_variables = '''打印输入信息  :  {input_variables}'''
    print_issue_json = '''打印issue_json内容  :  
    {issue_json}'''
    issue_state_is_open = '''Issue状态为“Open” , 此issue不是归档对象'''
    issue_state_is_update = '''Issue状态为“update” , 此issue不是归档对象'''
    webhook_payload_not_found = '''webhook payload为空 , 无法进行后续操作'''
    save_issue_content_to_file = '''正在将Issue内容写入至 {issue_output_path} '''
    unexpected_platform_type = '''未知的Issue平台类型 "{platform_type}" , 请检查命令行参数输入和环境变量'''
    issue_already_archived = '''{issue_repository}#{issue_id} 已存在归档记录 , 无需再次归档 , 跳过归档流程'''
    issue_output_not_found = '''未找到格式化的issue信息文件 , 跳过归档写入流程'''
    missing_issue_number = '''"{issues_number_var}"变量为空 , 必须填写"{issues_number_var}"才能执行归档流程'''
    invalid_issue_number = '''"{issues_number_var}"的值不能转换成整数 , 请检查输入参数是否正确'''
    running_ci_by_manual = '''流水线触发触发方式 : 手动'''
    running_ci_by_automated = '''流水线触发触发方式 : 自动'''
    http_404_not_found = '''无法请求到对应资源 , 请检查输入的Issue单号是否正确'''
    http_status_error = '''HTTP请求返回状态码错误 , 原因 : {reason}'''
    issue_type_webhook_detected = '''检测到流水线是由Issue类型webhook触发'''
    other_type_webhook_detected = '''检测到流水线是由非Issue类型webhook触发 , 无需执行归档流程'''
    matched_introduced_versions = '''匹配到的多个引入版本号 : {versions}'''
    matched_archive_versions = '''匹配到的多个归档版本号 : {versions}'''
    matched_issue_type = '''匹配到的多个Issue类型标签 : {issue_types}'''
    job_done = '''脚本执行完毕'''
    
    getting_something_success = '''获取 {something} 成功'''
    getting_something_from_success = '''成功从 {another} 中获取 {something}'''
    parse_something_success = '''处理 {something} 完成'''
    loading_something_success = '''加载 {something} 完毕'''
    sending_something_success = '''成功发送 {something}'''
    reopen_issue_success = '''重新打开Issue#{issue_number}成功'''
    close_issue_success = '''关闭Issue#{issue_number}成功'''
    getting_issue_info_success = '''成功获取Issue相关信息'''
    archive_version_found = '''成功匹配评论中的 归档关键字/归档版本号'''
    target_labels_found = '''成功匹配 Issue 中的 归档所需标签'''
    issue_type_found = '''成功在 Issue标题 中找到 Issue类型关键字'''
    save_issue_content_to_file_success = "成功将 Issue内容 写入至 {issue_output_path}"
    
    # auto_archiving
    archive_document_content = '''归档文件内容'''
    non_github_action_env = '''未检测到 github action 环境 , 将读取".env"文件'''
    print_issue_info = '''打印读取到的issue_info  :  {issue_info}'''
    format_issue_content = '''正在格式化Issue内容'''
    write_content_to_document = '''正在将内容写入归档文件'''
    time_used = '''脚本总耗时 : {time} s'''
    reopen_issue_request = '''正在尝试发送reopen Issue请求'''
    read_failed_recording = '''正在读取归档失败记录 : {failed_record_path}'''
    failed_recording = '''正在将Issue内容记录到归档失败记录'''
    create_failed_recording = '''未在 {failed_record_path} 检测到归档失败记录文件 , 即将创建'''
    failed_record_json_broken = '''归档失败记录损坏严重 , 无法读取有效内容 , 即将覆写 {failed_record_path}'''
    unrecognized_issue_id = '''传入了无法识别的issue_id , 值为 {issue_id}'''
    archived_failed_record_found = '''在Issue错误记录中发现已完成归档的Issue : {issue_ids}'''
    remove_failed_record_item = '''正在移除归档失败记录条目 : {record}'''
    failed_record_issue_id_not_found = '''无法归档失败记录条目中找到需要移除的条目 , issue_id为 {issue_id}'''
    issue_id_found_in_archive_record = "发现了issue_id为 {issue_id} 的归档记录"
    issue_id_not_found_in_archive_record = "找不到issue_id为 {issue_id} 的归档记录"
    unexpected_archive_number = '''匹配到无法使用的非整数的归档序号字符串 , 将使用归档序号默认值 {default_number} 进行归档。匹配到移仓归档序号的行内容为 :  {line}'''
    got_archive_number = '''成功匹配到归档序号字符串 , 归档序号为 {archive_number}'''
    enable_replace_mode = '''检测到本次归档流水线是手动触发的 , 启用归档内容替换模式'''
    replace_old_issue_record = '''正在替换 "{issue_repository}#{issue_id}" 旧归档记录'''
    replaced_line_index = '''替换的行号为 {line_index}'''
    add_new_line = '''正在添加新行'''
    job_down = '''归档任务执行完毕'''
    
    format_issue_content_success = '''格式化Issue内容成功'''
    write_content_to_document_success = '''成功将内容写入归档文件'''
    reopen_issue_request_success = '''reopen Issue请求成功'''
    read_failed_recording_success = '''成功读取归档失败记录 : {failed_record_path}'''
    remove_failed_record_item_success = '''成功移除归档失败记录条目 : {record}'''
    issue_archived_success = '''{issue_repository}#{issue_id} 自动归档成功'''

    # push_document
    pushing_document = '''正在提交归档文档'''
    pushing_document_success = '''提交归档文档成功'''
    push_document_failed = '''提交归档文档失败 , 错误信息 : {exc}'''
    issue_state_is_open_skip_push = '''Issue状态为“Open” , 不执行归档文件推送流程'''
    document_not_found = '''未找到归档文档 , 跳过推送流程'''
    issue_output_not_found_skip_push = '''未找到格式化的issue信息文件 , 不执行归档文件推送流程'''
    get_remote_file_sha256 = '''正在获取远程仓库文件 {file_path} 的sha256值'''
    get_remote_file_sha256_success = '''成功获取远程仓库文件 {file_path} 的sha256值 : {sha256}'''
    not_need_to_push_document = '''本地文件 {file_path} 的sha256值与远程仓库文件 {file_path} 的sha256值一致 , 跳过推送流程'''
    need_to_push_document = '''本地文件 {file_path} 的sha256值与远程仓库文件 {file_path} 的sha256值不一致 , 执行推送流程'''
    get_local_file_sha256 = '''正在获取本地文件 {file_path} 的sha256值'''
    get_local_file_sha256_success = '''成功获取本地文件 {file_path} 的sha256值 : {sha256}'''

    # archiving_success
    unknown_platform_type = '''未识别的平台类型 "{platform_type}"'''
    send_comment_failed = '''发送评论失败 , 原因 : {exc}'''