import os
from typing import Any, TypeVar, cast

from shared.log import Log


T1 = TypeVar("T1")
T2 = TypeVar("T2")


def get_env(key: str, type: type[T1] = str, default: T2 = None) -> T1 | T2:
    result = os.getenv(key)
    if result is None or result.strip() == "":
        return default
    result = result.strip()

    # bool 需要特殊处理，因为 bool("false") == True
    if type is bool:
        return cast(T1, result.lower() in ("1", "true", "yes", "y", "on"))

    try:
        return cast(
            T1,
            type(
                result  # type: ignore
            ),
        )  # 实在是不知道怎么写才能符合类型系统要求, 只能先忽略类型系统报错了
    except (TypeError, ValueError) as exc:
        raise ValueError(
            Log.env_value_convert_failed.format(
                key=key, value=result, type=type.__name__
            )
        ) from exc


def must_get_env(key: str, type: type[T1] = str) -> T1:
    result = get_env(key, type, None)
    if result is None:
        raise ValueError(Log.env_not_found_or_empty.format(key=key))
    return result
