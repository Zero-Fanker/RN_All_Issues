import json
from typing import Any


def json_dumps(
        obj: Any,
        indent: int = 4
):
    return json.dumps(
        obj=obj,
        indent=indent,
        ensure_ascii=False
    )
