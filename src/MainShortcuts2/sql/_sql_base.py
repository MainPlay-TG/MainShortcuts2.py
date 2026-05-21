import atexit
import random
import typing
import uuid as uuid_module
from functools import cached_property
from threading import Lock
T = typing.TypeVar("T")


def check_type(obj, cls: type[T], allow_None=True):
  """Проверить что объект соответствует типу"""
  if allow_None and obj is None:
    return
  if isinstance(obj, cls):
    return obj
  err_text = "Object %r must be like %r"
  if allow_None:
    err_text += " or None"
  raise ValueError(err_text % (obj, cls))


def _conv_val(value: T) -> T:
  if isinstance(value, memoryview):
    return value.tobytes()
  return value


def _conv_row(row: list[T]):
  return tuple(map(_conv_val, row))


def _gtn(obj: "TABLE_NAME"):
  """Получить имя таблицы из объекта"""
  if isinstance(obj, str):
    return obj
  if isinstance(obj, ObjectBase) or issubclass(obj, ObjectBase):
    return obj._table
  raise TypeError("obj must be str or ObjectBase")


class ObjectBase:
  """Базовый класс для объектов базы данных"""
  _autoinsert: bool
  _table: str

  def __init__(self, db, **index):
    if not index:
      raise ValueError("Index must not be empty")
    self._db: DatabaseBase = db
    self._index = index
    self._write_lock = Lock()
    if self._autoinsert:
      self._insert()
    self._init()

  def _init(self):
    """Функция вызывается после инициализации объекта"""
    pass

  def __repr__(self) -> str:
    cls = type(self)
    kwargs = []
    for k, v in self._index.items():
      kwargs.append(k + "=" + repr(v))
    return "{}.{}(...,{})".format(cls.__module__, cls.__name__, ",".join(kwargs))

  def __delitem__(self, column: str):
    self[column] = None

  def __getitem__(self, column: str):
    if column in self._index:
      return self._index[column]
    return self._get_values([column])[0]

  def __setitem__(self, column: str, value):
    self._set_values({column: value})

  def _insert(self):
    """Вставить объект в базу данных, если его нет"""
    if self._db.select_count(self._table, self._index) == 0:
      self._db.insert(self._table, self._index)

  def _get_values(self, columns: list[str]):
    """Получить несколько значений одним запросом"""
    return self._db.select_one(self._table, columns, self._index)

  def _set_values(self, data: dict):
    """Изменить несколько значений одним запросом"""
    if not data:
      return
    with self._write_lock:
      self._db.update(self._table, data, self._index)
      for i in data:
        if i in self._index:
          self._index = data[i]

  def delete_from_db(self):
    """Полностью удалить объект из базы данных"""
    self._db.delete(self._table, self._index)


TABLE_NAME = str | ObjectBase | type[ObjectBase]
gen_uuid = uuid_module.uuid4
if not typing.TYPE_CHECKING:  # Использовать последнюю версию uuid
  for i in range(10, 4, -1):
    j = f"uuid{i}"
    if callable(getattr(uuid_module, j, None)):
      gen_uuid = getattr(uuid_module, j)


class UuidObjectBase(ObjectBase):
  """Базовый класс для объектов базы данных с UUID"""
  _enable_cache = False

  def __init__(self, db, uuid: bytes):
    super().__init__(db, uuid=uuid)
    if self._enable_cache:
      self._db.cache[self._table][self.uuid_bytes] = self

  @cached_property
  def uuid_bytes(self) -> bytes:
    """Сырой UUID из БД"""
    return self["uuid"]

  @cached_property
  def uuid_str(self):
    """Строковый UUID"""
    return str(self.uuid)

  @cached_property
  def uuid(self):
    """Объект UUID"""
    return uuid_module.UUID(bytes=self.uuid_bytes)

  @classmethod
  def create_new(cls, db: "DatabaseBase", **data):
    """Создать новый объект"""
    data.setdefault("uuid", gen_uuid().bytes)
    db.insert(cls._table, data)
    return cls.get_by_uuid(db, data["uuid"])

  @classmethod
  def get_by_uuid(cls, db: "DatabaseBase", uuid) -> typing.Self:
    """Получить объект по UUID"""
    if isinstance(uuid, bytes):
      pass
    elif isinstance(uuid, str):
      uuid = uuid_module.UUID(uuid).bytes
    elif isinstance(uuid, uuid_module.UUID):
      uuid = uuid.bytes
    else:
      raise TypeError("uuid must be bytes, str or uuid.UUID")
    if uuid in db.cache[cls._table]:
      return db.cache[cls._table][uuid]
    return cls(db, uuid)


if typing.TYPE_CHECKING:
  class CacheDict(typing.Dict[str, typing.Dict[typing.Any, ObjectBase]]):
    """Словарь для кэширования объектов"""
    pass
else:
  class CacheDict(dict):
    def __getitem__(self, key) -> dict:
      if key not in self:
        self[key] = {}
      return super().__getitem__(key)


