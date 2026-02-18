# Password Policy Documentation

## Overview

The Ops-Center implements a user-friendly password policy that balances security with usability. The policy is designed to be easy to understand and not overly restrictive while still maintaining reasonable security standards.

## Policy Requirements

### Minimum Requirements

Your password must meet these basic requirements:

1. **Minimum Length**: 8 characters
2. **Character Diversity**: Must include at least 2 of the following 3 categories:
   - Letters (uppercase OR lowercase)
   - Numbers (0-9)
   - Special characters (!@#$%^&*()_+-=[]{}|;:,.<>?)

### What We DON'T Require

To keep things simple and user-friendly:

- No maximum length restriction
- No forced password expiration
- No password history (you can reuse passwords)
- No requirement for ALL character types (just 2 out of 3)
- Common passwords are warned about but not blocked

## Password Strength Ratings

When you create or change a password, you'll receive a strength rating:

- **Weak**: Meets minimum requirements but could be improved
- **Medium**: Good balance of length and character variety
- **Strong**: Excellent password with high security

## Examples

### Valid Passwords

These passwords will be accepted:

| Password | Why It Works |
|----------|--------------|
| `mypassword123` | 8+ chars, letters + numbers |
| `MyDog2024` | 8+ chars, letters + numbers |
| `super-secure` | 8+ chars, letters + special characters |
| `Hello123!` | 8+ chars, letters + numbers + special char |
| `Coffee&Code` | 8+ chars, letters + special characters |
| `SecurePass99` | 8+ chars, mixed case + numbers |
| `my_password_1` | 8+ chars, letters + special char + numbers |

### Invalid Passwords

These passwords will be rejected:

| Password | Why It Fails |
|----------|--------------|
| `test123` | Too short (only 7 characters) |
| `12345678` | Only contains numbers |
| `password` | Only contains letters |
| `abc` | Too short |
| `qwerty` | Only letters, too short |
| `aaaaaaaa` | Only letters, repetitive pattern |

## Tips for Creating Strong Passwords

1. **Use a passphrase**: Combine 3-4 words with numbers or special characters
   - Example: `Coffee&Code2024`

2. **Make it longer**: Passwords 12+ characters are significantly more secure
   - Example: `MyFavoriteDog2024`

3. **Mix character types**: Use uppercase, lowercase, numbers, and special characters
   - Example: `SecureP@ss123`

4. **Avoid common patterns**: Don't use sequential numbers (123) or letters (abc)

5. **Make it memorable**: Use something you can remember without writing it down
   - Example: `ILove2Code!`

## API Endpoints

### Get Password Policy Requirements

```bash
GET /api/v1/auth/password-policy
```

Returns the current password policy requirements and examples.

**Response:**
```json
{
  "minimum_length": 8,
  "required_categories": 2,
  "categories": [
    "Letters (uppercase or lowercase)",
    "Numbers (0-9)",
    "Special characters (!@#$%^&*()_+-=[]{}|;:,.<>?)"
  ],
  "restrictions": {
    "maximum_length": null,
    "forced_expiration": false,
    "password_history": false
  },
  "examples": {
    "valid": [
      "mypassword123",
      "MyDog2024",
      "super-secure"
    ],
    "invalid": [
      "test123",
      "12345678",
      "password"
    ]
  }
}
```

### Change Password

```bash
POST /api/v1/auth/change-password
```

**Request Body:**
```json
{
  "current_password": "OldPassword123",
  "new_password": "NewPassword456"
}
```

**Success Response:**
```json
{
  "success": true,
  "message": "Password changed successfully",
  "strength": "medium",
  "warnings": [
    "Password contains sequential numbers"
  ]
}
```

**Error Response (Invalid Password):**
```json
{
  "detail": "Password must be at least 8 characters long"
}
```

**Error Response (Wrong Current Password):**
```json
{
  "detail": "Current password is incorrect"
}
```

## Error Messages

Our error messages are designed to be helpful and actionable:

### Common Error Messages

1. **"Password must be at least 8 characters long"**
   - Your password is too short
   - Solution: Add more characters to reach 8+

2. **"Password should include at least 2 of these: letters, numbers, or special characters"**
   - Your password only uses one character type
   - Solution: Add numbers to a letter-only password, or add letters to a number-only password

3. **"Current password is incorrect"**
   - The current password you entered doesn't match
   - Solution: Double-check your current password

### Warning Messages (Non-Blocking)

These warnings inform you but won't prevent password changes:

1. **"This password is commonly used and may be easy to guess"**
   - Your password is on the common passwords list
   - Recommendation: Consider using a more unique password

2. **"Password contains sequential numbers"**
   - Your password has patterns like 123, 234, etc.
   - Recommendation: Use random numbers instead

3. **"Password contains sequential letters"**
   - Your password has patterns like abc, def, etc.
   - Recommendation: Use random letter combinations

## Implementation Details

### Files

- **`/backend/password_policy.py`**: Core password validation logic
- **`/backend/auth_manager.py`**: User authentication and password management
- **`/backend/server.py`**: API endpoints for password operations

### Functions

- `validate_password(password: str)`: Validates a password against the policy
- `check_password_strength(password: str)`: Returns password strength rating
- `get_password_requirements()`: Returns policy requirements for display

## Security Considerations

### Why This Policy?

1. **8-character minimum**: Industry standard for basic security
2. **2-of-3 categories**: Balances security with usability
3. **No expiration**: Modern security research shows forced expiration leads to weaker passwords
4. **No history**: Simplifies password management without significantly reducing security
5. **Warnings not blocks**: Educates users without frustrating them

### What We Check

1. Password length
2. Character category diversity
3. Common password detection
4. Sequential patterns
5. Repetitive characters

### What We Store

- Passwords are hashed using bcrypt (never stored in plain text)
- Password hashes are salted (unique per user)
- No password hints or reversible encryption

## Best Practices

### For Users

1. Use a password manager to generate and store complex passwords
2. Don't reuse passwords across different services
3. Enable two-factor authentication when available
4. Change your password if you suspect it's been compromised

### For Administrators

1. Monitor failed login attempts
2. Review user account security regularly
3. Educate users about password security
4. Consider implementing two-factor authentication

## Frequently Asked Questions

### Q: Why don't you require uppercase AND lowercase AND numbers AND special characters?

A: Research shows that overly complex requirements lead users to create predictable patterns (like "Password1!"). Our policy focuses on length and basic diversity, which creates stronger passwords in practice.

### Q: Why no password expiration?

A: Modern security guidelines (including NIST) recommend against forced password expiration. It leads to:
- Predictable password changes (adding numbers or incrementing dates)
- Written-down passwords
- User frustration
- No significant security benefit

### Q: Can I use spaces in my password?

A: Yes! Spaces are allowed and can help create memorable passphrases like "I Love Coffee 2024".

### Q: What if I forget my password?

A: Contact your system administrator for password reset assistance. For security reasons, passwords cannot be recovered, only reset.

### Q: Are common passwords blocked?

A: No, they trigger a warning but are not blocked. We believe in educating users rather than forcing choices. However, we strongly recommend choosing a unique password.

## Version History

- **v1.0.0** (2025-01-09): Initial implementation with user-friendly policy
  - Minimum 8 characters
  - 2-of-3 character categories
  - No expiration or history
  - Common password warnings

## Support

For questions or issues with the password policy, please contact:

- Technical Support: support@unicorncommander.ai
- Security Team: security@unicorncommander.ai
- Documentation: https://unicorncommander.ai/docs

---

**Remember**: A strong password is one you can remember and that nobody else can guess!
