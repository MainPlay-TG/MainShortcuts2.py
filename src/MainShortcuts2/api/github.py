import os
import requests
from .base import BaseClient, ObjectBase
from functools import cached_property
from pathlib import Path
from typing import IO
from urllib.parse import urlparse
__all__ = [
    "Client",
    "Release",
    "ReleaseAsset",
    "UrlInfo",
    "User",
]


class _CatBase:
  _n: str

  def __init__(self, client: "Client"):
    self._c = client

  def _r(self, httpm: str, apim: str, **kw):
    return self._c.request(httpm, self._n + "/" + apim, **kw)


class _ObjBase(ObjectBase):
  client: "Client"

  @classmethod
  def _get(cls, client, data, **kw):
    if data:
      return cls(client, data, **kw)


class _HasUrl(_ObjBase):
  def __init__(self, client: BaseClient, raw: dict, *args, **kwargs):
    super().__init__(client, raw, *args, **kwargs)
    self.url: str = self["url"]

  @cached_property
  def url_info(self):
    return UrlInfo(self.url)


class UrlInfo:
  asset_id: int | None
  release_id: int | None
  release_tag: str | None
  repo: str | None
  username: str | None

  def __init__(self, url: str):
    parsed = urlparse(url)
    path = parsed.path.split("/")
    self.repo = None
    self.username = None
    l = len(path)
    if parsed.hostname == "api.github.com":
      if l > 2 and path[1] in ("repos", "users"):
        self.username = path[2]
        if l > 3 and path[1] == "repos":
          self.repo = path[3]
          if l > 5 and path[4] == "releases":
            if path[5] == "assets" and l > 6 and path[6].isdigit():
              self.asset_id = int(path[6])
            elif path[5].isdigit():
              self.release_id = int(path[5])
    elif parsed.hostname == "github.com":
      if l > 1:
        self.username = path[1]
        if l > 2:
          self.repo = path[2]
          if l > 4 and path[3] == "releases":
            self.release_tag = path[4]
    else:
      raise ValueError("Unknown hostname: %s" % parsed.hostname)

  def get_asset(self, client: "Client"):
    if self.asset_id:
      return client.release_assets.get(self.username, self.repo, self.asset_id)

  def get_release(self, client: "Client"):
    if self.release_id:
      return client.releases.get(self.username, self.repo, self.release_id)
    if self.release_tag:
      return client.releases.get_by_tag_name(self.username, self.repo, self.release_tag)

  def get_user(self, client: "Client"):
    if self.username:
      return client.users.get(self.username)


class User(_HasUrl):
  """A GitHub user."""

  def _init(self):
    self.avatar_url: str = self["avatar_url"]
    self.email: str | None = self["email"]
    self.events_url: str = self["events_url"]
    self.followers_url: str = self["followers_url"]
    self.following_url: str = self["following_url"]
    self.gists_url: str = self["gists_url"]
    self.gravatar_id: str | None = self["gravatar_id"]
    self.html_url: str = self["html_url"]
    self.id: int = self["id"]
    self.login: str = self["login"]
    self.name: str | None = self["name"]
    self.node_id: str = self["node_id"]
    self.organizations_url: str = self["organizations_url"]
    self.received_events_url: str = self["received_events_url"]
    self.repos_url: str = self["repos_url"]
    self.site_admin: bool = self["site_admin"]
    self.starred_at: str | None = self["starred_at"]
    self.starred_url: str = self["starred_url"]
    self.subscriptions_url: str = self["subscriptions_url"]
    self.type: str = self["type"]
    self.user_view_type: str | None = self["user_view_type"]

  def reload(self):
    return self.client.users.get(self.login)


class Release(_HasUrl):
  """A release."""

  def _init(self):
    self.assets_url: str = self["assets_url"]
    self.assets = [ReleaseAsset(self.client, i) for i in self["assets"]]  # type: ignore
    self.author = User(self.client, self["author"])
    self.body_html: str | None = self["body_html"]
    self.body_text: str | None = self["body_text"]
    self.body: str | None = self["body"]
    self.created_at: str = self["created_at"]
    self.discussion_url: str | None = self["discussion_url"]
    self.draft: bool = self["draft"]
    self.html_url: str = self["html_url"]
    self.id: int = self["id"]
    self.immutable: bool = self["immutable"]
    self.mentions_count: int | None = self["mentions_count"]
    self.name: str | None = self["name"]
    self.node_id: str = self["node_id"]
    self.prerelease: bool = self["prerelease"]
    self.published_at: str | None = self["published_at"]
    self.tag_name: str = self["tag_name"]
    self.tarball_url: str | None = self["tarball_url"]
    self.target_commitish: str = self["target_commitish"]
    self.updated_at: str | None = self["updated_at"]
    self.upload_url: str = self["upload_url"]
    self.zipball_url: str | None = self["zipball_url"]

  def delete(self):
    self.client.releases.delete(self.url_info.username, self.url_info.repo, self.id)

  def reload(self):
    return self.client.releases.get(self.url_info.username, self.url_info.repo, self.id)

  def update(self, **data):
    return self.client.releases.update(self.url_info.username, self.url_info.repo, self.id, **data)


