"""Password Policy Module

This module implements a user-friendly password policy with sensible security requirements.

Policy Requirements:
- Minimum 8 characters
- Must contain at least 2 of the following 3 categories:
  * Letters (uppercase OR lowercase)
  * Numbers
  * Special characters
- No maximum length restriction
- No forced expiration
- No password history requirements
- Common password warnings (not blocking)
"""

import re
from typing import Dict, List


# Top 100 most common passwords for warning purposes (not blocking)
COMMON_PASSWORDS = {
    "password", "123456", "password123", "12345678", "qwerty", "123456789",
    "12345", "1234", "111111", "1234567", "dragon", "123123", "baseball",
    "iloveyou", "trustno1", "1234567890", "sunshine", "master", "welcome",
    "shadow", "ashley", "football", "jesus", "michael", "ninja", "mustang",
    "password1", "admin", "administrator", "root", "user", "test", "guest",
    "hello", "welcome1", "passw0rd", "qwerty123", "letmein", "monkey",
    "mypassword", "secret", "abc123", "qwertyuiop", "superman", "asdfghjkl",
    "computer", "maverick", "whatever", "starwars", "summer", "1q2w3e4r",
    "charlie", "soccer", "pokemon", "princess", "maggie", "tigger", "batman",
    "matrix", "freedom", "access", "password12", "pass123", "temp", "default",
    "changeme", "654321", "joshua", "hunter", "flower", "lovely", "bailey",
    "welcome123", "master1", "password1234", "admin123", "test123", "demo",
    "password!", "pass", "pwd", "temp123", "testing", "sample", "example",
    "demo123", "user123", "admin1", "qwerty1", "welcome12", "password01",
    "temp1234", "passw0rd1", "welcome2024", "admin2024", "test2024",
    "password2024", "password2025", "admin2025"
}


def check_password_strength(password: str) -> str:
    """
    Check password strength and return rating.

    Args:
        password: Password to check

    Returns:
        String: "weak", "medium", or "strong"
    """
    score = 0

    # Length scoring
    if len(password) >= 8:
        score += 1
    if len(password) >= 12:
        score += 1
    if len(password) >= 16:
        score += 1

    # Character diversity scoring
    has_lower = bool(re.search(r'[a-z]', password))
    has_upper = bool(re.search(r'[A-Z]', password))
    has_digit = bool(re.search(r'\d', password))
    has_special = bool(re.search(r'[^a-zA-Z0-9]', password))

    # Count character types
    char_types = sum([has_lower, has_upper, has_digit, has_special])

    if char_types >= 2:
        score += 1
    if char_types >= 3:
        score += 1
    if char_types >= 4:
        score += 1

    # Penalize common passwords
    if password.lower() in COMMON_PASSWORDS:
        score = max(0, score - 2)

    # Penalize simple patterns
    if re.match(r'^(.)\1+$', password):  # All same character
        score = 0
    elif re.match(r'^\d+$', password):  # Only digits
        score = max(0, score - 1)
    elif re.match(r'^[a-zA-Z]+$', password):  # Only letters
        score = max(0, score - 1)

    # Determine strength based on score
    if score <= 2:
        return "weak"
    elif score <= 4:
        return "medium"
    else:
        return "strong"


