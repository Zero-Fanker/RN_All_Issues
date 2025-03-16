# 流水线脚本源代码目录

- 自动归档的主要的功能被拆分成以下几个部分 :
- `issue_processor.py`
  - 流水线的第一步处理，大致主要功能如下
    - 判断issue（事件）是否是需要被归档的
    - 判断issue（信息）是否满足归档条件
    - 获取并格式化issue信息输出成json以供下一步处理
    - 若手动触发流水线，则判断issue是否被关闭，没有被关闭则关闭对应issue
    - issue不符合归档条件时（或处理时发生异常），发送告警评论并重新打开issue
    - 从已经获取的的issue信息中将内容格式化成归档文件的格式将内容写入归档文件
    - 若上述流程中的归档内容获取和处理时发生异常，发送告警评论并重新打开issue
- `push_document.py`(Github流水线中使用) , `push_document.py`(Gitlab流水线中使用)
  - 流水线的第二步
    - 判断第一步生成的归档文件是否有新内容，如果有则将上一步处理好的归档文件推送到文档仓库
- `archiving_success.py`
  - 流水线的第三步
    - 发送归档成功的issue评论
    

- 由于gitlab ci配置git和ssh过于繁琐，gitlab ci 流水线使用了RESTful API来提交归档文件，所以github和gitlab流水线的推送流程使用了不同的脚本
    - github 流水线使用 [push_document.sh](./push_document.sh) 脚本来提交归档文件
    - gitlab 流水线使用 [push_document.py](./push_document.py) 脚本来提交归档文件


# 开发

## 开发配置

- 环境需求：
    - Python : 3.10 或以上
    - IDE : visual studio code
    - 安装项目依赖的第三方库,例如使用这个命令 `pip install ./develop-requirements.txt`
    - 一个符合脚本运行所需的`.env`文件内容，请参考`example.env`编写`.env`，并将`.env`文件放入`项目根目录`目录下

- 项目开发时已经使用类型注解覆盖了绝大部分变量了,所以可以使用 Pylance Language Server 并启用 `Type Checking` 配置以达到最佳开发体验。

1. 在 VSCode 插件视图搜索并安装 `Python (ms-python.python)` 和 `Pylance (ms-python.vscode-pylance)` 插件。
2. 修改 VSCode 配置
   在 VSCode 设置视图搜索配置项 `Python: Language Server` 并将其值设置为 `Pylance`，搜索配置项 `Python > Analysis: Type Checking Mode` 并将其值设置为 `basic`。

   或者向项目 `.vscode` 文件夹中配置文件添加以下内容：

   ```json title=settings.json
   {
     "python.languageServer": "Pylance",
     "python.analysis.typeCheckingMode": "basic"
   }
   ```

## 测试环境与单元测试
### 本地调试
- 为了方便本地调试，项目引入了`python-dotenv`模块，它提供了读取本地`.env`文件内容并立刻设置为环境变量的能力
- 项目包含了`launch.json`文件，可以快速启动项目进行调试，在VSCode`运行与调试页`面可以选择调试的项目，选择对应启动项后按下`F5`即可启动调试
- vsc项目启动项分别有
    - github issue_processor （gitlab归档流水线第一步，用于整理issue信息和判断issue是否满足归档条件,并将整理好的issue内容格式化成新归档内容写入归档文档）
    - ~~push_document github~~ github侧的“提交归档文件”部分是shell脚本[push_document.sh](src/push_document.sh)完成的，所以无需使用python解释器进行调试
    - push_document gitlab （gitlab测归档流水线第二步，使用gitlab RESTful API 将新归档文档提交到仓库中）
    - archiving_success （流水线的第三步，发送归档成功的issue评论）

### 单元测试
- 请先在vsc中安装单元测试插件[Python Test Explorer for Visual Studio Code](https://marketplace.visualstudio.com/items?itemName=LittleFoxTeam.vscode-python-test-adapter)
- 然后vsc左侧`活动栏`就会出现`测试资源管理器`图标,即可查看和运行此项目的任意单元测试

## 代码提交注意事项：
- 为了防止json配置文件因为某些原因格式写错了导致归档脚本出现异常，所以引入了检查json格式的流水线，提交或者pr之前请务必确保脚本相关的json配置文件格式是正确的
- 本项目编写了单元测试,也配置了单元测试流水线,每次代码提交到远程仓库时都会运行单元测试流水线,请确保新提交的代码覆盖并通过了单元测试