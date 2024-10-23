import os, base64

from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from app.config import settings


base64_key = settings.ENCRYPTION_KEY
encryption_key = base64.b64decode(base64_key)


def encrypt_stream_url(url: str, key: bytes = encryption_key) -> str:
    """
    Шифрование пути к потоку камеры при её создании / редактировании
    """
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(url.encode()) + padder.finalize()
    encrypted_url = encryptor.update(padded_data) + encryptor.finalize()
    
    encrypted_stream_url = base64.b64encode(iv + encrypted_url).decode('utf-8')
    return encrypted_stream_url


def decrypt_stream_url(encrypted_stream_url: str, key: bytes = encryption_key) -> str:
    """
    Дешифрование пути к потоку камеры при её запросе пользователем  
    """
    encrypted_data = base64.b64decode(encrypted_stream_url)
    
    iv = encrypted_data[:16]
    encrypted_url = encrypted_data[16:]
    
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted_padded_url = decryptor.update(encrypted_url) + decryptor.finalize()
    
    unpadder = padding.PKCS7(128).unpadder()
    decrypted_url = unpadder.update(decrypted_padded_url) + unpadder.finalize()
    
    return decrypted_url.decode()
