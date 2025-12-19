"""
Security utilities for input validation and sanitization
"""
import os
import re
import shlex
from pathlib import Path
from typing import List, Tuple
from cryptography.fernet import Fernet
import logging

logger = logging.getLogger(__name__)

class SecurityManager:
    """Handles security operations including encryption and validation"""
    
    def __init__(self):
        # Generate or load encryption key
        self.key = self._get_or_create_key()
        self.cipher = Fernet(self.key)
    
    def _get_or_create_key(self) -> bytes:
        """Get existing encryption key or create new one"""
        key_file = Path(".encryption_key")
        if key_file.exists():
            return key_file.read_bytes()
        else:
            key = Fernet.generate_key()
            key_file.write_bytes(key)
            key_file.chmod(0o600)  # Read/write for owner only
            return key
    
    def encrypt(self, data: str) -> str:
        """Encrypt sensitive data"""
        try:
            return self.cipher.encrypt(data.encode()).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            return ""
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        try:
            return self.cipher.decrypt(encrypted_data.encode()).decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return ""
    
    @staticmethod
    def validate_file_path(file_path: str, base_dir: str) -> Tuple[bool, str]:
        """
        Validate file path to prevent directory traversal attacks
        Returns: (is_valid, sanitized_path or error_message)
        """
        try:
            # Resolve absolute paths
            base = Path(base_dir).resolve()
            target = (base / file_path).resolve()
            
            # Check if target is within base directory
            if not str(target).startswith(str(base)):
                return False, "Path traversal detected"
            
            return True, str(target)
        except Exception as e:
            logger.error(f"Path validation error: {e}")
            return False, str(e)
    
    @staticmethod
    def sanitize_command(command: str, allowed_commands: List[str]) -> Tuple[bool, str]:
        """
        Sanitize and validate shell commands
        Returns: (is_valid, sanitized_command or error_message)
        """
        try:
            # Parse command safely
            parts = shlex.split(command)
            if not parts:
                return False, "Empty command"
            
            # Check if base command is allowed
            base_cmd = parts[0]
            if base_cmd not in allowed_commands:
                return False, f"Command '{base_cmd}' not allowed"
            
            # Check for dangerous patterns
            dangerous_patterns = [
                r'[;&|`$]',  # Command chaining or substitution
                r'\$\(',     # Command substitution
                r'>\s*/dev', # Writing to devices
                r'rm\s+-rf', # Dangerous rm flags
            ]
            
            for pattern in dangerous_patterns:
                if re.search(pattern, command):
                    return False, f"Dangerous pattern detected: {pattern}"
            
            return True, command
        except Exception as e:
            logger.error(f"Command sanitization error: {e}")
            return False, str(e)
    
    @staticmethod
    def validate_file_size(file_path: str, max_size: int) -> Tuple[bool, str]:
        """
        Validate file size
        Returns: (is_valid, message)
        """
        try:
            size = os.path.getsize(file_path)
            if size > max_size:
                return False, f"File too large: {size} bytes (max: {max_size})"
            return True, "Valid"
        except Exception as e:
            logger.error(f"File size validation error: {e}")
            return False, str(e)
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Remove dangerous characters from filename"""
        # Remove path separators and dangerous characters
        sanitized = re.sub(r'[^\w\s\-\.]', '', filename)
        # Remove leading dots to prevent hidden files
        sanitized = sanitized.lstrip('.')
        return sanitized or "unnamed_file"
    
    @staticmethod
    def validate_api_key(api_key: str) -> bool:
        """Basic API key validation"""
        if not api_key or len(api_key) < 10:
            return False
        # Check for common placeholder values
        placeholders = ['your_key_here', 'xxx', 'test', 'demo']
        return api_key.lower() not in placeholders

# Global security manager instance
security_manager = SecurityManager()

# Made with Bob
