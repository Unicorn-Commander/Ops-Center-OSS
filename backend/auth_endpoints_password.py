"""
Additional authentication endpoints for email/password
Add these to server.py
"""
from pydantic import BaseModel
from fastapi import HTTPException, Response
import secrets


class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str


class LoginRequest(BaseModel):
    email: str
    password: str


def add_password_auth_endpoints(app, password_auth, session_manager, get_db):
    """Add password authentication endpoints to FastAPI app"""

    @app.post("/auth/register")
    async def register_user(data: RegisterRequest, response: Response):
        """Register new user with email/password"""
        
        # Validate email
        valid_email, email_error = password_auth.validate_email(data.email)
        if not valid_email:
            raise HTTPException(status_code=400, detail=email_error)
        
        # Validate password strength
        valid_password, password_error = password_auth.validate_password_strength(data.password)
        if not valid_password:
            raise HTTPException(status_code=400, detail=password_error)
        
        # Hash password
        password_hash, salt = password_auth.hash_password(data.password)
        
        # Create user in database
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Check if email already exists
            cursor.execute("SELECT id FROM users WHERE email = ?", (data.email,))
            if cursor.fetchone():
                raise HTTPException(status_code=400, detail="Email already registered")
            
            # Create user
            user_id = secrets.token_urlsafe(16)
            cursor.execute("""
                INSERT INTO users (id, email, name, password_hash, password_salt, subscription_tier, oauth_provider, oauth_id)
                VALUES (?, ?, ?, ?, ?, 'trial', 'password', ?)
            """, (user_id, data.email, data.name, password_hash, salt, user_id))
        
        # Create session
        session_token = session_manager.create_session({
            "user_id": user_id,
            "email": data.email,
            "name": data.name,
            "subscription_tier": "trial"
        })
        
        # Set session cookie
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=86400
        )
        
        return {
            "success": True,
            "message": "Account created successfully",
            "redirect": "/dashboard"
        }

    @app.post("/auth/login/password")
    async def login_with_password(data: LoginRequest, response: Response):
        """Login with email/password"""
        
        # Find user
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM users WHERE email = ? AND oauth_provider = 'password'",
                (data.email,)
            )
            row = cursor.fetchone()
            
            if not row:
                raise HTTPException(status_code=401, detail="Invalid email or password")
            
            user = dict(row)
        
        # Verify password
        if not password_auth.verify_password(data.password, user["password_hash"], user["password_salt"]):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Create session
        session_token = session_manager.create_session({
            "user_id": user["id"],
            "email": user["email"],
            "name": user["name"],
            "subscription_tier": user["subscription_tier"]
        })
        
        # Set session cookie
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=86400
        )
        
        return {
            "success": True,
            "message": "Login successful",
            "redirect": "/dashboard"
        }

