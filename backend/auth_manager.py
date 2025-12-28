"""Authentication and User Management Module

This module handles user authentication, authorization, and security management.
"""

import os
import json
import secrets
import hashlib
import jwt
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel, Field, validator
import bcrypt
import asyncio
from concurrent.futures import ThreadPoolExecutor
from password_policy import validate_password

class User(BaseModel):
    """User model"""
    id: str
    username: str
    email: str
    full_name: str
    role: str = "user"  # admin, user, viewer
    is_active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    last_login: Optional[str] = None
    
class UserCreate(BaseModel):
    """User creation model"""
    username: str
    email: str
    password: str
    full_name: str
    role: str = "user"

    @validator('username')
    def username_alphanumeric(cls, v):
        assert v.replace('_', '').replace('-', '').isalnum(), 'Username must be alphanumeric'
        return v

    @validator('email')
    def email_valid(cls, v):
        assert '@' in v, 'Invalid email format'
        return v

    @validator('password')
    def password_strength(cls, v):
        """Validate password against password policy"""
        result = validate_password(v)
        if not result['valid']:
            raise ValueError(result['feedback'])
        return v

class UserUpdate(BaseModel):
    """User update model"""
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None

class PasswordChange(BaseModel):
    """Password change model"""
    current_password: str
    new_password: str

    @validator('new_password')
    def password_strength(cls, v):
        """Validate new password against password policy"""
        result = validate_password(v)
        if not result['valid']:
            raise ValueError(result['feedback'])
        return v

class LoginCredentials(BaseModel):
    """Login credentials model"""
    username: str
    password: str

