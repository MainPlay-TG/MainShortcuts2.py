import subprocess
import tomli
from MainShortcuts2 import ms
exec(ms.import_code)
def run(*args,**kw)->subprocess.Popen:
  kw["args"]=args
  p=subprocess.Popen(**kw)
  p.wait()
  return p
with open("pyproject.toml","rb") as f:
  proj=tomli.load(f)
version=proj["tool"]["poetry"]["version"]
args=["gh","release","create"]
args.append("v%s"%version)
args+=["-t","MainShortcuts %s"%version]
args+=["-F","changelog/%s.md"%version]
for i in ms.dir.list("dist",func=lambda p:p.full_name.lower().startswith("mainshortcuts2-%s"%version)):
  if i.ext==".gz":
    args.append(i.path+"#MainShortcuts2.tar.gz")
  else:
    args.append(i.path)
run(*args)