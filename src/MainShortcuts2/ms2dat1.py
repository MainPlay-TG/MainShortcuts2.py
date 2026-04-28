import datetime
import hashlib
import math
import secrets
import struct
import typing
import uuid
from io import BytesIO
from MainShortcuts2.utils import int_size_unsigned
HASH_NAMES = None, "sha256", "sha3-256", "sha512"
HASH_SIZES = 0, 32, 32, 64
MAGIC_HEAD = b"MS2D"
SPECIAL_TYPES = None, False, True, float("-inf"), float("inf"), float("nan")


def hash_data(hash_type: int, data: bytes):
  """Хеширование данных"""
  if hash_type == 0:
    return b""
  return hashlib.new(HASH_NAMES[hash_type], data).digest()


def compress_data(compress_type: int, data: bytes):
  """Сжатие данных, применяется только если результат меньше исходных данных"""
  if compress_type == 1:
    import zlib
    result = zlib.compress(data)
    if len(result) < len(data):
      return 1, result
  elif compress_type == 2:
    import bz2
    result = bz2.compress(data)
    if len(result) < len(data):
      return 2, result
  elif compress_type == 3:
    import lzma  # СУПЕР сжатие
    result = lzma.compress(data, lzma.FORMAT_ALONE, preset=9 | lzma.PRESET_EXTREME)
    if len(result) < len(data):
      return 3, result
  return 0, data


def decompress_data(compress_type: int, data: bytes):
  if compress_type == 0:
    return data
  if compress_type == 1:
    import zlib
    return zlib.decompress(data)
  if compress_type == 2:
    import bz2
    return bz2.decompress(data)
  if compress_type == 3:
    import lzma
    return lzma.decompress(data)
  raise ValueError("Invalid compress type")


class FileHeader:
  """Подходит для всех версий"""

  def __init__(self, version: int):
    self.version = version

  @classmethod
  def from_file(cls, f: typing.IO[bytes]):
    if f.read(4) != MAGIC_HEAD:
      raise ValueError("Invalid file header")
    return cls(f.read(1)[0])

  def build(self):
    return bytes([*MAGIC_HEAD, self.version])


class UnknownType(typing.NamedTuple):
  typename: str
  body: bytes


class Reader:
  """v1"""

  def __init__(self, ms2dat: "MS2Dat1", f: typing.IO[bytes]):
    self.f = f
    self.ms2dat = ms2dat
    # MAGIC заголовок уже должен быть прочитан и проверен
    # Флаги
    flags = self._read1()
    self.compress_type = flags >> 6  # 0b11000000 0-3
    self.hash_type = flags >> 4 & 0b11  # 0b00110000 0-3
    self.encrypted = flags >> 3 & 1  # 0b00001000 0-1
    bodysize_size = flags & 0b111  # 0b00000111 0-7
    # Пользовательские типы
    self.custom_types: list[str] = []
    for i in range(self._read1()):
      self.custom_types.append(self._read(self._read1()).decode("utf-8"))
    # Размер тела
    self.body_size = int.from_bytes(self._read(bodysize_size), "big")

  def _read(self, n: int):
    buf = self.f.read(n)
    if len(buf) != n:
      raise ValueError(f"Expected {n} bytes, got {len(buf)}")
    return buf

  def _read1(self):
    return self._read(1)[0]

  def read_body(self, allow_unknown=False, verify=True) -> typing.Optional[typing.Any]:
    raw = self._read(self.body_size)
    if self.encrypted:
      raw = self.ms2dat.decrypt_body(raw)
    body = decompress_data(self.compress_type, raw)
    if verify and self.hash_type:
      reald = hash_data(self.hash_type, body)
      saved = self._read(HASH_SIZES[self.hash_type])
      if reald != saved:
        raise ValueError("The file is corrupted")
    with BytesIO(body) as buf:
      # Чтение словаря
      d = []
      for i in range(int.from_bytes(buf.read(3), "big")):
        d.append(self.decode_obj(buf, d, allow_unknown))
      # Чтение тела
      return self.decode_obj(buf, d, allow_unknown)

  def decode_obj(self, buf: typing.IO[bytes], d: list, allow_unknown=False):
    head = buf.read(1)[0]
    typeid = head >> 4
    sizesize = head & 0b1111
    size = int.from_bytes(buf.read(sizesize), "big")
    if typeid == 0:  # Специальный тип
      return SPECIAL_TYPES[size]
    if typeid == 6:  # dict
      result = {}
      for i in range(size):
        k = self.decode_obj(buf, d, allow_unknown)
        result[k] = self.decode_obj(buf, d, allow_unknown)
      return result
    if typeid in (7, 8, 9):  # list, tuple, set
      result = [self.decode_obj(buf, d, allow_unknown) for i in range(size)]
      if typeid == 8:
        return tuple(result)
      if typeid == 9:
        return set(result)
      return result
    if typeid == 12:  # datetime + timezone
      dt: datetime.datetime = self.decode_obj(buf, d)
      td: datetime.timedelta = self.decode_obj(buf, d)
      return dt.replace(tzinfo=datetime.timezone(td))
    if typeid == 14:  # Ссылка на словарь
      return d[size]
    if typeid == 15:  # Пользовательский тип
      ctypename = self.custom_types[buf.read(1)[0]]
      ctype = self.ms2dat.custom_types.get(ctypename)
      cbody = buf.read(size)
      if ctype is None:
        if allow_unknown:
          return UnknownType(ctypename, cbody)
        raise ValueError(f"Unknown custom type: {ctypename}")
      return ctype.decode_obj(self, cbody, d)
    body = buf.read(size)
    if typeid == 1:  # int
      return int.from_bytes(body, "big")
    if typeid == 2:  # int
      return -int.from_bytes(body, "big")
    if typeid == 3:  # float
      return struct.unpack("d", body)[0]
    if typeid == 4:  # bytes
      return body
    if typeid == 5:  # str
      return body.decode("utf-8")
    if typeid == 10:  # datetime
      return datetime.datetime.fromtimestamp(struct.unpack("d", body)[0])
    if typeid == 11:  # timedelta
      return datetime.timedelta(seconds=struct.unpack("d", body)[0])
    if typeid == 13:  # UUID
      return uuid.UUID(bytes=body)
    raise Exception("Эта ошибка никогда не вылезет")


