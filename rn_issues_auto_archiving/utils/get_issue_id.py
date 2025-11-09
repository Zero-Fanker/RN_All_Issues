import os
import json
from pathlib import Path

if __name__ == "__main__":
    payload: dict[str, dict] = json.loads(
        Path(os.environ["WEBHOOK_OUTPUT_PATH"]).read_text()
    )

    if (temp := payload.get("object_attributes")) is not None:
        issue_id = temp.get("iid")
        print(issue_id)