def validate_password(password: str) -> Dict[str, any]:
    """
    Validate password against policy requirements.

    Policy:
    - Minimum 8 characters
    - Must contain at least 2 of these 3 categories:
      * Letters (uppercase OR lowercase)
      * Numbers
      * Special characters

    Args:
        password: Password to validate

    Returns:
        Dictionary with:
        - valid (bool): Whether password meets minimum requirements
        - strength (str): Password strength ("weak", "medium", "strong")
        - feedback (str): User-friendly feedback message
        - warnings (List[str]): Optional warnings (not blocking)
    """
    result = {
        "valid": False,
        "strength": "weak",
        "feedback": "",
        "warnings": []
    }

    # Check minimum length
    if len(password) < 8:
        result["feedback"] = "Password must be at least 8 characters long"
        return result

    # Check character categories
    has_letters = bool(re.search(r'[a-zA-Z]', password))
    has_numbers = bool(re.search(r'\d', password))
    has_special = bool(re.search(r'[^a-zA-Z0-9]', password))

    # Count how many categories are present
    categories_present = sum([has_letters, has_numbers, has_special])

    if categories_present < 2:
        result["feedback"] = "Password should include at least 2 of these: letters, numbers, or special characters"
        return result

    # Password meets minimum requirements
    result["valid"] = True

    # Check password strength
    strength = check_password_strength(password)
    result["strength"] = strength

    # Add warnings for common passwords (not blocking)
    if password.lower() in COMMON_PASSWORDS:
        result["warnings"].append("This password is commonly used and may be easy to guess")

    # Check for simple patterns (not blocking, just warning)
    if re.search(r'(012|123|234|345|456|567|678|789)', password):
        result["warnings"].append("Password contains sequential numbers")

    if re.search(r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)', password.lower()):
        result["warnings"].append("Password contains sequential letters")

    # Generate helpful feedback based on strength
    if strength == "strong":
        result["feedback"] = "Strong password! Your password meets all security requirements"
    elif strength == "medium":
        result["feedback"] = "Good password. Consider making it longer or adding more character types for extra security"
    else:  # weak but valid
        result["feedback"] = "Password is acceptable but could be stronger. Consider:\n  - Using at least 12 characters\n  - Mixing uppercase and lowercase letters\n  - Including both numbers and special characters"

    return result


def get_password_requirements() -> Dict[str, any]:
    """
    Get password policy requirements for display to users.

    Returns:
        Dictionary with policy details
    """
    return {
        "minimum_length": 8,
        "required_categories": 2,
        "categories": [
            "Letters (uppercase or lowercase)",
            "Numbers (0-9)",
            "Special characters (!@#$%^&*()_+-=[]{}|;:,.<>?)"
        ],
        "restrictions": {
            "maximum_length": None,
            "forced_expiration": False,
            "password_history": False
        },
        "examples": {
            "valid": [
                "mypassword123",
                "MyDog2024",
                "super-secure",
                "Hello123!",
                "Coffee&Code"
            ],
            "invalid": [
                "test123",  # Too short
                "12345678",  # Only numbers
                "password",  # Only letters, too common
                "abc",  # Too short
                "qwerty"  # Only letters, too short, too common
            ]
        }
    }


def get_password_examples() -> Dict[str, List[str]]:
    """
    Get examples of valid and invalid passwords.

    Returns:
        Dictionary with "valid" and "invalid" password examples
    """
    return {
        "valid": [
            "mypassword123 - 8+ chars, letters + numbers",
            "MyDog2024 - 8+ chars, letters + numbers",
            "super-secure - 8+ chars, letters + special char",
            "Hello123! - 8+ chars, letters + numbers + special char",
            "Coffee&Code - 8+ chars, letters + special char",
            "SecurePass99 - 8+ chars, mixed case + numbers",
            "my_password_1 - 8+ chars, letters + special char + numbers"
        ],
        "invalid": [
            "test123 - Too short (only 7 characters)",
            "12345678 - Only contains numbers",
            "password - Only contains letters, too common",
            "abc - Too short",
            "qwerty - Only letters, too short, too common",
            "aaaaaaaa - Only letters, repetitive pattern"
        ]
    }


# Example usage and testing
if __name__ == "__main__":
    print("=== Password Policy Testing ===\n")

    test_passwords = [
        "mypassword123",  # Should be valid
        "MyDog2024",  # Should be valid
        "super-secure",  # Should be valid
        "test123",  # Too short
        "12345678",  # Only numbers
        "password",  # Only letters, common
        "Hello123!",  # Strong
        "Coffee&Code",  # Valid
        "password123",  # Common
        "SecurePass99",  # Strong
    ]

    for pwd in test_passwords:
        result = validate_password(pwd)
        print(f"Password: '{pwd}'")
        print(f"  Valid: {result['valid']}")
        print(f"  Strength: {result['strength']}")
        print(f"  Feedback: {result['feedback']}")
        if result['warnings']:
            print(f"  Warnings: {', '.join(result['warnings'])}")
        print()