class Writer:
  """v1"""

  def __init__(self, ms2dat: "MS2Dat1", f: typing.IO[bytes], obj):
    self.f = f
    self.ms2dat = ms2dat
    self.obj = obj
    self.obj_dict: list[bytes] = []
    self.used_ctypes: list[CustomType] = []

  def _write(self, data: bytes):
    return self.f.write(data)

  def _write1(self, byte: int):
    return self._write(bytes([byte]))

  def _addget_dict(self, typeid: int, size: int, body: bytes):
    if typeid == 14:
      # Если дана ссылка на словарь, то вернуть ее
      return typeid, size, b""
    # В словаре только уже собранные объекты
    buf = bytes(self._build_obj(typeid, size, body))
    if buf in self.obj_dict:
      # Объект уже есть в словаре
      return 14, self.obj_dict.index(buf), b""
    if len(self.obj_dict) >= 0xffffff:
      # Словарь переполнен
      return typeid, size, body
    # Добавить объект в словарь
    self.obj_dict.append(buf)
    return 14, len(self.obj_dict) - 1, b""

  def _encode_obj(self, data, sort_keys: bool, use_dict: bool) -> tuple[int, int, bytes | bytearray]:
    for m, n in enumerate(SPECIAL_TYPES):
      if m < 3:  # None, bool
        if data is n:
          return 0, m, b""
      else:  # float
        if data == n:
          return 0, m, b""
    if isinstance(data, int):
      typeid = 1
      if data < 0:
        data = -data
        typeid = 2
      size = int_size_unsigned(data)
      return typeid, size, data.to_bytes(size, "big")
    if isinstance(data, float):
      if math.isnan(data):
        return 0, 5, b""
      result = struct.pack("d", data)
      return 3, len(result), result
    if isinstance(data, bytes):
      if use_dict:
        return self._addget_dict(4, len(data), data)
      return 4, len(data), data
    if isinstance(data, str):
      result = data.encode("utf-8")
      if use_dict:
        return self._addget_dict(5, len(result), result)
      return 5, len(result), result
    if isinstance(data, dict):
      items = list(data.items())
      if sort_keys:
        try:
          items.sort()
        except Exception:
          pass
      buf = bytearray()
      for k, v in items:
        buf.extend(self.encode_obj(k, sort_keys, use_dict))
        buf.extend(self.encode_obj(v, sort_keys, use_dict))
      return 6, len(items), buf
    if isinstance(data, (list, tuple, set)) and not isinstance(data, UnknownType):
      typeid = 7
      if isinstance(data, tuple):
        typeid = 8
      elif isinstance(data, set):
        typeid = 9
        if sort_keys:
          try:
            data = sorted(data)
          except Exception:
            pass
      buf = bytearray()
      for v in data:
        buf.extend(self.encode_obj(v, sort_keys, use_dict))
      return typeid, len(data), buf
    if isinstance(data, datetime.datetime):
      if data.tzinfo is None:
        result = struct.pack("d", data.timestamp())
        return 10, len(result), result
      td = data.tzinfo.utcoffset(data)
      if td is None:
        return self._encode_obj(data.replace(tzinfo=None))
      buf = bytearray()
      buf.extend(self.encode_obj(data.replace(tzinfo=None)))
      buf.extend(self.encode_obj(td))
      return 12, len(buf), buf
    if isinstance(data, datetime.timedelta):
      result = struct.pack("d", data.total_seconds())
      return 11, len(result), result
    if isinstance(data, uuid.UUID):
      result = data.bytes
      return 13, len(result), result
    # Пользовательский тип
    if isinstance(data, UnknownType):
      handler = UnknownTypeHandler(self.ms2dat, data.typename)
    else:
      handler = self.ms2dat.find_handler(type(data))
    if handler is None:
      raise Exception(f"Unknown type: {type(data)}")
    if handler in self.used_ctypes:
      ctypeid = self.used_ctypes.index(handler)
    else:
      ctypeid = len(self.used_ctypes)
      self.used_ctypes.append(handler)
    body = handler.encode_obj(data, sort_keys)
    result = 15, len(body), bytes([ctypeid]) + body
    if use_dict and getattr(handler, "allow_dict", False):
      return self._addget_dict(*result)
    return result

  def _build_obj(self, typeid: int, size: int, body: bytes):
    sizesize = int_size_unsigned(size)
    if sizesize > 0b1111:
      raise Exception("Too big size")
    buf = bytearray()
    buf.append((typeid << 4) | sizesize)
    buf.extend(size.to_bytes(sizesize, "big"))
    buf.extend(body)
    return buf

  def encode_obj(self, data, sort_keys=False, use_dict=True):
    typeid, size, body = self._encode_obj(data, sort_keys, use_dict)
    return self._build_obj(typeid, size, body)

  def write_all(self, compress_type=0, encrypted=0, hash_type=1, sort_keys=False, use_dict=True):
    self._write(MAGIC_HEAD)
    self._write1(1)
    # Сохранение объекта
    raw_obj = self.encode_obj(self.obj, sort_keys, use_dict)
    # Тело
    raw_body = bytearray()
    raw_body.extend(len(self.obj_dict).to_bytes(3, "big"))
    for i in self.obj_dict:
      raw_body.extend(i)
    raw_body.extend(raw_obj)
    # Сжатие
    compress_type, body = compress_data(compress_type, raw_body)
    # Шифрование
    encrypted = 1 if encrypted else 0  # Если дадут bool
    if encrypted:
      body = self.ms2dat.encrypt_body(body)
    size = len(body)
    sizesize = int_size_unsigned(size)
    if sizesize > 0b111:
      raise Exception("Too big body")
    # Запись
    # Флаги
    self._write1((compress_type << 6) | (hash_type << 4) | (encrypted << 3) | sizesize)
    # Пользовательские типы
    self._write1(len(self.used_ctypes))
    for i in self.used_ctypes:
      name = i.typename.encode("utf-8")
      self._write1(len(name))
      self._write(name)
    # Тело
    self._write(size.to_bytes(sizesize, "big"))
    self._write(body)
    # Хеш
    self._write(hash_data(hash_type, body))


