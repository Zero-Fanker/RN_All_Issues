from http import HTTPStatus

import httpx

from shared.log import Log
from shared.json_dumps import json_dumps


def http_request(
    headers: dict[str, str],
    url: str,
    method: str,
    params: dict[str, str] = None,
    json_content: dict[str, str] = None,
    retry_times: int = 3,
) -> httpx.Response:
    error = None
    for _ in range(retry_times):
        try:
            response = httpx.request(
                headers=headers,
                method=method,
                url=url,
                params=params,
                json=json_content,
                follow_redirects=True,
            )
            if response.status_code == HTTPStatus.NOT_FOUND:
                print(Log.http_404_not_found)
            response.raise_for_status()
            return response
        except httpx.HTTPStatusError:
            try:
                print(Log.http_status_error
                        .format(
                            reason=json_dumps(
                                response.json(),
                            ),
                        ))
            except Exception:
                pass
            raise
        except Exception as e:
            error = e
    raise error
