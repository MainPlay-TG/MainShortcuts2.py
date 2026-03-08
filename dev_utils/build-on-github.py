if __name__ != "__main__":
  raise RuntimeError("This script must not be imported")
import logging
import os
import subprocess
from changelog_formatter import prepare_changelog
from gh_api import GitHubClient
from pathlib import Path
from pep8_formatter import format_code
from poetry.factory import Factory as PoetryFactory
from sys import exit
log = logging.Logger(__name__,logging.INFO)
log.setLevel(logging.INFO)
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
log.info("Project: %s %s", poetry.package.name, poetry.package.version)
# Changelog
log.info("Formatting changelog...")
chlogs = prepare_changelog(PROJ_DIR, poetry.package.name)
if not poetry.package.version in chlogs:
  log.fatal("Changelog not found")
  exit(1)
# PEP 8
log.info("Formatting code...")
format_code(PROJ_DIR)
# Build
file_prefix = f"{poetry.package.name}-{poetry.package.version}"
sdist = PROJ_DIST / f"{file_prefix}.tar.gz"
if sdist.is_file():
  log.fatal("File %s already exists", sdist.name)
  exit(1)
log.info("Building")
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
gh.git.commit_all(poetry.package.version, log)
# Release
log.info("Uploading release...")
rel_assets = {i.name: i for i in wheels}
rel_assets[f"{poetry.package.name}.tar.gz"] = sdist
release = gh.create_release(
    tag_name=f"v{poetry.package.version}",
    name=f"{poetry.package.name} {poetry.package.version}",
    body=chlogs[poetry.package.version].to_md(poetry.package.name),
    files=rel_assets,
)
log.info("Release: %s", release.html_url)
# PyPi
log.info("Uploading to PyPi...")
subprocess.run(["poetry", "publish"], check=True)
# Complete
log.info("All tasks complete!")
