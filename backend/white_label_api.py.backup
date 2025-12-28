"""
White-Label Configuration API
GUI-based white-label customization for Ops-Center landing page

Admins can customize branding (logo, colors, company name) through a web interface
without editing config files or restarting containers.

Endpoints:
- GET    /api/v1/admin/white-label/config         - Get current config
- PUT    /api/v1/admin/white-label/config         - Update config
- POST   /api/v1/admin/white-label/logo           - Upload logo file
- GET    /api/v1/admin/white-label/preview        - Preview config before saving
- GET    /api/v1/admin/white-label/templates      - List available template bases
- GET    /api/v1/admin/white-label/colors/presets - Get color presets
- POST   /api/v1/admin/white-label/reset          - Reset to default

Integration:
- Loads config from platform_settings table in PostgreSQL
- Saves uploaded logos to /app/public/logos/ directory
- Calls landing_config.reload_with_white_label() to apply changes (no restart!)
"""

from fastapi import APIRouter, HTTPException, Depends, Request, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any
import os
import json
import shutil
from pathlib import Path
from datetime import datetime
import logging
import asyncpg
import hashlib
import io

# Optional PIL import for image validation
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("Warning: PIL (Pillow) not available - image validation disabled")

# Import landing config singleton
from landing_config import landing_config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin/white-label", tags=["White Label"])

# ============================================================================
# CONSTANTS
# ============================================================================

LOGO_UPLOAD_DIR = Path("/app/public/logos")
ALLOWED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/gif", "image/webp"}
MAX_LOGO_SIZE_MB = 2
MAX_LOGO_SIZE_BYTES = MAX_LOGO_SIZE_MB * 1024 * 1024

# Color presets for quick theming
COLOR_PRESETS = {
    "professional": {
        "name": "Professional Blue",
        "primary": "#3B82F6",
        "secondary": "#1E40AF",
        "accent": "#10B981",
        "background_gradient": "linear-gradient(135deg, #1E40AF 0%, #3B82F6 100%)"
    },
    "unicorn": {
        "name": "Magic Unicorn",
        "primary": "#8B5CF6",
        "secondary": "#EC4899",
        "accent": "#F59E0B",
        "background_gradient": "linear-gradient(135deg, #8B5CF6 0%, #EC4899 50%, #F59E0B 100%)"
    },
    "ocean": {
        "name": "Ocean Breeze",
        "primary": "#0EA5E9",
        "secondary": "#06B6D4",
        "accent": "#10B981",
        "background_gradient": "linear-gradient(135deg, #0891B2 0%, #0EA5E9 50%, #06B6D4 100%)"
    },
    "sunset": {
        "name": "Sunset Glow",
        "primary": "#F97316",
        "secondary": "#EA580C",
        "accent": "#FCD34D",
        "background_gradient": "linear-gradient(135deg, #F97316 0%, #EA580C 50%, #DC2626 100%)"
    },
    "forest": {
        "name": "Forest Green",
        "primary": "#10B981",
        "secondary": "#059669",
        "accent": "#34D399",
        "background_gradient": "linear-gradient(135deg, #064E3B 0%, #047857 50%, #10B981 100%)"
    },
    "corporate": {
        "name": "Corporate Gray",
        "primary": "#6366F1",
        "secondary": "#4F46E5",
        "accent": "#A78BFA",
        "background_gradient": "linear-gradient(135deg, #1F2937 0%, #111827 100%)"
    }
}

# Template bases for different industries/use cases
TEMPLATES = {
    "default": {
        "name": "Default UC-Cloud",
        "description": "Standard UC-Cloud branding",
        "branding": {
            "company_name": "UC-1 Pro Operations Center",
            "company_subtitle": "Enterprise AI Infrastructure Platform",
            "logo_url": "/the-colonel-logo.png"
        }
    },
    "ai_platform": {
        "name": "AI Platform",
        "description": "Generic AI platform branding",
        "branding": {
            "company_name": "AI Operations Platform",
            "company_subtitle": "Enterprise Intelligence Hub",
            "logo_url": "/logos/ai-platform.png"
        }
    },
    "enterprise": {
        "name": "Enterprise",
        "description": "Corporate enterprise branding",
        "branding": {
            "company_name": "Enterprise AI Center",
            "company_subtitle": "Advanced Technology Platform",
            "logo_url": "/logos/enterprise.png"
        }
    },
    "startup": {
        "name": "Startup",
        "description": "Modern startup branding",
        "branding": {
            "company_name": "AI Innovation Hub",
            "company_subtitle": "Next-Generation Intelligence",
            "logo_url": "/logos/startup.png"
        }
    }
}

