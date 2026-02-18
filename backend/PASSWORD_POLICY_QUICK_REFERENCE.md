# Password Policy Quick Reference

## For Users

### What Makes a Valid Password?

Your password needs:
1. At least 8 characters
2. At least 2 of these 3:
   - Letters (A-Z, a-z)
   - Numbers (0-9)
   - Special characters (!@#$%^&*()_+-=[]{}|;:,.<>?)

### Easy Examples That Work

- `mypassword123` - letters + numbers
- `MyDog2024` - letters + numbers
- `super-secure` - letters + special char (hyphen)
- `Coffee&Code` - letters + special char
- `Hello123!` - all three types

### Common Mistakes

- `test123` - Too short (needs 8+ characters)
- `12345678` - Only numbers (need letters too)
- `password` - Only letters (need numbers or special chars)

## For Developers

### Import and Use

```python
from password_policy import validate_password

# Validate a password
result = validate_password("mypassword123")

if result['valid']:
    print(f"Password is {result['strength']}")
    if result['warnings']:
        print("Warnings:", result['warnings'])
else:
    print("Error:", result['feedback'])
```

### Response Format

```python
{
    'valid': bool,           # True if password meets requirements
    'strength': str,         # 'weak', 'medium', or 'strong'
    'feedback': str,         # User-friendly message
    'warnings': list[str]    # Optional warnings (not blocking)
}
```

## For Admins

### Files

- **Policy Logic**: `/backend/password_policy.py`
- **Auth Integration**: `/backend/auth_manager.py`
- **API Endpoints**: `/backend/server.py`

### API Endpoints

- `GET /api/v1/auth/password-policy` - Get policy info
- `POST /api/v1/auth/change-password` - Change password

### Configuration

No configuration needed - works with sensible defaults:
- 8 character minimum
- 2 of 3 character categories
- No expiration
- No password history

### Common Password List

100+ common passwords trigger warnings (but don't block):
- password, 123456, qwerty, admin, etc.

## Testing

Run tests:
```bash
cd /home/deploy/Production/UC-1-Pro/services/ops-center/backend
python3 password_policy.py
```

## Documentation

- **User Guide**: `/docs/PASSWORD_POLICY.md`
- **Implementation**: `/docs/PASSWORD_POLICY_IMPLEMENTATION_SUMMARY.md`
- **This Guide**: `/backend/PASSWORD_POLICY_QUICK_REFERENCE.md`
