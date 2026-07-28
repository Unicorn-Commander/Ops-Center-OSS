"""
Landing Page Configuration Management
Handles customization of the public landing page
"""

import json
import os
from typing import Dict, List, Any, Optional
from pathlib import Path

class LandingPageConfig:
    """Manages landing page customization settings"""
    
    CONFIG_FILE = "/app/config/landing_config.json"
    TEMPLATES_DIR = "/app/config/templates"
    DEFAULT_CONFIG = {
        "theme": {
            "preset": "dashboard",  # dashboard, magic-unicorn, professional, dark, ocean, sunset
            "custom_colors": {
                "primary": "#3B82F6",
                "secondary": "#8B5CF6",
                "accent": "#F59E0B",
                "background_gradient": "linear-gradient(135deg, #1e293b 0%, #334155 100%)"
            }
        },
        "branding": {
            "logo_url": "/the-colonel-logo.png",
            "company_name": "UC-1 Pro Operations Center",
            "company_subtitle": "Enterprise AI Infrastructure Platform",
            "show_emoji": False,
            "emoji": "🚀"
        },
        "welcome": {
            "title": "Welcome to UC-1 Pro Operations Center",
            "description": "Your enterprise AI infrastructure is ready. Experience the power of unified AI services with single sign-on authentication and advanced model management.",
            "show_emoji": True
        },
        "services": [
            {
                "id": "chat",
                "name": "Open-WebUI Chat",
                "icon": "💬",
                "logo_url": "/magic-unicorn-logo.png",
                "description": "Advanced AI chat interface powered by state-of-the-art language models",
                "url": "auto",  # auto means use default port/subdomain logic
                "port": 8080,
                "enabled": True,
                "order": 1
            },
            {
                "id": "search",
                "name": "Center-Deep Search",
                "icon": "🔍",
                "logo_url": "/center-deep-logo.png",
                "description": "AI-powered intelligent search platform with advanced tool servers",
                "url": "auto",
                "port": 8888,
                "enabled": True,
                "order": 2
            },
            {
                "id": "vllm",
                "name": "vLLM Engine",
                "icon": "🚀",
                "description": "High-performance LLM inference optimized for RTX 5090",
                "url": None,
                "port": 8000,
                "enabled": True,
                "apiOnly": True,
                "order": 3
            },
            {
                "id": "amanuensis",
                "name": "Unicorn Amanuensis",
                "icon": "🎙️",
                "logo_url": "/amanuensis-logo.png",
                "description": "Advanced speech-to-text with speaker diarization and 100+ languages",
                "url": "http://192.168.1.135:8887/web",
                "port": 8887,
                "enabled": True,
                "apiOnly": False,
                "order": 4,
                "subdomain": "stt",
                "path": "/web"
            },
            {
                "id": "orator",
                "name": "Unicorn Orator",
                "icon": "🔊",
                "logo_url": "/Unicorn_Orator.png",
                "description": "Professional AI voice synthesis with multiple voices and emotions",
                "url": "auto",
                "port": 8885,
                "enabled": True,
                "apiOnly": False,
                "order": 5
            },
            {
                "id": "qdrant",
                "name": "Qdrant Vector DB",
                "icon": "📊",
                "description": "High-performance vector database for RAG applications",
                "url": None,
                "port": 6333,
                "enabled": True,
                "apiOnly": True,
                "order": 6
            }
        ],
        "custom_links": [],  # Additional custom service cards
        "admin_section": {
            "enabled": True,
            "title": "Administrative Control Center",
            "description": "Access full system management, model configuration, and monitoring dashboards",
            "button_text": "Enter Admin Dashboard",
            "button_emoji": "🛡️"
        },
        "animations": {
            "enabled": True,
            "gradient_animation": True,
            "hover_effects": True,
            "loading_spinner": True
        }
    }
    
    THEME_PRESETS = {
        "dashboard": {
            "name": "Dashboard",
            "primary": "#3B82F6",
            "secondary": "#8B5CF6",
            "accent": "#F59E0B",
            "background_gradient": "linear-gradient(135deg, #1e293b 0%, #334155 100%)"
        },
        "magic-unicorn": {
            "name": "Magic Unicorn",
            "primary": "#8B5CF6",
            "secondary": "#EC4899",
            "accent": "#F59E0B",
            "background_gradient": "linear-gradient(135deg, #8B5CF6 0%, #EC4899 50%, #F59E0B 100%)"
        },
        "professional": {
            "name": "Professional",
            "primary": "#3B82F6",
            "secondary": "#1E40AF",
            "accent": "#10B981",
            "background_gradient": "linear-gradient(135deg, #1E40AF 0%, #3B82F6 100%)"
        },
        "dark": {
            "name": "Dark Mode",
            "primary": "#6366F1",
            "secondary": "#4F46E5",
            "accent": "#A78BFA",
            "background_gradient": "linear-gradient(135deg, #1F2937 0%, #111827 100%)"
        },
        "ocean": {
            "name": "Ocean",
            "primary": "#0EA5E9",
            "secondary": "#06B6D4",
            "accent": "#10B981",
            "background_gradient": "linear-gradient(135deg, #0891B2 0%, #0EA5E9 50%, #06B6D4 100%)"
        },
        "sunset": {
            "name": "Sunset",
            "primary": "#F97316",
            "secondary": "#EA580C",
            "accent": "#FCD34D",
            "background_gradient": "linear-gradient(135deg, #F97316 0%, #EA580C 50%, #DC2626 100%)"
        },
        "matrix": {
            "name": "Matrix",
            "primary": "#10B981",
            "secondary": "#059669",
            "accent": "#34D399",
            "background_gradient": "linear-gradient(135deg, #064E3B 0%, #047857 50%, #10B981 100%)"
        }
    }
    
    def __init__(self):
        self.config_path = Path(self.CONFIG_FILE)
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file or template"""
        try:
            # Check for template selection via environment variable
            template_name = os.getenv('LANDING_CONFIG_TEMPLATE', '')

            if template_name:
                # Load from template directory
                template_path = Path(self.TEMPLATES_DIR) / f"landing_config.{template_name}.json"
                if template_path.exists():
                    print(f"Loading landing config from template: {template_name}")
                    with open(template_path, 'r') as f:
                        config = json.load(f)
                        return self._merge_configs(self.DEFAULT_CONFIG, config)
                else:
                    print(f"Warning: Template '{template_name}' not found at {template_path}")

            # Fall back to default config file
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    return self._merge_configs(self.DEFAULT_CONFIG, config)
            else:
                # Create config directory if it doesn't exist
                self.config_path.parent.mkdir(parents=True, exist_ok=True)
                self.save_config(self.DEFAULT_CONFIG)
                return self.DEFAULT_CONFIG.copy()
        except Exception as e:
            print(f"Error loading landing config: {e}")
            return self.DEFAULT_CONFIG.copy()
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """Save configuration to file"""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
            self.config = config
            return True
        except Exception as e:
            print(f"Error saving landing config: {e}")
            return False
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration"""
        return self.config.copy()
    
    def update_config(self, updates: Dict[str, Any]) -> bool:
        """Update configuration with new values"""
        try:
            # Deep merge the updates
            new_config = self._merge_configs(self.config, updates)
            return self.save_config(new_config)
        except Exception as e:
            print(f"Error updating config: {e}")
            return False
    
    def apply_theme_preset(self, preset_name: str) -> bool:
        """Apply a predefined theme preset"""
        if preset_name not in self.THEME_PRESETS:
            return False
        
        preset = self.THEME_PRESETS[preset_name]
        theme_update = {
            "theme": {
                "preset": preset_name,
                "custom_colors": preset
            }
        }
        return self.update_config(theme_update)
    
    def add_custom_link(self, link_data: Dict[str, Any]) -> bool:
        """Add a custom service link"""
        try:
            custom_links = self.config.get("custom_links", [])
            
            # Generate ID if not provided
            if "id" not in link_data:
                link_data["id"] = f"custom_{len(custom_links) + 1}"
            
            # Set default values
            link_data.setdefault("enabled", True)
            link_data.setdefault("order", len(self.config.get("services", [])) + len(custom_links) + 1)
            
            custom_links.append(link_data)
            return self.update_config({"custom_links": custom_links})
        except Exception as e:
            print(f"Error adding custom link: {e}")
            return False
    
    def remove_custom_link(self, link_id: str) -> bool:
        """Remove a custom service link"""
        try:
            custom_links = self.config.get("custom_links", [])
            custom_links = [link for link in custom_links if link.get("id") != link_id]
            return self.update_config({"custom_links": custom_links})
        except Exception as e:
            print(f"Error removing custom link: {e}")
            return False
    
    def update_service(self, service_id: str, updates: Dict[str, Any]) -> bool:
        """Update a specific service configuration"""
        try:
            services = self.config.get("services", [])
            for service in services:
                if service.get("id") == service_id:
                    service.update(updates)
                    return self.update_config({"services": services})
            return False
        except Exception as e:
            print(f"Error updating service: {e}")
            return False
    
    def reorder_services(self, service_order: List[str]) -> bool:
        """Reorder services based on ID list"""
        try:
            services = self.config.get("services", [])
            custom_links = self.config.get("custom_links", [])
            
            # Create a mapping of IDs to items
            all_items = {item["id"]: item for item in services + custom_links}
            
            # Update order based on provided list
            for index, item_id in enumerate(service_order):
                if item_id in all_items:
                    all_items[item_id]["order"] = index + 1
            
            # Separate back into services and custom links
            services = [item for item in all_items.values() if item["id"] in [s["id"] for s in services]]
            custom_links = [item for item in all_items.values() if item["id"] not in [s["id"] for s in services]]
            
            return self.update_config({
                "services": services,
                "custom_links": custom_links
            })
        except Exception as e:
            print(f"Error reordering services: {e}")
            return False
    
    def reset_to_default(self) -> bool:
        """Reset configuration to default"""
        return self.save_config(self.DEFAULT_CONFIG.copy())
    
    def _merge_configs(self, base: Dict, updates: Dict) -> Dict:
        """Deep merge two configuration dictionaries"""
        result = base.copy()
        
        for key, value in updates.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def export_config(self) -> str:
        """Export configuration as JSON string"""
        return json.dumps(self.config, indent=2)
    
    def import_config(self, config_json: str) -> bool:
        """Import configuration from JSON string"""
        try:
            new_config = json.loads(config_json)
            # Validate it has required keys
            if "theme" in new_config and "services" in new_config:
                return self.save_config(new_config)
            return False
        except Exception as e:
            print(f"Error importing config: {e}")
            return False

# Singleton instance
landing_config = LandingPageConfig()