class ReleaseAsset(_HasUrl):
  """Data related to a release."""

  def _init(self):
    self.browser_download_url: str = self["browser_download_url"]
    self.content_type: str = self["content_type"]
    self.created_at: str = self["created_at"]
    self.digest: str | None = self["digest"]
    self.download_count: int = self["download_count"]
    self.id: int = self["id"]
    self.label: str | None = self["label"]
    self.name: str = self["name"]
    self.node_id: str = self["node_id"]
    self.size: int = self["size"]
    self.state: str = self["state"]
    self.type: str | None = self["type"]
    self.updated_at: str = self["updated_at"]
    self.uploader = User._get(self.client, self["uploader"])

  def delete(self):
    self.client.release_assets.delete(self.url_info.username, self.url_info.repo, self.id)

  def reload(self):
    return self.client.release_assets.get(self.url_info.username, self.url_info.repo, self.id)

  def update(self, **data):
    return self.client.release_assets.update(self.url_info.username, self.url_info.repo, self.id, **data)


class Client(BaseClient):
  class _ReleaseAssets(_CatBase):
    def _r(self, httpm, owner, repo, asset_id, **kw):
      return self._c.request(httpm, f"repos/{owner}/{repo}/releases/assets/{asset_id}", **kw)

    def delete(self, owner: str, repo: str, asset_id: int):
      """Delete a release asset"""
      self._r("DELETE", owner, repo, asset_id)

    def get(self, owner: str, repo: str, asset_id: int):
      """Get a release asset"""
      return ReleaseAsset(self._c, self._r("GET", owner, repo, asset_id))

    def list(self, owner: str, repo: str, release_id: int, per_page=30, page=1):
      """List release assets"""
      resp: list = self._c.request("GET", f"repos/{owner}/{repo}/releases/{release_id}/assets", params={"per_page": per_page, "page": page})
      return [ReleaseAsset(self._c, i) for i in resp]

    def update(self, owner: str, repo: str, asset_id: int, *,
               label: str = None,
               name: str = None,
               state: str = None,
               ):
      """Update a release asset"""
      data = {}
      if label:
        data["label"] = label
      if name:
        data["name"] = name
      if state:
        data["state"] = state
      if not data:
        return self.get(owner, repo, asset_id)
      return ReleaseAsset(self._c, self._r("PATCH", owner, repo, asset_id, json=data))

    def upload(self, owner: str, repo: str, release_id: int, data: bytes | Path | IO[bytes], name: str = None, label: str = None, **kw):
      """Upload a release asset"""
      kw.setdefault("headers", {})
      if isinstance(data, Path):
        with data.open("rb") as f:
          kw["label"] = label
          kw["name"] = name or data.name
          return self.upload(owner, repo, release_id, f, **kw)
      elif isinstance(data, bytes):
        kw["data"] = data
        kw["headers"]["Content-Length"] = len(data)
      else:
        pos = data.tell()
        data.seek(0, os.SEEK_END)
        kw["headers"]["Content-Length"] = data.tell()
        data.seek(pos)
        kw["data"] = data
        if not name:
          fname = getattr(data, "name", None)
          if fname:
            name = os.path.basename(fname)
      kw.setdefault("params", {})
      if label:
        kw["params"]["label"] = label
      if not name:
        raise ValueError("You must specify the name")
      kw["headers"].setdefault("Content-Type", "application/octet-stream")
      kw["params"]["name"] = name
      resp = self._c.request("POST", f"/repos/{owner}/{repo}/releases/{release_id}/assets", **kw)
      return ReleaseAsset(self._c, resp)

  class _Releases(_CatBase):
    def _r(self, httpm, owner, repo, release_id, **kw):
      return self._c.request(httpm, f"repos/{owner}/{repo}/releases/{release_id}", **kw)

    def create(self, owner: str, repo: str, tag_name: str,
               body: str = None,
               discussion_category_name: str = None,
               draft=False,
               generate_release_notes=False,
               make_latest="true",
               name: str = None,
               prerelease=False,
               target_commitish: str = None,
               **kw):
      kw.setdefault("json", {})
      kw["json"]["draft"] = bool(draft)
      kw["json"]["generate_release_notes"] = bool(generate_release_notes)
      kw["json"]["make_latest"] = make_latest
      kw["json"]["prerelease"] = bool(prerelease)
      kw["json"]["tag_name"] = tag_name
      if body:
        kw["json"]["body"] = body
      if discussion_category_name:
        kw["json"]["discussion_category_name"] = discussion_category_name
      if name:
        kw["json"]["name"] = name
      if target_commitish:
        kw["json"]["target_commitish"] = target_commitish
      resp = self._c.request("POST", f"repos/{owner}/{repo}/releases", **kw)
      return Release(self._c, resp)

    def delete(self, owner: str, repo: str, release_id: int):
      self._r("DELETE", owner, repo, release_id)

    def get(self, owner: str, repo: str, release_id: int):
      return Release(self._c, self._r("GET", owner, repo, release_id))

    def get_by_tag_name(self, owner: str, repo: str, tag_name: str):
      return Release(self._c, self._r("GET", owner, repo, f"tags/{tag_name}"))

    def get_latest(self, owner: str, repo: str):
      return Release(self._c, self._r("GET", owner, repo, "latest"))

    def list(self, owner: str, repo: str, per_page=30, page=1, **kw):
      resp: list = self._c.request("GET", f"repos/{owner}/{repo}/releases", params={"per_page": per_page, "page": page})
      return [Release(self._c, i) for i in resp]

    def update(self, owner: str, repo: str, release_id: int,
               body: str = None,
               discussion_category_name: str = None,
               draft: bool = None,
               make_latest: str = None,
               name: str = None,
               prerelease: bool = None,
               tag_name: str = None,
               target_commitish: str = None,
               **kw):
      kw.setdefault("json", {})
      if body is not None:
        kw["json"]["body"] = body
      if discussion_category_name is not None:
        kw["json"]["discussion_category_name"] = discussion_category_name
      if draft is not None:
        kw["json"]["draft"] = bool(draft)
      if make_latest is not None:
        kw["json"]["make_latest"] = make_latest
      if name is not None:
        kw["json"]["name"] = name
      if prerelease is not None:
        kw["json"]["prerelease"] = bool(prerelease)
      if tag_name is not None:
        kw["json"]["tag_name"] = tag_name
      if target_commitish is not None:
        kw["json"]["target_commitish"] = target_commitish
      if not kw["json"]:
        return self.get(owner, repo, release_id)
      return Release(self._c, self._r("PATCH", owner, repo, release_id, **kw))

  class _Users(_CatBase):
    _n = "users"

    def get(self, username: str):
      return User(self._c, self._r("GET", username))

  def __init__(self, token: str = None, **kw):
    self._init(**kw)
    self._headers["Accept"] = "application/vnd.github+json"
    self._headers["X-GitHub-Api-Version"] = "2022-11-28"
    self._url = "https://api.github.com/{method}"
    self.token = token
    # Категории запросов
    self.release_assets = self._ReleaseAssets(self)
    self.releases = self._Releases(self)
    self.users = self._Users(self)

  @property
  def token(self) -> str | None:
    return self.__dict__.get("token")

  @token.setter
  def token(self, v):
    if v is None:
      self.__dict__.pop("token", None)
      self._headers.pop("Authorization", None)
    elif isinstance(v, str):
      if not v:
        self.token = None
        return
      self.__dict__["token"] = v
      self._headers["Authorization"] = "Bearer " + v
    else:
      raise TypeError("Token must be str")

  @classmethod
  def from_env(cls, allow_no_token=False, **kw):
    """Создать клиент, взяв токен из переменной среды если он не указан аргументом"""
    if kw.get("token"):
      return cls(**kw)  # Токен указан в аргументах
    if allow_no_token:
      return cls(os.environ.get("GITHUB_TOKEN"), **kw)  # Может быть без токена
    return cls(os.environ["GITHUB_TOKEN"], **kw)  # Токен обязателен

  def request(self, httpm, apim, raw=False, **kw) -> dict | list | requests.Response:
    if raw:
      return self._request(httpm, apim, **kw)
    with self._request(httpm, apim, **kw) as resp:
      return resp.json()