# ============================================================================
# MODELS
# ============================================================================

class ColorTheme(BaseModel):
    """Color theme configuration"""
    primary: str = Field(..., description="Primary color (hex)")
    secondary: str = Field(..., description="Secondary color (hex)")
    accent: str = Field(..., description="Accent color (hex)")
    background_gradient: str = Field(..., description="CSS gradient string")

    @validator('primary', 'secondary', 'accent')
    def validate_hex_color(cls, v):
        """Validate hex color format"""
        if not v.startswith('#') or len(v) not in [4, 7]:
            raise ValueError(f"Invalid hex color: {v}")
        return v

class BrandingConfig(BaseModel):
    """Branding configuration"""
    logo_url: str = Field(..., description="Logo URL (relative or absolute)")
    company_name: str = Field(..., max_length=100, description="Company name")
    company_subtitle: str = Field(..., max_length=200, description="Company subtitle/tagline")
    show_emoji: bool = Field(default=False, description="Show emoji in branding")
    emoji: str = Field(default="🚀", max_length=5, description="Emoji to display")

class WhiteLabelConfig(BaseModel):
    """Complete white-label configuration"""
    theme: ColorTheme
    branding: BrandingConfig
    welcome_title: Optional[str] = Field(None, max_length=200, description="Landing page welcome title")
    welcome_description: Optional[str] = Field(None, max_length=500, description="Landing page description")
    animations_enabled: bool = Field(default=True, description="Enable animations")

class WhiteLabelUpdateRequest(BaseModel):
    """Request to update white-label configuration"""
    theme: Optional[ColorTheme] = None
    branding: Optional[BrandingConfig] = None
    welcome_title: Optional[str] = None
    welcome_description: Optional[str] = None
    animations_enabled: Optional[bool] = None

# ============================================================================
# DEPENDENCY: REQUIRE ADMIN
# ============================================================================

async def require_admin(request: Request):
    """Verify user is authenticated and has admin role"""
    import sys
    if '/app' not in sys.path:
        sys.path.insert(0, '/app')

    from redis_session import RedisSessionManager

    # Get session token from cookie
    session_token = request.cookies.get("session_token")
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Get Redis connection info
    redis_host = os.getenv("REDIS_HOST", "unicorn-redis")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))

    # Initialize session manager
    sessions = RedisSessionManager(host=redis_host, port=redis_port)

    # Get session data
    if session_token not in sessions:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    session_data = sessions[session_token]
    user = session_data.get("user", {})

    if not user:
        raise HTTPException(status_code=401, detail="User not found in session")

    # Check if user has admin role
    if not user.get("is_admin") and user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    return True

# ============================================================================
# DATABASE UTILITIES
# ============================================================================

async def get_db_connection():
    """Get PostgreSQL database connection"""
    try:
        conn = await asyncpg.connect(
            host=os.getenv('POSTGRES_HOST', 'unicorn-postgresql'),
            port=int(os.getenv('POSTGRES_PORT', '5432')),
            user=os.getenv('POSTGRES_USER', 'unicorn'),
            password=os.getenv('POSTGRES_PASSWORD', 'unicorn'),
            database=os.getenv('POSTGRES_DB', 'unicorn_db')
        )
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")

async def get_white_label_config_from_db() -> Dict[str, Any]:
    """Load white-label configuration from platform_settings table"""
    conn = await get_db_connection()
    try:
        # Query for white-label settings
        rows = await conn.fetch(
            "SELECT key, value FROM platform_settings WHERE category = 'white_label' ORDER BY key"
        )

        if not rows:
            return None

        # Build config dictionary
        config = {}
        for row in rows:
            key = row['key']
            value = row['value']

            # Parse JSON values
            if key.endswith('_json'):
                try:
                    config[key.replace('_json', '')] = json.loads(value)
                except:
                    config[key] = value
            else:
                config[key] = value

        return config
    finally:
        await conn.close()

