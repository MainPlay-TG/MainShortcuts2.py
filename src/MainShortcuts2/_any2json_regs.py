import builtins
from .core import ms
decoders = {}
encoders = {}


def reg_decoder(type: str):
  if builtins.type(type) != str:
    type = type.__module__ + "." + type.__name__

  def deco(func):
    decoders[type] = func
    return func
  return deco


def reg_encoder(type: str):
  if builtins.type(type) != str:
    type = type.__module__ + "." + type.__name__

  def deco(func):
    encoders[type] = func
    return func
  return deco


@reg_decoder(type(None))
def _(obj):
  return None


@reg_decoder(bool)
def _(obj):
  return obj


@reg_decoder(bytes)
def _(obj):
  import base64
  if obj[0] == "base64":
    return base64.b64decode(obj[1].encode("utf-8"))


@reg_decoder(dict)
def _(obj):
  result = {}
  for k, v in obj:
    result[ms.any2json._decode_obj(k)] = ms.any2json._decode_obj(v)
  return result


@reg_decoder(float)
def _(obj):
  return obj


@reg_decoder(int)
def _(obj):
  return obj


@reg_decoder(list)
def _(obj):
  return [ms.any2json._decode_obj(i) for i in obj]


@reg_decoder(str)
def _(obj):
  return obj


@reg_decoder(tuple)
def _(obj):
  return tuple([ms.any2json._decode_obj(i) for i in obj])


@reg_encoder(type(None))
def _(obj):
  if obj is None:
    return 0


@reg_encoder(bool)
def _(obj):
  if isinstance(obj, bool):
    return bool(obj)


@reg_encoder(bytes)
def _(obj):
  if isinstance(obj, bytes):
    from base64 import b64encode
    result = [
        "base64",
        b64encode(obj).decode("utf-8"),
    ]
    return result


@reg_encoder(dict)
def _(obj):
  if isinstance(obj, dict):
    result = []
    for k, v in obj.items():
      result.append([ms.any2json._encode_obj(k), ms.any2json._encode_obj(v)])
    return result


@reg_encoder(float)
def _(obj):
  if isinstance(obj, float):
    return float(obj)


@reg_encoder(int)
def _(obj):
  if isinstance(obj, int):
    return int(obj)


@reg_encoder(list)
def _(obj):
  if isinstance(obj, list):
    return [ms.any2json._encode_obj(i) for i in obj]


@reg_encoder(str)
def _(obj):
  if isinstance(obj, str):
    return str(obj)


@reg_encoder(tuple)
def _(obj):
  if isinstance(obj, tuple):
    return [ms.any2json._encode_obj(i) for i in obj]
