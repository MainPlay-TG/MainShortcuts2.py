import configparser
from io import StringIO
from typing import Any
from .core import ms
@ms.utils.generator2list(tuple)
def parse_list(line:str)->list[str]:
  for i in line.split(";"):
    i=i.strip()
    if i:
      yield i
class DesktopFile:
  """Создать файл .desktop"""
  def __init__(self,path:str):
    self.path=ms.path.Path(path)
    self.parser=configparser.ConfigParser(interpolation=None)
  def __getitem__(self,key:str|tuple[str,str]|tuple[str,str,Any]):
    if isinstance(key,str):
      return self.parser[key]
    if len(key)==2:
      return self.parser.get(key[0],key[1])
    if len(key)==3:
      return self.parser.get(key[0],key[1],fallback=key[2])
    raise TypeError("Key must be str or tuple[str,str] or tuple[str,str,Any]")
  def __setitem__(self,key:str|tuple[str,str],value:Any):
    if isinstance(key,str):
      self.parser[key]=value
    elif len(key)==2:
      if not self.parser.has_section(key[0]):
        self.parser.add_section(key[0])
      self.parser.set(key[0],key[1],value)
    else:
      raise TypeError("Key must be str or tuple[str,str]")
  def read(self):
    self.parser.read(self.path.path,"utf-8")
  @classmethod
  def load(cls,path:str):
    self=cls(path)
    self.read()
    return self
  def save(self):
    tmp_path=self.path.path+ms.file.TMP_SUFFIX
    with ms.path.TempFiles(tmp_path) as tmp:
      with open(tmp_path,"w",encoding="utf-8") as f:
        self.parser.write(f)
      ms.file.delete(self.path)
      ms.file.move(tmp_path,self.path)
  def to_string(self):
    with StringIO() as f:
      self.parser.write(f)
      f.seek(0)
      return f.read()
  def save2(self):
    return ms.file.write(self.path,self.to_string())
  @property
  def name(self)->None|str:
    return self["Desktop Entry","Name"]
  @name.setter
  def name(self,v):
    self["Desktop Entry","Name"]=v
  @property
  def exec(self)->None|str:
    return self["Desktop Entry","Exec"]
  @exec.setter
  def exec(self,v):
    self["Desktop Entry","Exec"]=v
  @property
  def icon(self)->None|str:
    return self["Desktop Entry","Icon",None]
  @icon.setter
  def icon(self,v):
    self["Desktop Entry","Icon"]=v
  @property
  def terminal(self)->bool:
    value=self["Desktop Entry","Terminal",False]
    if isinstance(value,bool):
      return value
    return value.lower()=="true"
  @terminal.setter
  def terminal(self,v):
    self["Desktop Entry","Terminal"]="true" if v else "false"
  @property
  def keywords(self):
    return parse_list(self["Desktop Entry","Keywords",""])
  @keywords.setter
  def keywords(self,v):
    if isinstance(v,str):
      self["Desktop Entry","Keywords"]=v
    else:
      self["Desktop Entry","Keywords"]=";".join(v)
  @property
  def actions(self):
    return parse_list(self["Desktop Entry","Actions",""])
  @actions.setter
  def actions(self,v):
    if isinstance(v,str):
      self["Desktop Entry","Actions"]=v
    else:
      self["Desktop Entry","Actions"]=";".join(v)
  @property
  def categories(self):
    return parse_list(self["Desktop Entry","Categories",""])
  @categories.setter
  def categories(self,v):
    if isinstance(v,str):
      self["Desktop Entry","Categories"]=v
    else:
      self["Desktop Entry","Categories"]=";".join(v)
  @property
  def mimetypes(self):
    return parse_list(self["Desktop Entry","MimeType",""])
  @mimetypes.setter
  def mimetypes(self,v):
    if isinstance(v,str):
      self["Desktop Entry","MimeType"]=v
    else:
      self["Desktop Entry","MimeType"]=";".join(v)