class CustomType:
  allow_dict: bool
  handled_types: set[type]
  typename: str

  def __init__(self, ms2dat: "MS2Dat1"):
    self.ms2dat = ms2dat

  def __eq__(self, other):
    if isinstance(other, CustomType):
      return (self.ms2dat is other.ms2dat) and (self.typename == other.typename)

  def encode_obj(self, data: object, sort_keys=False) -> bytes:
    raise NotImplementedError()

  def decode_obj(self, reader: Reader, body: bytes, d: list) -> object:
    raise NotImplementedError()


class UnknownTypeHandler(CustomType):
  def __init__(self, ms2dat: "MS2Dat1", typename: str):
    super().__init__(ms2dat)
    self.allow_dict = True
    self.handled_types = set()
    self.typename = typename

  def encode_obj(self, data: UnknownType, sort_keys=False):
    return data.body


class MS2Dat1:
  VERSION = 1
  COMPRESS_NONE = 0
  COMPRESS_ZLIB = 1
  COMPRESS_BZ2 = 2
  COMPRESS_LZMA = 3
  HASH_NONE = 0
  HASH_SHA256 = 1
  HASH_SHA3_256 = 2
  HASH_SHA512 = 3

  def __init__(self):
    self._dump_kw = {}
    self._load_kw = {}
    self.custom_types: dict[str, CustomType] = {}

  def set_allow_unknown(self, value: bool):
    """Разрешить загрузку неизвестных пользовательских типов? Такие объекты будут загружены в виде `UnknownType`"""
    self._load_kw["allow_unknown"] = bool(value)

  def set_compress(self, value: int):
    """Уровень сжатия (см. константы класса)"""
    self._dump_kw["compress_type"] = value

  def set_encrypt(self, value: bool):
    """Включить шифрование? Шифрование должно быть реализовано подклассом"""
    self._dump_kw["encrypted"] = 1 if value else 0

  def set_hash(self, value: int):
    """Алгоритм хеширования (см. константы класса)"""
    self._dump_kw["hash_type"] = value

  def set_sort_keys(self, value: bool):
    """Сортировать ключи `dict` и `set`?"""
    self._dump_kw["sort_keys"] = bool(value)

  def set_use_dict(self, value: bool):
    """Использовать словарь? Словарь уменьшает объём данных при наличии одинаковых объектов"""
    self._dump_kw["use_dict"] = bool(value)

  def set_verify(self, value: bool):
    """Проверять хеш данных (если есть) при загрузке?"""
    self._load_kw["verify"] = bool(value)

  def profile_fast(self):
    """Отключение сжатия, хеширования, сортировки, и словаря для быстрейшей работы"""
    self.set_compress(self.COMPRESS_NONE)
    self.set_hash(self.HASH_NONE)
    self.set_sort_keys(False)
    self.set_use_dict(False)

  def profile_fastest(self):
    """Быстрый профиль + отключение проверки данных"""
    self.profile_fast()
    self.set_verify(False)

  def profile_safe(self):
    """Лучшее хеширование"""
    self.set_hash(self.HASH_SHA512)
    self.set_verify(True)

  def profile_smaller_size(self):
    """Максимальное сжатие, но медленная работа"""
    self.set_compress(self.COMPRESS_LZMA)

  def profile_minimum_size(self):
    """Максимальное сжатие без хеширования и с включенным словарём"""
    self.set_compress(self.COMPRESS_LZMA)
    self.set_hash(self.HASH_NONE)
    self.set_use_dict(True)

  def reg_custom_type(self, obj: CustomType, replace=False):
    """Зарегистрировать пользовательский тип"""
    if (obj.typename in self.custom_types) and not replace:
      raise Exception(f"Type {obj.typename} already registered")
    self.custom_types[obj.typename] = obj

  def reg_custom_type_deco(self, replace=False):
    """Регистрация пользовательского типа в виде декоратора над классом"""
    def deco(cls: type[CustomType]):
      self.reg_custom_type(cls(self), replace)
      return cls
    return deco

  def find_handler(self, cls: type) -> CustomType | None:
    """Найти обработчик для типа данных (только пользовательские типы)"""
    for i in self.custom_types.values():
      if cls in i.handled_types:
        return i

  def decrypt_body(self, data: bytes) -> bytes:
    """Расшифровать тело. Должен быть переопределен для работы"""
    raise NotImplementedError("This class cannot work with encryption")

  def encrypt_body(self, data: bytes) -> bytes:
    """Зашифровать тело. Должен быть переопределен для работы"""
    raise NotImplementedError("This class cannot work with encryption")

  def dump(self, obj, file: typing.BinaryIO, **kw):
    """Сохранить объект в IO"""
    writer = Writer(self, file, obj)
    for k, v in self._dump_kw.items():
      kw.setdefault(k, v)
    writer.write_all(**kw)

  def dumps(self, obj, **kw):
    """Сохранить объект в `bytes`"""
    with BytesIO() as f:
      self.dump(obj, f, **kw)
      return f.getvalue()

  def load(self, file: typing.BinaryIO, *, _h: FileHeader = None, **kw):
    """Загрузить объект из IO"""
    if _h is None:
      _h = FileHeader.from_file(file)
    if _h.version != self.VERSION:
      raise Exception(f"Unsupported version {_h.version}")
    reader = Reader(self, file)
    for k, v in self._load_kw.items():
      kw.setdefault(k, v)
    return reader.read_body(**kw)

  def loads(self, data: bytes, **kw):
    """Загрузить объект из `bytes`"""
    with BytesIO(data) as f:
      return self.load(f, **kw)

  def read_file(self, path, **kw):
    """Загрузить объект из локального файла"""
    with open(path, "rb") as f:
      return self.load(f, **kw)

  def write_file(self, obj, path, **kw):
    """Сохранить объект в локальный файл"""
    with open(path, "wb") as f:
      self.dump(obj, f, **kw)


class MS2Dat1EncryptExample(MS2Dat1):
  """Пример реализации шифрования через XOR. Ненадёжное шифрование!"""

  def __init__(self, key: bytes):
    super().__init__()
    self.encrypt_key = key

  @classmethod
  def create_with_random_key(cls, keysize=32):
    return cls(secrets.token_bytes(keysize))

  def decrypt_body(self, data: bytes):
    """Зашифровать/расшифровать данные, используя XOR-шифрование"""
    key = self.encrypt_key
    lkey = len(key)
    return bytes([b ^ key[i % lkey] for i, b in enumerate(data)])
  encrypt_body = decrypt_body


inst = MS2Dat1()
"""Настройки по умолчанию"""
dump = inst.dump
dumps = inst.dumps
load = inst.load
loads = inst.loads
read_file = inst.read_file
write_file = inst.write_file