async def save_white_label_config_to_db(config: Dict[str, Any]) -> bool:
    """Save white-label configuration to platform_settings table"""
    conn = await get_db_connection()
    try:
        # Delete existing white-label settings
        await conn.execute("DELETE FROM platform_settings WHERE category = 'white_label'")

        # Insert new settings
        for key, value in config.items():
            # Convert complex objects to JSON
            if isinstance(value, (dict, list)):
                db_key = f"{key}_json"
                db_value = json.dumps(value)
            else:
                db_key = key
                db_value = str(value)

            await conn.execute(
                """
                INSERT INTO platform_settings (key, value, category, is_secret, updated_at)
                VALUES ($1, $2, 'white_label', false, $3)
                """,
                db_key, db_value, datetime.utcnow()
            )

        return True
    except Exception as e:
        logger.error(f"Failed to save white-label config to database: {e}")
        return False
    finally:
        await conn.close()

# ============================================================================
# FILE UPLOAD UTILITIES
# ============================================================================

def validate_image(file: UploadFile) -> bool:
    """Validate uploaded image file"""
    # Check file type
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_IMAGE_TYPES)}"
        )

    return True

async def save_logo_file(file: UploadFile) -> str:
    """Save uploaded logo file and return URL"""
    # Create logos directory if it doesn't exist
    LOGO_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # Read file content
    content = await file.read()

    # Check file size
    if len(content) > MAX_LOGO_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds {MAX_LOGO_SIZE_MB}MB limit"
        )

    # Validate image using PIL (if available)
    if PIL_AVAILABLE:
        try:
            img = Image.open(io.BytesIO(content))
            img.verify()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid image file: {str(e)}")
    else:
        logger.warning("PIL not available - skipping image validation")

    # Generate unique filename using hash
    file_hash = hashlib.md5(content).hexdigest()[:12]
    file_ext = Path(file.filename).suffix
    filename = f"logo_{file_hash}{file_ext}"

    # Save file
    file_path = LOGO_UPLOAD_DIR / filename
    with open(file_path, 'wb') as f:
        f.write(content)

    # Return relative URL
    return f"/logos/{filename}"

# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/config")
async def get_white_label_config(admin: bool = Depends(require_admin)):
    """
    Get current white-label configuration

    Returns the active white-label configuration from database or defaults
    """
    try:
        # Try to load from database first
        db_config = await get_white_label_config_from_db()

        if db_config:
            # Return database config
            return {
                "source": "database",
                "config": db_config,
                "last_updated": db_config.get("last_updated")
            }

        # Fall back to landing_config defaults
        current_config = landing_config.get_config()

        return {
            "source": "default",
            "config": {
                "theme": current_config.get("theme", {}),
                "branding": current_config.get("branding", {}),
                "welcome_title": current_config.get("welcome", {}).get("title"),
                "welcome_description": current_config.get("welcome", {}).get("description"),
                "animations_enabled": current_config.get("animations", {}).get("enabled", True)
            }
        }

    except Exception as e:
        logger.error(f"Error getting white-label config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/config")
