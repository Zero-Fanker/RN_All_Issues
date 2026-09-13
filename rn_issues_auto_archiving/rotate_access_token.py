from datetime import datetime, timedelta

import httpx

from shared.env import Env
from utils.env import get_env, must_get_env


# 由于这个脚本专为gitlab使用
# 且不属于归档流程范围内
# 所以并没有将这里的log信息放到shared.log里
class Log:
    rotate_token = """正在轮换token"""
    rotate_success = """token轮换成功，过期时间为：{expire_time}"""
    update_repo_variable = '''正在更新仓库变量"{variable_name}"'''
    update_repo_variable_success = """更新仓库变量"{variable_name}"成功"""
    non_platform_action_env = """未检测到流水线环境，将读取".env"文件"""


def create_http_header(token: str) -> dict[str, str]:
    """所需http header结构详见：
    https://docs.gitlab.com/ee/api/rest/index.html#request-payload"""
    return {"Authorization": "Bearer " + token, "Content-Type": "application/json"}


def rotate_token(old_token: str, gitlab_host: str, token_ttl_days: int) -> str:
    """rotate personal token 自身的文档：
    https://docs.gitlab.com/ee/api/personal_access_tokens.html#using-a-request-header-1
    """
    print(Log.rotate_token)
    response = httpx.post(
        headers=create_http_header(old_token),
        url=f"https://{gitlab_host}/api/v4/personal_access_tokens/self/rotate",
        params={
            "expires_at": (datetime.now() + timedelta(days=token_ttl_days)).isoformat()
        },
    )
    response.raise_for_status()
    new_token: str = response.json()["token"]

    print(Log.rotate_success.format(expire_time=response.json()["expires_at"]))

    return new_token


def update_repository_variable(
    new_token: str, gitlab_host: str, project_id: str, target_variable_name: str
) -> None:
    """更新仓库变量的文档：
    https://docs.gitlab.com/ee/api/project_level_variables.html#update-a-variable
    """
    print(Log.update_repo_variable.format(variable_name=target_variable_name))
    response = httpx.put(
        headers=create_http_header(new_token),
        url=f"https://{gitlab_host}/api/v4/projects/{project_id}/variables/{target_variable_name}",
        json={"value": new_token},
    )
    response.raise_for_status()
    print(Log.update_repo_variable_success.format(variable_name=target_variable_name))


def main():
    if not get_env(Env.GITLAB_CI, bool, False):
        print(Log.non_platform_action_env)
        from dotenv import load_dotenv

        load_dotenv()

    old_token = must_get_env(Env.TOKEN)
    gitlab_host = must_get_env(Env.GITLAB_HOST)
    project_id = must_get_env(Env.PROJECT_ID)
    token_ttl_days = must_get_env(Env.TOKEN_TTL_DAYS, int)
    target_variable_name = must_get_env(Env.TARGET_VARIABLE_NAME)

    new_token = rotate_token(old_token, gitlab_host, token_ttl_days)
    update_repository_variable(new_token, gitlab_host, project_id, target_variable_name)


if __name__ == "__main__":
    main()
