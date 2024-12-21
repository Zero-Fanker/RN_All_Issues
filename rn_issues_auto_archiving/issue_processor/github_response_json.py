from typing import TypedDict

class GithubUserJson(TypedDict):
    avatar_url: str
    events_url: str
    followers_url: str
    following_url: str
    gists_url: str
    gravatar_id: str
    html_url: str
    id: int
    login: str
    node_id: str
    organizations_url: str
    received_events_url: str
    repos_url: str
    site_admin: bool
    starred_url: str
    subscriptions_url: str
    type: str
    url: str

class GithubCommentJson(TypedDict):
    author_association: str
    body: str
    created_at: str
    html_url: str
    id: int
    issue_url: str
    node_id: str
    updated_at: str
    url: str
    user: GithubUserJson
