"""
Encryption utilities for sensitive data like API keys.
"""
import base64
import logging
import os
from typing import Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.core.config import settings

logger = logging.getLogger(__name__)


class EncryptionService:
    """Service for encrypting and decrypting sensitive data."""
    
    _instance: Optional["EncryptionService"] = None
    _fernet: Optional[Fernet] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EncryptionService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self) -> None:
        """Initialize encryption service with key from settings."""
        encryption_key = settings.ENCRYPTION_KEY
        
        if not encryption_key:
            logger.warning(
                "ENCRYPTION_KEY not set. Using a temporary key for development. "
                "Set ENCRYPTION_KEY environment variable for production."
            )
            # Generate a temporary key for development
            encryption_key = Fernet.generate_key()
        
        try:
            # Ensure the key is properly formatted for Fernet
            if isinstance(encryption_key, str):
                encryption_key = encryption_key.encode()
            
            # Fernet requires a 32-byte URL-safe base64-encoded key
            # If the key is not in the right format, derive a proper key
            if len(encryption_key) != 32:
                # Derive a 32-byte key using PBKDF2
                salt = b"supabase_chatbot_salt"  # Should be unique per application
                kdf = PBKDF2HMAC(
                    algorithm=hashes.SHA256(),
                    length=32,
                    salt=salt,
                    iterations=100000,
                    backend=default_backend()
                )
                encryption_key = base64.urlsafe_b64encode(kdf.derive(encryption_key))
            else:
                # Already 32 bytes, encode to URL-safe base64
                encryption_key = base64.urlsafe_b64encode(encryption_key)
            
            self._fernet = Fernet(encryption_key)
            logger.info("Encryption service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize encryption service: {e}")
            raise
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a plaintext string.
        
        Args:
            plaintext: The string to encrypt.
            
        Returns:
            Encrypted string (base64 encoded).
            
        Raises:
            ValueError: If encryption service is not initialized.
        """
        if not self._fernet:
            raise ValueError("Encryption service not initialized")
        
        try:
            encrypted_bytes = self._fernet.encrypt(plaintext.encode())
            return encrypted_bytes.decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt(self, encrypted_text: str) -> str:
        """
        Decrypt an encrypted string.
        
        Args:
            encrypted_text: The encrypted string (base64 encoded).
            
        Returns:
            Decrypted plaintext string.
            
        Raises:
            ValueError: If encryption service is not initialized.
        """
        if not self._fernet:
            raise ValueError("Encryption service not initialized")
        
        try:
            decrypted_bytes = self._fernet.decrypt(encrypted_text.encode())
            return decrypted_bytes.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise
    
    def encrypt_api_key(self, api_key: str, provider: str) -> dict:
        """
        Encrypt an API key and return metadata.
        
        Args:
            api_key: The API key to encrypt.
            provider: The provider name (e.g., 'openai', 'anthropic').
            
        Returns:
            Dictionary with encrypted key and metadata.
        """
        encrypted_key = self.encrypt(api_key)
        
        return {
            "encrypted_key": encrypted_key,
            "provider": provider,
            "key_length": len(api_key),
            "masked_key": self._mask_api_key(api_key),
        }
    
    def decrypt_api_key(self, encrypted_key: str) -> str:
        """
        Decrypt an encrypted API key.
        
        Args:
            encrypted_key: The encrypted API key.
            
        Returns:
            Decrypted API key.
        """
        return self.decrypt(encrypted_key)
    
    def _mask_api_key(self, api_key: str) -> str:
        """
        Mask an API key for display purposes.
        
        Args:
            api_key: The API key to mask.
            
        Returns:
            Masked API key (e.g., 'sk-...abcd').
        """
        if len(api_key) <= 8:
            return "***"
        
        # Show first 4 chars and last 4 chars
        prefix = api_key[:4]
        suffix = api_key[-4:]
        return f"{prefix}...{suffix}"


# Global instance
encryption_service = EncryptionService()