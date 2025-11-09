import json
import sys
from pathlib import Path


class Log:
    json_decode_error = """"{path}" json格式不正确，错误信息：{e}"""
    json_ok = """"{path}" json格式正确"""
    job_done = """所有json文件格式验证通过"""


def get_value_from_args(short_arg: str, long_arg: str) -> str:
    argv = sys.argv
    result = ""
    if long_arg in argv:
        result = argv[argv.index(long_arg) + 1]
    if short_arg in argv != -1:
        result = argv[argv.index(short_arg) + 1]
    return result


def main():
    config_dir_path = Path(
        get_value_from_args(short_arg="-cd", long_arg="--config-dir")
    )
    files = config_dir_path.glob("**/*.json")
    for file in files:
        if file.parent.name == ".vscode":
            continue
        try:
            json.loads((file.read_text(encoding="utf-8")))
            print(Log.json_ok.format(path=file.name))
        except json.JSONDecodeError as e:
            print(Log.json_decode_error.format(path=file.name, e=e))
            raise
    print(Log.job_done)


if __name__ == "__main__":
    main()
