import subprocess
import tomli
from MainShortcuts2 import ms
def run(*args,**kw)->subprocess.Popen:
  kw["args"]=args
  p=subprocess.Popen(**kw)
  p.wait()
  return p
print("Загрузка релиза на GitHub")
with open("pyproject.toml","rb") as f:
  proj=tomli.load(f)
name=proj["tool"]["poetry"]["name"]
version=proj["tool"]["poetry"]["version"]
args=["gh","release","create"]
args.append("v%s"%version)
args+=["-t","%s %s"%(name,version)]
args+=["-F","changelog/%s.md"%version]
for i in ms.dir.list("dist",func=lambda p:p.full_name.lower().startswith("%s-%s"%(name.lower(),version))):
  if i.ext==".gz":
    args.append(i.path+("#%s.tar.gz"%name))
  else:
    args.append(i.path)
run(*args)
