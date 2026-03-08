from MainShortcuts2 import ms
ver_hist={}
def check_chlog(path:ms.path.Path)->bool:
  try:
    data=ms.json.read(path)
    if "version_id" in data:
      ver_hist[data["version_id"]]=data
      return True
  except Exception as err:
    print(err)
    return False
data={}
data["added"]=[]
data["changed"]=[]
data["fixed"]=[]
data["removed"]=[]
data["version_id"]=len(ms.dir.list(ms.MAIN_DIR,exts=[".json"],func=check_chlog,type="file"))
if data["version_id"]-1 in ver_hist:
  print("Предыдущая версия: %(version)s (%(version_id)s)"%ver_hist[data["version_id"]-1])
data["version"]=input("Введите название версии > ").strip()
print('Запись файла "%(version)s.json" с ID версии %(version_id)i'%data)
ms.json.write(ms.MAIN_DIR+"/"+data["version"]+".json",data,mode="p")
