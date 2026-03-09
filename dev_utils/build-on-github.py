if __name__ != "__main__":
  raise RuntimeError("This script must not be imported")
import logging
import os
import subprocess
from changelog_formatter import dump_json, prepare_changelog
from create_hash import create_hash
from gh_api import GitHubClient
from pathlib import Path
from pep8_formatter import format_code
from poetry.factory import Factory as PoetryFactory
from sys import exit
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler())
for i in log.handlers:
  i.setLevel(log.level)
# Проверка GitHub Actions
if os.environ.get("GITHUB_ACTIONS") != "true":
  log.fatal("Allowed only on GitHub Actions")
  exit(1)
# Окружение
PROJ_DIR = Path(__file__).parent.parent
PYPI_TOKEN = os.environ.get("POETRY_PYPI_TOKEN_PYPI")
if not PYPI_TOKEN:
  log.fatal("POETRY_PYPI_TOKEN_PYPI is empty")
  exit(1)
os.chdir(PROJ_DIR)
log.info("Project dir: %s", PROJ_DIR)
# Папки
PROJ_CHANGELOG = PROJ_DIR / "changelog"
PROJ_DIST = PROJ_DIR / "dist"
PROJ_TOML = PROJ_DIR / "pyproject.toml"
if not PROJ_CHANGELOG.is_dir():
  log.fatal("Changelog not found")
  exit(1)
if not PROJ_TOML.is_file():
  log.fatal("pyproject.toml not found")
  exit(1)
# GitHub
gh = GitHubClient.from_env()
log.info("GitHub repo: %s", gh.repo)
# Poetry
poetry = PoetryFactory().create_poetry(PROJ_DIR)
proj_name = str(poetry.package.name)
proj_version = str(poetry.package.version)
log.info("Project: %s %s", proj_name, proj_version)
# Changelog
log.info("Formatting changelog...")
chlogs = prepare_changelog(PROJ_CHANGELOG, proj_name)
if log.isEnabledFor(logging.DEBUG):
  log.debug("Found %s changelogs: %s", len(chlogs), ", ".join(sorted(chlogs, key=lambda i: chlogs[i].version_id)))
if not proj_version in chlogs:
  log.fatal("Changelog %s not found", proj_version)
  exit(1)
# PEP 8
log.info("Formatting code...")
format_code(PROJ_DIR)
# Build
file_prefix = f"{proj_name}-{proj_version}"
sdist = PROJ_DIST / f"{file_prefix}.tar.gz"
if sdist.is_file():
  log.fatal("File %s already exists", sdist.name)
  exit()
log.info("Building...")
subprocess.run(["poetry", "build"], check=True)
if not sdist.is_file():
  log.fatal("File %s not found", sdist.name)
  exit(1)
wheels: set[Path] = set()
for file in PROJ_DIST.iterdir():
  if file.stem.startswith(file_prefix) and (file.suffix == ".whl") and file.is_file():
    log.debug("Found wheel %s", file.name)
    wheels.add(file)
log.info("Found sdist and %s wheels", len(wheels))
# Commit
gh.git.commit_all(proj_version, log)
# Release
log.info("Preparing files for release...")
chlog = chlogs[proj_version]
rel_assets = {i.name: i for i in wheels}
rel_assets["changelog.json"] = dump_json(chlog).encode("utf-8")
rel_assets[f"{proj_name}.tar.gz"] = sdist
rel_assets["sha256sums.txt"] = create_hash("sha256", rel_assets).encode("utf-8")
log.info("Uploading release...")
release = gh.create_release(
    tag_name=f"v{proj_version}",
    name=f"{proj_name} {proj_version}",
    body=chlog.to_md(proj_name),
    files=rel_assets,
)
log.info("Release: %s", release.html_url)
# PyPi
log.info("Uploading to PyPi...")
subprocess.run(["poetry", "publish"], check=True)
# Complete
log.info("\nAll tasks are completed!")
