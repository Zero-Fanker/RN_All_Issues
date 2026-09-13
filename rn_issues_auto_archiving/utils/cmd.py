import subprocess

from shared.log import Log


class CommandFailed(Exception):
    """命令执行失败"""

    pass


def cmd_run(cmd: list[str]) -> str:
    """执行命令，成功时返回 stdout（已 strip）。\n
    返回码非 0 或命令不存在时抛出 CommandFailed
    """
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
    except FileNotFoundError as exc:
        raise CommandFailed(
            Log.command_failed.format(cmd=" ".join(cmd), code=-1, err_msg=str(exc))
        ) from exc

    if result.returncode != 0:
        raise CommandFailed(
            Log.command_failed.format(
                cmd=" ".join(cmd),
                code=result.returncode,
                err_msg=result.stderr.strip(),
            )
        )

    return result.stdout.strip()
