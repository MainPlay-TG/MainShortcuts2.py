import os
import requests
import subprocess
from functools import cached_property
from logging import Logger
from pathlib import Path


class Release(dict):
  @property
  def assets_url(self) -> str:
    return self["assets_url"]

  @property
  def html_url(self) -> str:
    return self["html_url"]

  @property
  def id(self) -> int:
    return self["id"]

  @property
  def upload_url(self) -> str:
    url: str = self["upload_url"]
    if "{" in url:
      return url[:url.index("{")]
    return url

  @property
  def url(self) -> str:
    return self["url"]


class GitHubClient:
  def __init__(self, repo: str, token: str):
    self.http = requests.Session()
    self.http.headers["Accept"] = "application/vnd.github+json"
    self.http.headers["Authorization"] = f"Bearer {token}"
    self.http.headers["X-GitHub-Api-Version"] = "2022-11-28"
    self.repo = repo
    self.token = token

  @cached_property
  def git(self):
    return GitClient(self.repo, self.token)

  @classmethod
  def from_env(cls):
    return cls(os.environ["GITHUB_REPOSITORY"], os.environ["GITHUB_TOKEN"])

  def make_request(self, method: str, subpath: str, **kw):
    kw.setdefault("url", f"https://api.github.com/repos/{self.repo}{subpath}")
    kw["method"] = method
    resp = self.http.request(**kw)
    resp.raise_for_status()
    return resp

  def create_release(self, tag_name: str,
                     name: str = None,
                     body: str = None,
                     files: dict[str, Path] = None,
                     draft=False,
                     **kw):
    # Создание релиза
    kw["json"] = {"tag_name": tag_name}
    if name:
      kw["json"]["name"] = name
    if body:
      kw["json"]["body"] = body
    if files:
      for filepath in files.values():
        if not filepath.is_file():
          raise FileNotFoundError(filepath)
      kw["json"]["draft"] = True
    else:
      kw["json"]["draft"] = bool(draft)
    with self.make_request("POST", "/releases", **kw) as resp:
      release = Release(resp.json())
    # Релиз без файлов
    if not files:
      return release
    # Загрузка файлов в релиз
    upload_kw = kw.copy()
    del upload_kw["json"]
    upload_kw["url"] = release.upload_url
    upload_kw.setdefault("params", {})
    upload_kw.setdefault("headers", {})
    upload_kw["headers"]["Content-Type"] = "application/octet-stream"
    upload_kw["subpath"] = ""
    for filename, filepath in files.items():
      with filepath.open("rb") as f:
        upload_kw["data"] = f
        upload_kw["headers"]["Content-Length"] = str(filepath.stat().st_size)
        upload_kw["params"]["name"] = filename
        with self.make_request("POST", **upload_kw) as resp:
          resp.json()
    if draft:
      # Вернуть новый статус релиза
      with self.make_request("GET", f"/releases/{release.id}", **kw) as resp:
        return Release(resp.json())
    else:
      # Опубликовать релиз
      kw["json"] = {"draft": False}
      with self.make_request("PATCH", f"/releases/{release.id}", **kw) as resp:
        return Release(resp.json())


class GitClient:
  def __init__(self, repo: str, token: str):
    self.repo = repo
    self.token = token
    self.run("config", "--global", "user.email", "actions@github.com")
    self.run("config", "--global", "user.name", "github-actions")

  def run(self, *args: str, **kw) -> subprocess.CompletedProcess:
    kw.setdefault("check", True)
    kw.setdefault("env", dict(os.environ))
    kw["args"] = ["git", *args]
    kw["env"]["GITHUB_TOKEN"] = self.token
    return subprocess.run(**kw)

  def commit_all(self, version: str, log: Logger):
    self.run("add", ".")
    if self.run("diff", "--cached", "--exit-code", check=False, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL).returncode == 0:
      return log.info("No changes to commit")
    log.info("Running commit...")
    self.run("commit", "-a", "-m", f"Build {version} [skip ci]")
    log.info("Running push")
    self.run("push")
