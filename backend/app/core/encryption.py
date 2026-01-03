"""
Encryption utilities for sensitive data like API keys.
Uses Fernet (symmetric encryption) from cryptography library.
"""
from cryptography.fernet import Fernet
import base64
import hashlib
from app.core.config import settings

class EncryptionManager:
    """Manages encryption/decryption of sensitive data."""
    
    def __init__(self, secret_key: str):
        """
        Initialize encryption manager with a secret key.
        Derives a Fernet key from the provided secret.
        """
        # Derive a consistent 32-byte key from the secret using SHA256
        key_bytes = hashlib.sha256(secret_key.encode()).digest()
        # Fernet requires a 32-byte URL-safe base64 encoded key
        fernet_key = base64.urlsafe_b64encode(key_bytes)
        self.cipher = Fernet(fernet_key)
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt plaintext to ciphertext.
        Returns base64-encoded ciphertext suitable for database storage.
        """
        encrypted = self.cipher.encrypt(plaintext.encode())
        return encrypted.decode()
    
    def decrypt(self, ciphertext: str) -> str:
        """
        Decrypt ciphertext back to plaintext.
        Expects base64-encoded ciphertext from database.
        """
        decrypted = self.cipher.decrypt(ciphertext.encode())
        return decrypted.decode()

# Global encryption manager using JWT secret key
encryption_manager = EncryptionManager(settings.JWT_SECRET_KEY)
