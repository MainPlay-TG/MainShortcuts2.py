import math
import os
from collections import Counter
from functools import cached_property
from io import BytesIO
from PIL import Image as ImageModule
from PIL import ImageDraw
from PIL.Image import Resampling
from typing import TYPE_CHECKING, Self
COLOR_TYPES = float | tuple[int, ...] | None


def is_image_file(name: str) -> bool:
  ext = os.path.splitext(name)[1].lower()
  return ext in ImageModule.registered_extensions()


try:
  import numpy as np
  # NumPy быстрее

  def _replace_img_color(img: "Image", old_color, new_color):
    arr = np.array(img)
    if img.mode in ("L", "P"):
      mask = (arr == old_color)
    else:
      mask = np.all(arr == np.array(old_color), axis=-1)
    arr[mask] = new_color
    result = Image.from_standard(ImageModule.fromarray(arr))
    assert img.size == result.size
    img._im = result._im
    img._mode = result._mode
except Exception:
  def _replace_img_color(img: "Image", old_color, new_color):
    for coord, color in img.iter_pixels():
      if color == old_color:
        img.putpixel(coord, new_color)


class Image(ImageModule.Image):
  def __getitem__(self, key) -> COLOR_TYPES:
    return self.getpixel(key)

  def __setitem__(self, key, value):
    self.putpixel(key, value)

  def _new(self, im):
    return self.from_standard(super()._new(im))

  @cached_property
  def aspect_ratio(self) -> tuple[int, int]:
    """Соотношение сторон"""
    cd = math.gcd(*self.size)
    return self.width // cd, self.height // cd

  @cached_property
  def aspect_ratio_float(self) -> float:
    """Соотношение сторон (в виде `float`)"""
    return self.width / self.height

  @cached_property
  def converter(self):
    """Конвертер изображения в объекты других библиотек"""
    return Converter(self)

  @cached_property
  def draw(self) -> ImageDraw.ImageDraw:
    """Рисовалка"""
    return ImageDraw.Draw(self)

  @classmethod
  def from_standard(cls, other: ImageModule.Image):
    """Преобразовать стандартный `PIL.Image.Image` в текущий класс"""
    other.load()
    self = cls()
    self._exif = other._exif
    self._im = other.im
    self._mode = other.mode
    self._size = other.size
    self.info = None if other.info is None else other.info.copy()
    self.palette = None if other.palette is None else other.palette.copy()
    self.readonly = other.readonly
    return self

  @classmethod
  def open(cls, fp, mode="r", formats=None):
    """Загрузить из файла или `BytesIO`"""
    other = ImageModule.open(fp, mode, formats)
    return cls.from_standard(other)

  @classmethod
  def new(cls, mode, size, color=0):
    other = ImageModule.new(mode, size, color)
    return cls.from_standard(other)

  def copy(self):
    return self.from_standard(super().copy())

  def to_bytesio(self, format: str, **kw) -> BytesIO:
    """Сохранить в `BytesIO`"""
    f = BytesIO()
    self.save(f, format, **kw)
    f.seek(0)
    return f

  def iter_coords(self):
    """Итерация координат сверху вниз слева направо"""
    for y in range(self.height):
      for x in range(self.width):
        yield x, y

  def iter_pixels(self):
    """Итерация координат и значений пикселей"""
    for coord in self.iter_coords():
      yield coord, self.getpixel(coord)

  def replace_color(self, old_color, new_color):
    """Заменить один цвет на другой"""
    if old_color == new_color:
      return
    if isinstance(old_color, (list, tuple)) and isinstance(new_color, (list, tuple)):
      if len(old_color) != len(new_color):
        raise ValueError("The lengths of the colors are different")
    _replace_img_color(self, old_color, new_color)

  def count_colors(self):
    """Посчитать количество цветов"""
    return Counter(self.getdata())

  def scale(self, scale: float, **kw):
    """Умножить размер изображения"""
    new_size = int(self.width * scale), int(self.height * scale)
    return self.from_standard(self.resize(new_size, **kw))

  def to_dict_matrix(self):
    """Преобразовать в матрицу (словарь)"""
    return {coord: color for coord, color in self.iter_pixels()}

  def to_list_matrix(self):
    """Преобразовать в матрицу (вложенный список)"""
    return [[self.getpixel((x, y)) for x in range(self.width)] for y in range(self.height)]

  def optimize(self, add_methods: list = None):
    """Оптимизировать изображение (если возможно). Возвращает список использованных методов"""
    methods = []
    if add_methods:
      methods.extend(add_methods)
    if self.mode.upper() in ("LA", "PA", "RGBA"):
      # Если есть прозрачность
      n = len(self.mode) - 1
      p = tuple([0] * len(self.mode))

      def clear_invisible_colors(coords, color):
        # И пиксель полностью прозрачный
        if color[n] == 0:
          # Удалить его цвет для лучшего сжатия при сохранении
          return p
      methods.append(clear_invisible_colors)
    if methods:
      for coords, color in self.iter_pixels():
        edited = False
        for method in methods:
          new_color = method(coords, color)
          if new_color is not None:
            color = new_color
            edited = True
        if edited:
          self.putpixel(coords, color)
    return methods
  if TYPE_CHECKING:
    def resize(self, size: tuple[int, int] | list[int] | ImageModule.NumpyArray, resample: int | None = None, box: tuple[float, float, float, float] | None = None, reducing_gap: float | None = None) -> Self:
      return super().resize(size, resample, box, reducing_gap)

    def reduce(self, factor: int | tuple[int, int], box: tuple[int, int, int, int] | None = None) -> Self:
      return super().reduce(factor, box)

    def rotate(self, angle: float, resample: Resampling = Resampling.NEAREST, expand: int | bool = False, center: tuple[float, float] | None = None, translate: tuple[int, int] | None = None, fillcolor: float | tuple[float, ...] | str | None = None) -> Self:
      return super().rotate(angle, resample, expand, center, translate, fillcolor)


