"""
Unit tests for security utilities
"""
import pytest
import os
from pathlib import Path
from utils.security import SecurityManager

@pytest.fixture
def security_manager():
    return SecurityManager()

class TestSecurityManager:
    """Test suite for SecurityManager"""
    
    def test_encryption_decryption(self, security_manager):
        """Test encryption and decryption"""
        original = "sensitive_api_key_12345"
        encrypted = security_manager.encrypt(original)
        decrypted = security_manager.decrypt(encrypted)
        
        assert encrypted != original
        assert decrypted == original
    
    def test_validate_file_path_safe(self):
        """Test valid file path"""
        base_dir = "/home/user/project"
        file_path = "src/main.py"
        
        is_valid, result = SecurityManager.validate_file_path(file_path, base_dir)
        assert is_valid
        assert "src/main.py" in result
    
    def test_validate_file_path_traversal(self):
        """Test path traversal detection"""
        base_dir = "/home/user/project"
        file_path = "../../etc/passwd"
        
        is_valid, result = SecurityManager.validate_file_path(file_path, base_dir)
        assert not is_valid
        assert "traversal" in result.lower()
    
    def test_sanitize_command_allowed(self):
        """Test allowed command"""
        command = "ls -la"
        allowed = ["ls", "pwd", "cat"]
        
        is_valid, result = SecurityManager.sanitize_command(command, allowed)
        assert is_valid
    
    def test_sanitize_command_not_allowed(self):
        """Test disallowed command"""
        command = "rm -rf /"
        allowed = ["ls", "pwd", "cat"]
        
        is_valid, result = SecurityManager.sanitize_command(command, allowed)
        assert not is_valid
    
    def test_sanitize_command_dangerous_pattern(self):
        """Test dangerous command pattern detection"""
        command = "ls; rm -rf /"
        allowed = ["ls", "rm"]
        
        is_valid, result = SecurityManager.sanitize_command(command, allowed)
        assert not is_valid
    
    def test_sanitize_filename(self):
        """Test filename sanitization"""
        dangerous = "../../../etc/passwd"
        safe = SecurityManager.sanitize_filename(dangerous)
        
        assert ".." not in safe
        assert "/" not in safe
    
    def test_validate_api_key_valid(self):
        """Test valid API key"""
        valid_key = "sk-1234567890abcdef"
        assert SecurityManager.validate_api_key(valid_key)
    
    def test_validate_api_key_invalid(self):
        """Test invalid API key"""
        invalid_keys = ["", "short", "your_key_here", "xxx"]
        for key in invalid_keys:
            assert not SecurityManager.validate_api_key(key)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# Made with Bob