class Token(BaseModel):
    """JWT token model"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600

class APIKey(BaseModel):
    """API key model"""
    id: str
    name: str
    key_prefix: str
    created_at: str
    last_used: Optional[str] = None
    expires_at: Optional[str] = None
    permissions: List[str] = Field(default_factory=list)

class APIKeyCreate(BaseModel):
    """API key creation model"""
    name: str
    expires_in_days: Optional[int] = None
    permissions: List[str] = Field(default_factory=list)

class Session(BaseModel):
    """User session model"""
    id: str
    user_id: str
    ip_address: str
    user_agent: str
    created_at: str
    expires_at: str
    is_active: bool = True

class AuthManager:
    """Manages authentication and user management"""
    
    def __init__(self):
        self.base_dir = Path("/home/ucadmin/UC-1-Pro")
        self.data_dir = self.base_dir / "services" / "admin-dashboard" / "data"
        self.users_file = self.data_dir / "users.json"
        self.api_keys_file = self.data_dir / "api_keys.json"
        self.sessions_file = self.data_dir / "sessions.json"
        
        # JWT configuration
        self.secret_key = os.getenv("JWT_SECRET_KEY", self._generate_secret_key())
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 60
        
        # Ensure directories exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Load data
        self.users = self._load_users()
        self.api_keys = self._load_api_keys()
        self.sessions = self._load_sessions()
        
        # Create default admin user if none exists
        self._ensure_admin_user()
    
    def _generate_secret_key(self) -> str:
        """Generate a secure secret key"""
        return secrets.token_urlsafe(32)
    
    def _load_users(self) -> Dict[str, Dict[str, Any]]:
        """Load users from file"""
        if self.users_file.exists():
            try:
                with open(self.users_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading users: {e}")
        return {}
    
    def _save_users(self):
        """Save users to file"""
        try:
            with open(self.users_file, 'w') as f:
                json.dump(self.users, f, indent=2)
        except Exception as e:
            print(f"Error saving users: {e}")
    
    def _load_api_keys(self) -> Dict[str, Dict[str, Any]]:
        """Load API keys from file"""
        if self.api_keys_file.exists():
            try:
                with open(self.api_keys_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading API keys: {e}")
        return {}
    
    def _save_api_keys(self):
        """Save API keys to file"""
        try:
            with open(self.api_keys_file, 'w') as f:
                json.dump(self.api_keys, f, indent=2)
        except Exception as e:
            print(f"Error saving API keys: {e}")
    
    def _load_sessions(self) -> Dict[str, Dict[str, Any]]:
        """Load sessions from file"""
        if self.sessions_file.exists():
            try:
                with open(self.sessions_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading sessions: {e}")
        return {}
    
    def _save_sessions(self):
        """Save sessions to file"""
        try:
            with open(self.sessions_file, 'w') as f:
                json.dump(self.sessions, f, indent=2)
        except Exception as e:
            print(f"Error saving sessions: {e}")
    
    def _ensure_admin_user(self):
        """Ensure at least one admin user exists"""
        has_admin = any(user.get('role') == 'admin' for user in self.users.values())
        
        if not has_admin:
            # Create default admin user
            admin_password = os.getenv("ADMIN_PASSWORD", "your-admin-password")
            admin_user = UserCreate(
                username="ucadmin",
                email="admin@your-domain.com",
                password=admin_password,
                full_name="UC-1 Admin",
                role="admin"
            )
            self.create_user(admin_user)
            print("Created default admin user: ucadmin")
    
    def _hash_password(self, password: str) -> str:
        """Hash a password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def _verify_password_sync(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash (sync version)"""
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    
    async def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash (async version)"""
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            return await loop.run_in_executor(
                executor, 
                self._verify_password_sync,
                plain_password, 
                hashed_password
            )
    
    def _generate_user_id(self) -> str:
        """Generate a unique user ID"""
        return f"user_{secrets.token_urlsafe(8)}"
    
    def _generate_api_key(self) -> str:
        """Generate a secure API key"""
        return f"uc1_{''.join(secrets.choice('abcdefghijklmnopqrstuvwxyz0123456789') for _ in range(32))}"
    
    def _create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_user(self, user_create: UserCreate) -> Dict[str, Any]:
        """Create a new user"""
        # Check if username already exists
        if any(u.get('username') == user_create.username for u in self.users.values()):
            raise ValueError("Username already exists")
        
        # Check if email already exists
        if any(u.get('email') == user_create.email for u in self.users.values()):
            raise ValueError("Email already exists")
        
        # Create user
        user_id = self._generate_user_id()
        user = User(
            id=user_id,
            username=user_create.username,
            email=user_create.email,
            full_name=user_create.full_name,
            role=user_create.role
        )
        
        # Store user with hashed password
        user_data = user.dict()
        user_data['password_hash'] = self._hash_password(user_create.password)
        
        self.users[user_id] = user_data
        self._save_users()
        
        return user.dict()
    
    async def authenticate_user(self, credentials: LoginCredentials) -> Optional[Dict[str, Any]]:
        """Authenticate a user with username and password"""
        # Find user by username
        user_data = None
        for uid, udata in self.users.items():
            if udata.get('username') == credentials.username:
                user_data = udata
                break
        
        if not user_data:
            return None
        
        # Verify password (async to prevent blocking)
        if not await self._verify_password(credentials.password, user_data.get('password_hash', '')):
            return None
        
        # Update last login
        user_data['last_login'] = datetime.now().isoformat()
        self._save_users()
        
        # Return user without password hash
        user = {k: v for k, v in user_data.items() if k != 'password_hash'}
        return user
    
    async def login(self, credentials: LoginCredentials, request_info: Dict[str, str]) -> Token:
        """Login and create access token"""
        user = await self.authenticate_user(credentials)
        if not user:
            raise ValueError("Invalid username or password")
        
        if not user.get('is_active'):
            raise ValueError("User account is disabled")
        
        # Create session
        session_id = secrets.token_urlsafe(16)
        expires_at = datetime.now() + timedelta(minutes=self.access_token_expire_minutes)
        
        session = Session(
            id=session_id,
            user_id=user['id'],
            ip_address=request_info.get('ip_address', 'unknown'),
            user_agent=request_info.get('user_agent', 'unknown'),
            created_at=datetime.now().isoformat(),
            expires_at=expires_at.isoformat()
        )
        
        self.sessions[session_id] = session.dict()
        self._save_sessions()
        
        # Create access token
        access_token = self._create_access_token(
            data={"sub": user['id'], "username": user['username'], "role": user['role'], "session": session_id}
        )
        
        return Token(
            access_token=access_token,
            expires_in=self.access_token_expire_minutes * 60
        )
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id = payload.get("sub")
            session_id = payload.get("session")
            
            # Verify user exists and is active
            user = self.users.get(user_id)
            if not user or not user.get('is_active'):
                return None
            
            # Verify session is valid
            session = self.sessions.get(session_id)
            if not session or not session.get('is_active'):
                return None
            
            # Check session expiration
            expires_at = datetime.fromisoformat(session['expires_at'])
            if datetime.now() > expires_at:
                session['is_active'] = False
                self._save_sessions()
                return None
            
            return {
                "user_id": user_id,
                "username": payload.get("username"),
                "role": payload.get("role"),
                "session_id": session_id
            }
            
        except jwt.ExpiredSignatureError:
            return None
        except jwt.JWTError:
            return None
    
    def logout(self, session_id: str):
        """Logout and invalidate session"""
        if session_id in self.sessions:
            self.sessions[session_id]['is_active'] = False
            self._save_sessions()
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        user_data = self.users.get(user_id)
        if user_data:
            # Return user without password hash
            return {k: v for k, v in user_data.items() if k != 'password_hash'}
        return None
    
    def get_users(self) -> List[Dict[str, Any]]:
        """Get all users"""
        users = []
        for user_data in self.users.values():
            # Return users without password hashes
            users.append({k: v for k, v in user_data.items() if k != 'password_hash'})
        return users
    
    def update_user(self, user_id: str, user_update: UserUpdate) -> Optional[Dict[str, Any]]:
        """Update user information"""
        if user_id not in self.users:
            return None
        
        user_data = self.users[user_id]
        
        # Update fields
        update_data = user_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                user_data[field] = value
        
        self._save_users()
        
        # Return updated user without password hash
        return {k: v for k, v in user_data.items() if k != 'password_hash'}
    
    def change_password(self, user_id: str, password_change: PasswordChange) -> Dict[str, Any]:
        """
        Change user password

        Returns:
            Dictionary with success status and optional message
            Example: {"success": True, "message": "Password changed successfully"}
                    or {"success": False, "error": "Invalid current password"}
        """
        if user_id not in self.users:
            return {"success": False, "error": "User not found"}

        user_data = self.users[user_id]

        # Verify current password (sync version for compatibility)
        if not self._verify_password_sync(password_change.current_password, user_data.get('password_hash', '')):
            return {"success": False, "error": "Current password is incorrect"}

        # Validate new password (already validated by pydantic, but get strength info)
        from password_policy import validate_password
        validation_result = validate_password(password_change.new_password)

        # Update password
        user_data['password_hash'] = self._hash_password(password_change.new_password)
        self._save_users()

        # Invalidate all user sessions
        for session_id, session in self.sessions.items():
            if session.get('user_id') == user_id:
                session['is_active'] = False
        self._save_sessions()

        # Return success with strength info and warnings
        result = {
            "success": True,
            "message": "Password changed successfully",
            "strength": validation_result.get("strength", "unknown")
        }

        if validation_result.get("warnings"):
            result["warnings"] = validation_result["warnings"]

        return result
    
    def delete_user(self, user_id: str) -> bool:
        """Delete a user"""
        if user_id not in self.users:
            return False
        
        # Don't delete the last admin
        user = self.users[user_id]
        if user.get('role') == 'admin':
            admin_count = sum(1 for u in self.users.values() if u.get('role') == 'admin')
            if admin_count <= 1:
                raise ValueError("Cannot delete the last admin user")
        
        # Delete user
        del self.users[user_id]
        self._save_users()
        
        # Invalidate all user sessions
        for session_id, session in list(self.sessions.items()):
            if session.get('user_id') == user_id:
                del self.sessions[session_id]
        self._save_sessions()
        
        # Delete user's API keys
        for key_id, key_data in list(self.api_keys.items()):
            if key_data.get('user_id') == user_id:
                del self.api_keys[key_id]
        self._save_api_keys()
        
        return True
    
    def create_api_key(self, user_id: str, key_create: APIKeyCreate) -> Dict[str, Any]:
        """Create a new API key"""
        # Generate key
        api_key = self._generate_api_key()
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        key_prefix = api_key[:7]
        
        # Calculate expiration
        expires_at = None
        if key_create.expires_in_days:
            expires_at = (datetime.now() + timedelta(days=key_create.expires_in_days)).isoformat()
        
        # Create key record
        key_data = APIKey(
            id=key_hash,
            name=key_create.name,
            key_prefix=key_prefix,
            created_at=datetime.now().isoformat(),
            expires_at=expires_at,
            permissions=key_create.permissions
        )
        
        # Store key data with user association
        key_record = key_data.dict()
        key_record['user_id'] = user_id
        self.api_keys[key_hash] = key_record
        self._save_api_keys()
        
        # Return key info with actual key (only shown once)
        result = key_data.dict()
        result['api_key'] = api_key
        return result
    
    def verify_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """Verify an API key"""
        # Hash the key to find it
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        key_data = self.api_keys.get(key_hash)
        
        if not key_data:
            return None
        
        # Check expiration
        if key_data.get('expires_at'):
            expires_at = datetime.fromisoformat(key_data['expires_at'])
            if datetime.now() > expires_at:
                return None
        
        # Update last used
        key_data['last_used'] = datetime.now().isoformat()
        self._save_api_keys()
        
        # Get associated user
        user = self.get_user(key_data['user_id'])
        if not user or not user.get('is_active'):
            return None
        
        return {
            "user_id": user['id'],
            "username": user['username'],
            "role": user['role'],
            "permissions": key_data.get('permissions', []),
            "api_key_id": key_hash
        }
    
    def get_user_api_keys(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all API keys for a user"""
        keys = []
        for key_data in self.api_keys.values():
            if key_data.get('user_id') == user_id:
                # Don't include the actual key hash
                keys.append({k: v for k, v in key_data.items() if k != 'user_id'})
        return keys
    
    def delete_api_key(self, key_id: str, user_id: str) -> bool:
        """Delete an API key"""
        key_data = self.api_keys.get(key_id)
        if not key_data or key_data.get('user_id') != user_id:
            return False
        
        del self.api_keys[key_id]
        self._save_api_keys()
        return True
    
    def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all sessions for a user"""
        sessions = []
        for session_data in self.sessions.values():
            if session_data.get('user_id') == user_id:
                sessions.append(session_data)
        return sorted(sessions, key=lambda x: x['created_at'], reverse=True)
    
    def revoke_session(self, session_id: str, user_id: str) -> bool:
        """Revoke a specific session"""
        session = self.sessions.get(session_id)
        if not session or session.get('user_id') != user_id:
            return False
        
        session['is_active'] = False
        self._save_sessions()
        return True
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        now = datetime.now()
        expired_sessions = []
        
        for session_id, session in self.sessions.items():
            expires_at = datetime.fromisoformat(session['expires_at'])
            if now > expires_at:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
        
        if expired_sessions:
            self._save_sessions()
        
        return len(expired_sessions)

# Create singleton instance
auth_manager = AuthManager()