import typing
from . import ms2dat1
from io import BytesIO
# Использовать последнюю версию для сохранения
dump = ms2dat1.dump
dumps = ms2dat1.dumps
write_file = ms2dat1.write_file
# Авто определение версии при загрузке


def load(file: typing.BinaryIO, **kw):
  """Загрузить объект из IO"""
  header = ms2dat1.FileHeader.from_file(file)
  if header.version == 1:
    return ms2dat1.load(file, _h=header, **kw)
  raise Exception(f"Unsupported version {header.version}")


def loads(data: bytes, **kw):
  """Загрузить объект из `bytes`"""
  with BytesIO(data) as f:
    return load(f, **kw)


def read_file(path, **kw):
  """Загрузить объект из локального файла"""
  with open(path, "rb") as f:
    return load(f, **kw)