class DatabaseBase:
  """Базовая база данных"""

  def __init__(self, *, autosave=True, connect_on_init=True, schema: dict[str, dict[str, str]] = None, **kw):
    atexit.register(self.close)
    self._need_update_schema = True
    self._save_lock = Lock()
    self._schema_lock = Lock()
    self.autosave = autosave
    self.cache = CacheDict()
    self.closed = False
    self.conn = None
    self.conn_kw = kw
    self.ConnectionError = ConnectionError
    self.schema = schema
    if connect_on_init:
      self.connect()

  def __enter__(self):
    return self

  def __exit__(self, *a):
    self.close()
  # Обязательно переопределить

  def _connect(self):
    raise NotImplementedError

  def _create_table(self, cur, table: str, columns: dict[str, str]):
    raise NotImplementedError

  def _delete(self, table: str, where: dict):
    raise NotImplementedError

  def _insert(self, table: str, values: dict):
    raise NotImplementedError

  def _select_adv(self, table: str, columns: list[str], where: dict = None, order_by: str = None, limit: int = None, offset: int = None, other: str = None) -> list[tuple]:
    raise NotImplementedError

  def _select(self, table: str, columns: list[str], where: dict = None) -> list[tuple]:
    raise NotImplementedError

  def _update(self, table: str, values: dict, where: dict):
    raise NotImplementedError

  @property
  def connected(self):
    """Активно ли подключение"""
    return self.conn is not None

  def _update_schema(self, schema: dict[str, dict[str, str]]):
    with self.cursor() as cur:
      for table, columns in schema.items():
        self._create_table(cur, table, columns)
    self.save()

  def close(self, save=True):
    """Закрыть базу данных"""
    if self.closed:
      return
    if save:
      self.save()
    self.disconnect()
    self.closed = True

  def cursor(self):
    """Создать курсор"""
    self.connect()
    return self.conn.cursor()

  def disconnect(self):
    """Отключиться от базы данных, если она подключена"""
    if self.connected:
      self.conn.close()
      self.conn = None

  def exec(self, code: str, values: tuple = [], fetch=True, reconnect=True) -> list[tuple]:
    """Выполнить SQL-запрос"""
    if not code.endswith(";"):
      code += ";"
    if not isinstance(values, tuple):
      values = tuple(values)
    try:
      with self.cursor() as cur:
        cur.execute(code, values)
        if fetch:
          return [_conv_row(i) for i in cur.fetchall()]
        if self.autosave:
          self.save()
    except self.ConnectionError:
      self.disconnect()
      if reconnect:
        return self.exec(code, values, fetch, reconnect=False)
      raise

  def exec2(self, code: str, *values, **kw):
    """Удобнее для статичного кол-ва параметров"""
    return self.exec(code, values, **kw)

  def save(self):
    """Сохранить изменения в базе данных"""
    if self.connected:
      with self._save_lock:
        self.conn.commit()

  def select_one(self, table: TABLE_NAME, columns: list[str], where: dict, max_error: bool = True):
    """Выбрать одну строку из таблицы"""
    limit = 2 if max_error else 1
    results = self.select_adv(table, columns, where, limit=limit)
    if len(results) == 0:
      raise KeyError(f"Object not found in table {table}")
    if max_error:
      if len(results) > 1:
        raise OverflowError(f"Too many objects found in table {table}")
    return results[0]
  # Рекомендуеться переопределить для оптимизации

  def select_count(self, table: TABLE_NAME, where: dict):
    """Получить кол-во объектов в таблице"""
    return len(self.select(table, list(where)[0], where))

  def select_random(self, table: TABLE_NAME, columns: list[str], where: dict = None, limit=1, **kw):
    """Выбрать случайные строки из таблицы"""
    sel = self.select_adv(table, columns, where, **kw)
    if limit == 1:
      return [random.choice(sel)]
    return random.choices(sel, k=limit)
  # Обёртки для методов

  def connect(self):
    """Подключиться к базе данных, если она не подключена"""
    if self.closed:
      raise RuntimeError("Database closed")
    if not self.connected:
      self._connect()
      if self._need_update_schema:
        self.update_schema()

  def delete(self, table: TABLE_NAME, where: dict):
    """Удалить строки из таблицы"""
    if not where:
      raise ValueError("Where is empty")
    return self._delete(_gtn(table), where)

  def insert(self, table: TABLE_NAME, values: dict):
    """Вставить новую строку в таблицу"""
    if not values:
      raise ValueError("Values is empty")
    return self._insert(_gtn(table), values)

  def select_adv(self, table: TABLE_NAME, columns: list[str], where: dict = None, order_by: str = None, limit: int = None, offset: int = None, other: str = None):
    """Улучшенный SELECT"""
    return self._select_adv(_gtn(table), columns, where, order_by, limit, offset, other)

  def select(self, table: TABLE_NAME, columns: list[str], where: dict = None):
    """Выбрать строки из таблицы"""
    return self._select(_gtn(table), columns, where)

  def update_schema(self, schema: dict[str, dict[str, str]] = None):
    """Обновить схему базы данных"""
    if schema is None:
      schema = self.schema
    if schema is None:
      return
    with self._schema_lock:
      self._update_schema(schema)
    self._need_update_schema = False

  def update(self, table: TABLE_NAME, values: dict, where: dict):
    """Изменить строки в таблице"""
    return self._update(_gtn(table), values, where)


class SyncDatabaseBase(DatabaseBase):
  if not typing.TYPE_CHECKING:  # Чтобы не менять сигнатуру
    def __init__(self, *args, **kw):
      super().__init__(*args, **kw)
      self._edit_lock = Lock()

    def update(self, table, values, where):
      with self._edit_lock:
        return super().update(table, values, where)