async def update_white_label_config(
    update: WhiteLabelUpdateRequest,
    admin: bool = Depends(require_admin)
):
    """
    Update white-label configuration

    Saves changes to database and applies them to landing_config (no restart required!)
    """
    try:
        # Get current config
        current = await get_white_label_config_from_db()
        if not current:
            # Initialize with defaults if not exists
            current = {
                "theme": landing_config.THEME_PRESETS["professional"],
                "branding": landing_config.DEFAULT_CONFIG["branding"],
                "welcome_title": landing_config.DEFAULT_CONFIG["welcome"]["title"],
                "welcome_description": landing_config.DEFAULT_CONFIG["welcome"]["description"],
                "animations_enabled": True
            }

        # Apply updates
        if update.theme:
            current["theme"] = update.theme.dict()

        if update.branding:
            current["branding"] = update.branding.dict()

        if update.welcome_title is not None:
            current["welcome_title"] = update.welcome_title

        if update.welcome_description is not None:
            current["welcome_description"] = update.welcome_description

        if update.animations_enabled is not None:
            current["animations_enabled"] = update.animations_enabled

        # Save to database
        current["last_updated"] = datetime.utcnow().isoformat()
        success = await save_white_label_config_to_db(current)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to save configuration")

        # Apply to landing_config (live update, no restart!)
        landing_update = {
            "theme": {
                "preset": "custom",
                "custom_colors": current["theme"]
            },
            "branding": current["branding"],
            "welcome": {
                "title": current["welcome_title"],
                "description": current["welcome_description"]
            },
            "animations": {
                "enabled": current["animations_enabled"]
            }
        }

        landing_config.update_config(landing_update)

        return {
            "success": True,
            "message": "White-label configuration updated successfully",
            "config": current
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating white-label config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/logo")
async def upload_logo(
    file: UploadFile = File(...),
    admin: bool = Depends(require_admin)
):
    """
    Upload logo file

    Validates image file, saves to /app/public/logos/, and returns URL
    Max size: 2MB
    Allowed types: PNG, JPEG, GIF, WebP
    """
    try:
        # Validate image
        validate_image(file)

        # Save file and get URL
        logo_url = await save_logo_file(file)

        return {
            "success": True,
            "message": "Logo uploaded successfully",
            "logo_url": logo_url,
            "filename": Path(logo_url).name
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading logo: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/preview")
async def preview_config(admin: bool = Depends(require_admin)):
    """
    Preview configuration before saving

    Returns merged configuration showing how it will look when applied
    """
    try:
        # Get current database config
        db_config = await get_white_label_config_from_db()

        if not db_config:
            db_config = {
                "theme": landing_config.THEME_PRESETS["professional"],
                "branding": landing_config.DEFAULT_CONFIG["branding"]
            }

        # Get current landing config
        current_landing = landing_config.get_config()

        # Merge to show preview
        preview = {
            "theme": db_config.get("theme", current_landing["theme"]),
            "branding": db_config.get("branding", current_landing["branding"]),
            "welcome": {
                "title": db_config.get("welcome_title", current_landing["welcome"]["title"]),
                "description": db_config.get("welcome_description", current_landing["welcome"]["description"])
            },
            "animations": {
                "enabled": db_config.get("animations_enabled", True)
            }
        }

        return {
            "preview": preview,
            "note": "This is how the landing page will look when this configuration is applied"
        }

    except Exception as e:
        logger.error(f"Error generating preview: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/templates")
async def list_templates(admin: bool = Depends(require_admin)):
    """
    List available template bases

    Returns pre-configured templates for different industries/use cases
    """
    return {
        "templates": [
            {
                "id": template_id,
                "name": template["name"],
                "description": template["description"],
                "preview": template["branding"]
            }
            for template_id, template in TEMPLATES.items()
        ]
    }

@router.get("/colors/presets")
async def list_color_presets(admin: bool = Depends(require_admin)):
    """
    Get color presets

    Returns pre-defined color schemes for quick theming
    """
    return {
        "presets": [
            {
                "id": preset_id,
                "name": preset["name"],
                "colors": {
                    "primary": preset["primary"],
                    "secondary": preset["secondary"],
                    "accent": preset["accent"],
                    "background_gradient": preset["background_gradient"]
                }
            }
            for preset_id, preset in COLOR_PRESETS.items()
        ]
    }

@router.post("/reset")
async def reset_to_default(admin: bool = Depends(require_admin)):
    """
    Reset to default configuration

    Removes all white-label customizations and restores defaults
    """
    try:
        # Delete from database
        conn = await get_db_connection()
        try:
            await conn.execute("DELETE FROM platform_settings WHERE category = 'white_label'")
        finally:
            await conn.close()

        # Reset landing_config to defaults
        landing_config.reset_to_default()

        return {
            "success": True,
            "message": "White-label configuration reset to defaults",
            "config": landing_config.DEFAULT_CONFIG
        }

    except Exception as e:
        logger.error(f"Error resetting white-label config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/apply-template/{template_id}")
async def apply_template(
    template_id: str,
    admin: bool = Depends(require_admin)
):
    """
    Apply a pre-configured template

    Quick way to apply industry-specific branding
    """
    if template_id not in TEMPLATES:
        raise HTTPException(status_code=404, detail=f"Template '{template_id}' not found")

    template = TEMPLATES[template_id]

    # Create update request from template
    update = WhiteLabelUpdateRequest(
        branding=BrandingConfig(**template["branding"])
    )

    # Apply the update
    return await update_white_label_config(update, admin=True)

@router.post("/apply-preset/{preset_id}")
async def apply_color_preset(
    preset_id: str,
    admin: bool = Depends(require_admin)
):
    """
    Apply a color preset

    Quick way to change color scheme
    """
    if preset_id not in COLOR_PRESETS:
        raise HTTPException(status_code=404, detail=f"Preset '{preset_id}' not found")

    preset = COLOR_PRESETS[preset_id]

    # Create update request from preset
    update = WhiteLabelUpdateRequest(
        theme=ColorTheme(**preset)
    )

    # Apply the update
    return await update_white_label_config(update, admin=True)