class Converter:
  def __init__(self, img: Image):
    self._img = img

  @property
  def img(self):
    if self._img.mode == "RGBA":
      return self._img
    return self._img.convert("RGBA")
  # PySide6

  def to_ps6_icon(self):
    """`PySide6.QtGui.QIcon`"""
    from PySide6.QtGui import QIcon
    return QIcon(self.to_ps6_pixmap())

  def to_ps6_image(self):
    """`PySide6.QtGui.QImage`"""
    from PySide6.QtGui import QImage
    img = self.img
    return QImage(img.tobytes(), img.width, img.height, QImage.Format.Format_RGBA8888)

  def to_ps6_pixmap(self):
    """`PySide6.QtGui.QPixmap`"""
    from PySide6.QtGui import QPixmap
    return QPixmap.fromImage(self.to_ps6_image())
  # PyQt5

  def to_qt5_icon(self):
    """`PyQt5.QtGui.QIcon`"""
    from PyQt5.QtGui import QIcon
    return QIcon(self.to_qt5_pixmap())

  def to_qt5_image(self):
    """`PyQt5.QtGui.QImage`"""
    from PyQt5.QtGui import QImage
    img = self.img
    return QImage(img.tobytes(), img.width, img.height, QImage.Format.Format_RGBA8888)

  def to_qt5_pixmap(self):
    """`PyQt5.QtGui.QPixmap`"""
    from PyQt5.QtGui import QPixmap
    return QPixmap.fromImage(self.to_qt5_image())
  # PyQt6

  def to_qt6_icon(self):
    """`PyQt6.QtGui.QIcon`"""
    from PyQt6.QtGui import QIcon
    return QIcon(self.to_qt6_pixmap())

  def to_qt6_image(self):
    """`PyQt6.QtGui.QImage`"""
    from PyQt6.QtGui import QImage
    img = self.img
    return QImage(img.tobytes(), img.width, img.height, QImage.Format.Format_RGBA8888)

  def to_qt6_pixmap(self):
    """`PyQt6.QtGui.QPixmap`"""
    from PyQt6.QtGui import QPixmap
    return QPixmap.fromImage(self.to_qt6_image())
