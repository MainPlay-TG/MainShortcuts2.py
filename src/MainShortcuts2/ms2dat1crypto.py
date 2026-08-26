import os
from .ms2dat1 import MS2Dat1
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from functools import cached_property
PADDING_OAEP = padding.OAEP(
    mgf=padding.MGF1(algorithm=hashes.SHA256()),
    algorithm=hashes.SHA256(),
    label=None
)


class _Base(MS2Dat1):
  @classmethod
  def generate_key(cls):
    """Создать с новым ключом"""
    raise NotImplementedError()


class MS2Dat1WithAESGCM(_Base):
  """MS2Dat v1 с шифрованием AES-GCM"""

  def __init__(self, key: bytes):
    super().__init__()
    self.aes = AESGCM(key)

  @classmethod
  def generate_key(cls, key_size=256):
    key = AESGCM.generate_key(key_size)
    return key, cls(key)

  def decrypt_body(self, data: bytes):
    return self.aes.decrypt(data[:12], data[12:], None)

  def encrypt_body(self, data: bytes):
    nonce = os.urandom(12)
    return nonce + self.aes.encrypt(nonce, data, None)


class MS2Dat1WithFernet(_Base):
  """MS2Dat v1 с шифрованием Fernet"""

  def __init__(self, key: bytes):
    super().__init__()
    self.fernet = Fernet(key)

  @classmethod
  def generate_key(cls):
    key = Fernet.generate_key()
    return key, cls(key)

  def decrypt_body(self, data: bytes):
    return self.fernet.decrypt(data)

  def encrypt_body(self, data: bytes):
    return self.fernet.encrypt(data)


class MS2Dat1WithRSA(_Base):
  """MS2Dat v1 с шифрованием RSA"""

  def __init__(self, key: RSAPrivateKey | RSAPublicKey):
    super().__init__()
    if isinstance(key, RSAPrivateKey):
      self.priv_key = key
      self.pub_key = key.public_key()
    elif isinstance(key, RSAPublicKey):
      self.priv_key = None
      self.pub_key = key
    else:
      raise TypeError(f"A private or public cryptography RSA key is required, not {type(key)}")

  @cached_property
  def _rsa_data_size(self):
    return (self.pub_key.public_numbers().n.bit_length() + 7) // 8

  @classmethod
  def generate_key(cls, key_size=2048):
    key = rsa.generate_private_key(65537, key_size)
    return key, cls(key)

  def decrypt_body(self, data: bytes):
    # Если дан публичный ключ
    if self.priv_key is None:
      raise ValueError("Only the public key is present. Decryption is impossible")
    # Расшифровка ключа AES
    aes_key = self.priv_key.decrypt(data[:self._rsa_data_size], PADDING_OAEP)
    # Извлечение nonce и зашифрованных данных
    nonce = data[self._rsa_data_size:self._rsa_data_size + 12]
    enc_data = data[self._rsa_data_size + 12:]
    # Расшифровка данных
    return AESGCM(aes_key).decrypt(nonce, enc_data, None)

  def encrypt_body(self, data: bytes):
    # Создание одноразового ключа AES
    aes_key = AESGCM.generate_key(256)
    # Шифрование ключа AES
    enc_aes_key = self.pub_key.encrypt(aes_key, PADDING_OAEP)
    # Шифрование данных
    nonce = os.urandom(12)
    enc_data = AESGCM(aes_key).encrypt(nonce, data, None)
    return enc_aes_key + nonce + enc_data


class MS2Dat1WithEd25519(_Base):
  """MS2Dat v1 с подписью Ed25519 **без шифрования**"""

  def __init__(self, key: Ed25519PrivateKey | Ed25519PublicKey):
    super().__init__()
    if isinstance(key, Ed25519PrivateKey):
      self.priv_key = key
      self.pub_key = key.public_key()
    elif isinstance(key, Ed25519PublicKey):
      self.priv_key = None
      self.pub_key = key
    else:
      raise TypeError(f"A private or public cryptography Ed25519 key is required, not {type(key)}")

  @classmethod
  def generate_key(cls):
    key = Ed25519PrivateKey.generate()
    return key, cls(key)

  def decrypt_body(self, data: bytes):
    d = data[:-64]
    self.pub_key.verify(data[-64:], d)
    return d

  def encrypt_body(self, data: bytes):
    # Если дан публичный ключ
    if self.priv_key is None:
      raise ValueError("Only the public key is present. Verify is impossible")
    return data + self.priv_key.sign(data)
