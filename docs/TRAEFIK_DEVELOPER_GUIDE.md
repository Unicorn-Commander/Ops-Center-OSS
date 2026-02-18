# Traefik Configuration Management - Developer Guide

**Version**: 1.0.0
**Epic**: 1.3 - Traefik Configuration Management
**Last Updated**: October 24, 2025
**Target Audience**: Developers contributing to the codebase

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Backend Architecture](#2-backend-architecture)
3. [Frontend Architecture](#3-frontend-architecture)
4. [Development Environment](#4-development-environment)
5. [Code Structure](#5-code-structure)
6. [Extending Functionality](#6-extending-functionality)
7. [Testing Guidelines](#7-testing-guidelines)
8. [Deployment](#8-deployment)

---

## 1. Architecture Overview

### 1.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface (React)                    │
│             TraefikConfig.jsx (1540 lines)                   │
│   4 Tabs: Certificates, Routes, Middleware, Configuration   │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP REST API
                      │ (JSON over HTTPS)
┌─────────────────────▼───────────────────────────────────────┐
│                FastAPI Backend (Python)                      │
│                  traefik_api.py (171 lines)                  │
│   - Route: /api/v1/traefik/*                                │
│   - Auth: Keycloak JWT validation                           │
│   - Handlers: Route to TraefikManager                       │
└─────────────────────┬───────────────────────────────────────┘
                      │ Python Method Calls
┌─────────────────────▼───────────────────────────────────────┐
│              TraefikManager (Business Logic)                 │
│              traefik_manager.py (2022 lines)                 │
│   - Certificate management (Let's Encrypt)                  │
│   - Route management (CRUD operations)                      │
│   - Middleware management                                   │
│   - Configuration validation                                │
│   - Backup/restore                                          │
│   - Audit logging                                           │
│   - Rate limiting                                           │
└─────────────────────┬───────────────────────────────────────┘
                      │ File I/O Operations
┌─────────────────────▼───────────────────────────────────────┐
│              Traefik Configuration Files                     │
│   - traefik.yml (static config)                             │
│   - dynamic/*.yml (routes, middleware, services)            │
│   - acme.json (SSL certificates)                            │
│   - backups/ (timestamped configuration backups)            │
└─────────────────────────────────────────────────────────────┘
                      │ Auto-reload (file watcher)
┌─────────────────────▼───────────────────────────────────────┐
│                   Traefik Container                          │
│   - Monitors /traefik/ directory for changes                │
│   - Reloads configuration within 1-2 seconds                │
│   - Applies new routes, middleware, certificates            │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 Data Flow

#### Certificate Request Flow
```
User → TraefikConfig.jsx → POST /api/v1/traefik/certificates
  ↓
traefik_api.py validates JWT token
  ↓
traefik_manager.request_certificate()
  ├─ Validate domain format
  ├─ Check rate limit
  ├─ Update traefik.yml with ACME email
  ├─ Create temporary route for HTTP-01 challenge
  ├─ Save configuration
  └─ Return "pending" status
  ↓
Traefik detects configuration change
  ↓
Traefik requests certificate from Let's Encrypt
  ↓
Let's Encrypt validates domain ownership (HTTP-01)
  ↓
Certificate issued and stored in acme.json
```

#### Route Creation Flow
```
User → TraefikConfig.jsx → POST /api/v1/traefik/routes
  ↓
traefik_api.py validates JWT token
  ↓
traefik_manager.create_route()
  ├─ Validate input with Pydantic model
  ├─ Check rate limit (5 changes/minute)
  ├─ Create automatic backup
  ├─ Load routes.yml
  ├─ Add new route to YAML structure
  ├─ Validate complete configuration
  ├─ Write routes.yml
  ├─ Reload Traefik (Docker healthcheck)
  ├─ Log to audit trail
  └─ Return success with backup path
  ↓
Traefik detects routes.yml change
  ↓
Traefik reloads routes (graceful, no downtime)
```

### 1.3 Technology Stack

**Backend**:
- Python 3.10+
- FastAPI 0.104+
- Pydantic 2.x (data validation)
- PyYAML (YAML parsing)
- bcrypt (password hashing for Basic Auth)

**Frontend**:
- React 18
- Material-UI (MUI) v5
- React Router v6
- Axios (HTTP client)

**Infrastructure**:
- Docker (Traefik container)
- File-based configuration (YAML)
- Let's Encrypt (ACME protocol)

---

## 2. Backend Architecture

### 2.1 Module Structure

```
backend/
├── traefik_manager.py        # Core business logic (2022 lines)
│   ├── TraefikManager         # Main manager class
│   ├── AuditLogger            # Change tracking
│   ├── RateLimiter            # Rate limiting
│   ├── ConfigValidator        # YAML validation
│   ├── Custom exceptions      # TraefikError, RouteError, etc.
│   ├── Pydantic models        # RouteCreate, MiddlewareCreate, etc.
│   └── Helper functions       # get_traefik_status()
│
└── traefik_api.py            # FastAPI endpoints (171 lines)
    ├── router                 # APIRouter instance
    ├── traefik_manager        # TraefikManager singleton
    ├── Health endpoints       # /health, /status
    ├── Certificate endpoints  # /certificates, /certificates/{domain}
    ├── Route endpoints        # /routes, /routes/{name}
    ├── Middleware endpoints   # /middleware, /middleware/{name}
    └── Config endpoints       # /config, /backups, /reload
```

### 2.2 TraefikManager Class

**File**: `backend/traefik_manager.py`

**Key Methods**:

#### Certificate Management
```python
def list_certificates(self) -> List[Dict[str, Any]]:
    """List all SSL certificates from acme.json"""
    # Reads /traefik/acme/acme.json
    # Parses ACME data structure
    # Returns list of certificate info

def request_certificate(
    self,
    domain: str,
    email: str,
    sans: List[str] = None,
    username: str = "system"
) -> Dict[str, Any]:
    """Request new SSL certificate from Let's Encrypt"""
    # Validates input with CertificateRequest Pydantic model
    # Checks rate limit (5 changes/minute)
    # Updates traefik.yml with ACME email
    # Creates route to trigger HTTP-01 challenge
    # Logs to audit trail
    # Returns pending status

def revoke_certificate(
    self,
    domain: str,
    username: str = "system"
) -> Dict[str, Any]:
    """Revoke SSL certificate (remove from acme.json)"""
    # Removes certificate from ACME data
    # Writes updated acme.json
    # Logs to audit trail
```

#### Route Management
```python
def list_routes(
    self,
    config_file: str = None
) -> List[Dict[str, Any]]:
    """List all HTTP routes"""
    # Reads dynamic/*.yml files
    # Extracts router configurations
    # Returns standardized route info

def create_route(
    self,
    name: str,
    rule: str,
    service: str,
    entrypoints: List[str] = None,
    middlewares: List[str] = None,
    priority: int = 0,
    tls_enabled: bool = True,
    cert_resolver: str = "letsencrypt",
    username: str = "system"
) -> Dict[str, Any]:
    """Create new route"""
    # Validates input with RouteCreate Pydantic model
    # Checks rate limit
    # Creates automatic backup
    # Loads routes.yml
    # Adds route to config
    # Validates complete config
    # Saves routes.yml
    # Reloads Traefik
    # Logs to audit trail
    # Returns success with backup path

def update_route(
    self,
    name: str,
    updates: Dict[str, Any],
    username: str = "system"
) -> Dict[str, Any]:
    """Update existing route"""
    # Similar flow to create_route
    # Merges updates into existing route

def delete_route(
    self,
    name: str,
    username: str = "system"
) -> Dict[str, Any]:
    """Delete route"""
    # Creates backup
    # Removes route from config
    # Saves and reloads
```

#### Middleware Management
```python
def list_middleware(
    self,
    config_file: str = None
) -> List[Dict[str, Any]]:
    """List all middleware"""

def create_middleware(
    self,
    name: str,
    type: str,
    config: Dict[str, Any],
    username: str = "system"
) -> Dict[str, Any]:
    """Create new middleware"""
    # Validates with MiddlewareCreate Pydantic model
    # Type-specific config validation

def update_middleware(
    self,
    name: str,
    config: Dict[str, Any],
    username: str = "system"
) -> Dict[str, Any]:
    """Update middleware"""

def delete_middleware(
    self,
    name: str,
    username: str = "system"
) -> Dict[str, Any]:
    """Delete middleware"""
```

#### Configuration Management
```python
def get_config(self) -> Dict[str, Any]:
    """Read current traefik.yml"""

def update_config(
    self,
    updates: Dict[str, Any],
    username: str = "system"
) -> Dict[str, Any]:
    """Update traefik.yml"""
    # Deep merges updates
    # Validates YAML
    # Creates backup
    # Saves config

def validate_config(
    self,
    config: Dict[str, Any] = None
) -> bool:
    """Validate Traefik configuration"""
    # YAML syntax validation
    # Traefik structure validation

def backup_config(self) -> str:
    """Create timestamped backup"""
    # Copies traefik.yml, dynamic/*.yml, acme.json
    # Creates manifest.json
    # Returns backup path
    # Cleans up old backups (keeps last 10)

def restore_config(
    self,
    backup_path: str,
    username: str = "system"
) -> Dict[str, Any]:
    """Restore from backup"""
    # Creates safety backup first
    # Restores all files from backup
    # Reloads Traefik

def reload_traefik(self) -> Dict[str, Any]:
    """Trigger Traefik reload"""
    # Runs Docker healthcheck
    # Returns status
```

### 2.3 Pydantic Models

**Input Validation Models**:

```python
class RouteCreate(BaseModel):
    """Validated model for creating routes"""
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        pattern=r"^[a-z0-9-]+$",
        description="Route name (lowercase, alphanumeric, hyphens)"
    )
    rule: str = Field(
        ...,
        min_length=5,
        max_length=500,
        description="Traefik routing rule"
    )
    service: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Backend service name"
    )
    entrypoints: List[EntryPoint] = Field(
        default=[EntryPoint.WEBSECURE],
        description="Entry points"
    )
    middlewares: List[str] = Field(
        default_factory=list,
        description="Middleware names"
    )
    priority: int = Field(
        default=0,
        ge=0,
        le=1000,
        description="Route priority"
    )
    tls_enabled: bool = Field(
        default=True,
        description="Enable TLS/SSL"
    )
    cert_resolver: str = Field(
        default="letsencrypt",
        description="Certificate resolver"
    )

    @field_validator('rule')
    @classmethod
    def validate_rule_syntax(cls, v):
        """Validate Traefik rule syntax"""
        valid_patterns = [
            r'Host\(`[^`]+`\)',
            r'PathPrefix\(`[^`]+`\)',
            r'Path\(`[^`]+`\)',
            r'Method\(`[^`]+`\)',
            r'Headers\(`[^`]+`,\s*`[^`]+`\)',
        ]
        has_valid = any(re.search(pattern, v) for pattern in valid_patterns)
        if not has_valid:
            raise ValueError(f"Invalid Traefik rule syntax: {v}")
        return v
```

```python
class MiddlewareCreate(BaseModel):
    """Validated model for creating middleware"""
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        pattern=r"^[a-z0-9-]+$"
    )
    type: MiddlewareType = Field(...)
    config: Dict[str, Any] = Field(...)

    @field_validator('config')
    @classmethod
    def validate_config_structure(cls, v, info):
        """Type-specific validation"""
        middleware_type = info.data.get('type')

        if middleware_type == MiddlewareType.RATE_LIMIT:
            required = ['average', 'period']
            if not all(k in v for k in required):
                raise ValueError(f"RateLimit requires: {required}")
        # ... more type-specific validation
```

```python
class CertificateRequest(BaseModel):
    """Validated model for certificate requests"""
    domain: str = Field(
        ...,
        min_length=3,
        max_length=253
    )
    email: str = Field(...)
    sans: List[str] = Field(default_factory=list)

    @field_validator('domain')
    @classmethod
    def validate_domain(cls, v):
        """Validate RFC 1035 domain format"""
        v = v.lower().strip()
        pattern = r'^(?!-)([a-z0-9-]{1,63}(?<!-)\.)+[a-z]{2,}$'
        if not re.match(pattern, v):
            raise ValueError(f"Invalid domain: {v}")
        return v
```

### 2.4 Custom Exceptions

```python
class TraefikError(Exception):
    """Base exception for Traefik operations"""
    pass

class ConfigValidationError(TraefikError):
    """Configuration validation failed"""
    pass

class CertificateError(TraefikError):
    """Certificate operation failed"""
    pass

class RouteError(TraefikError):
    """Route operation failed"""
    pass

class MiddlewareError(TraefikError):
    """Middleware operation failed"""
    pass

class BackupError(TraefikError):
    """Backup/restore operation failed"""
    pass

class RateLimitExceeded(TraefikError):
    """Rate limit exceeded for configuration changes"""
    pass
```

### 2.5 Audit Logging

**Class**: `AuditLogger`

**Purpose**: Track all configuration changes for security and compliance.

```python
class AuditLogger:
    def __init__(self, log_file: str = None):
        self.log_file = log_file or "/var/log/traefik_audit.log"
        self._ensure_log_file()

    def log_change(
        self,
        action: str,
        details: Dict[str, Any],
        username: str,
        success: bool = True,
        error: str = None
    ):
        """Log configuration change"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "user": username,
            "success": success,
            "details": details,
            "error": error
        }
        # Write to file (JSON per line)
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
        # Also log to standard logger
        logger.info(f"TRAEFIK_AUDIT: {action} by {username}")
```

**Log Format**:
```json
{
  "timestamp": "2025-10-24T14:30:00.123456Z",
  "action": "create_route",
  "user": "admin@unicorncommander.ai",
  "success": true,
  "details": {
    "name": "api-route",
    "rule": "Host(`api.example.com`)",
    "service": "api-svc",
    "backup": "/traefik/backups/traefik_backup_20251024_143000"
  },
  "error": null
}
```

### 2.6 Rate Limiting

**Class**: `RateLimiter`

**Purpose**: Prevent abuse by limiting configuration changes per user.

```python
class RateLimiter:
    def __init__(
        self,
        max_changes: int = 5,
        window_seconds: int = 60
    ):
        self.max_changes = max_changes
        self.window_seconds = window_seconds
        self.changes = defaultdict(list)  # username -> [timestamps]

    def check_limit(self, username: str) -> Tuple[bool, int]:
        """Check if user exceeded rate limit"""
        now = time.time()
        cutoff = now - self.window_seconds

        # Remove old timestamps
        self.changes[username] = [
            ts for ts in self.changes[username] if ts > cutoff
        ]

        # Check limit
        current_count = len(self.changes[username])
        if current_count >= self.max_changes:
            raise RateLimitExceeded(
                f"Rate limit exceeded: {current_count}/{self.max_changes} "
                f"changes in {self.window_seconds}s"
            )

        # Record this change
        self.changes[username].append(now)
        return True, self.max_changes - current_count - 1
```

**Usage**:
```python
# In TraefikManager methods
def create_route(self, name, rule, service, username="system"):
    # Check rate limit before processing
    self.rate_limiter.check_limit(username)
    # ... continue with route creation
```

### 2.7 Configuration Validation

**Class**: `ConfigValidator`

**Purpose**: Ensure YAML syntax and Traefik structure are valid before saving.

```python
class ConfigValidator:
    @staticmethod
    def validate_yaml(content: str) -> Dict[str, Any]:
        """Validate YAML syntax"""
        try:
            return yaml.safe_load(content)
        except yaml.YAMLError as e:
            raise ConfigValidationError(f"Invalid YAML: {e}")

    @staticmethod
    def validate_traefik_config(config: Dict[str, Any]) -> bool:
        """Validate Traefik structure"""
        # Check top-level keys
        valid_keys = {'http', 'tcp', 'udp', 'tls'}
        if not any(key in config for key in valid_keys):
            raise ConfigValidationError(
                f"Config must contain one of: {valid_keys}"
            )

        # Validate HTTP section
        if 'http' in config:
            http = config['http']

            # Validate routers
            if 'routers' in http:
                for name, router in http['routers'].items():
                    if 'rule' not in router:
                        raise ConfigValidationError(
                            f"Router '{name}' missing 'rule'"
                        )
                    if 'service' not in router:
                        raise ConfigValidationError(
                            f"Router '{name}' missing 'service'"
                        )

            # Validate services
            if 'services' in http:
                for name, service in http['services'].items():
                    if 'loadBalancer' not in service:
                        raise ConfigValidationError(
                            f"Service '{name}' missing 'loadBalancer'"
                        )
                    lb = service['loadBalancer']
                    if 'servers' not in lb or not lb['servers']:
                        raise ConfigValidationError(
                            f"Service '{name}' has no servers'"
                        )

        return True
```

---

## 3. Frontend Architecture

### 3.1 Component Structure

**File**: `src/pages/TraefikConfig.jsx` (1540 lines)

**Component Hierarchy**:
```
TraefikConfig (Main Component)
├── Tabs (MUI Tabs)
│   ├── SSL Certificates Tab
│   ├── Routes Tab
│   ├── Middleware Tab
│   └── Configuration Tab
│
├── Certificate Management
│   ├── Certificate Status Card
│   ├── Certificates Table
│   ├── Request Certificate Dialog
│   └── Revoke Certificate Dialog
│
├── Route Management
│   ├── Actions Bar (Add, Refresh, Search)
│   ├── Routes Table
│   ├── Add/Edit Route Dialog
│   └── Delete Route Dialog
│
├── Middleware Management
│   ├── Actions Bar (Add, Refresh)
│   ├── Middleware Table
│   ├── Add/Edit Middleware Dialog
│   └── Delete Middleware Dialog
│
└── Configuration Management
    ├── Actions Bar (Edit, Backup, Restore, Reload)
    ├── Config Display/Editor
    ├── Recent Backups List
    └── Restore Backup Dialog
```

### 3.2 State Management

**React Hooks Used**:

```javascript
// Tab state
const [activeTab, setActiveTab] = useState(0);

// Global state
const [loading, setLoading] = useState(true);
const [toast, setToast] = useState({ open: false, message: '', severity: 'success' });

// Certificate state
const [certificates, setCertificates] = useState([]);
const [certPage, setCertPage] = useState(0);
const [certRowsPerPage, setCertRowsPerPage] = useState(10);
const [certDialogOpen, setCertDialogOpen] = useState(false);
const [selectedCert, setSelectedCert] = useState(null);
const [newCert, setNewCert] = useState({ domain: '', email: '' });

// Route state
const [routes, setRoutes] = useState([]);
const [routePage, setRoutePage] = useState(0);
const [routeDialogOpen, setRouteDialogOpen] = useState(false);
const [routeEditMode, setRouteEditMode] = useState(false);
const [selectedRoute, setSelectedRoute] = useState(null);
const [newRoute, setNewRoute] = useState({
  name: '',
  rule: '',
  service: '',
  middleware: []
});
const [routeSearchQuery, setRouteSearchQuery] = useState('');

// Middleware state
const [middleware, setMiddleware] = useState([]);
const [middlewareDialogOpen, setMiddlewareDialogOpen] = useState(false);
const [newMiddleware, setNewMiddleware] = useState({
  name: '',
  type: 'basicAuth',
  config: {}
});

// Configuration state
const [config, setConfig] = useState('');
const [configEditing, setConfigEditing] = useState(false);
const [editedConfig, setEditedConfig] = useState('');
const [backups, setBackups] = useState([]);
```

### 3.3 Data Fetching

**Auto-refresh Pattern**:
```javascript
// Auto-refresh every 60 seconds
useEffect(() => {
  const interval = setInterval(() => {
    if (activeTab === 0) fetchCertificates();
    if (activeTab === 1) fetchRoutes();
    if (activeTab === 2) fetchMiddleware();
    if (activeTab === 3) fetchConfig();
  }, 60000);

  return () => clearInterval(interval);
}, [activeTab]);

// Fetch on tab change
useEffect(() => {
  if (activeTab === 0) fetchCertificates();
  if (activeTab === 1) fetchRoutes();
  // ...
}, [activeTab]);
```

**Fetch Functions**:
```javascript
const fetchCertificates = async () => {
  try {
    setLoading(true);
    const response = await fetch('/api/v1/traefik/certificates', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('authToken')}`
      },
      credentials: 'include',
    });

    if (!response.ok) throw new Error('Failed to fetch certificates');

    const data = await response.json();
    setCertificates(data.certificates || []);
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    setLoading(false);
  }
};
```

### 3.4 Form Handling

**Create Route Example**:
```javascript
const handleSaveRoute = async () => {
  try {
    const url = routeEditMode
      ? `/api/v1/traefik/routes/${selectedRoute.name}`
      : '/api/v1/traefik/routes';

    const method = routeEditMode ? 'PUT' : 'POST';

    const response = await fetch(url, {
      method,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('authToken')}`
      },
      credentials: 'include',
      body: JSON.stringify(newRoute),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to save route');
    }

    showToast(`Route ${routeEditMode ? 'updated' : 'created'} successfully`);
    setRouteDialogOpen(false);
    setRouteEditMode(false);
    setNewRoute({ name: '', rule: '', service: '', middleware: [] });
    fetchRoutes(); // Refresh list
  } catch (err) {
    showToast(err.message, 'error');
  }
};
```

### 3.5 UI Components

**Material-UI Components Used**:
- `Box`, `Card`, `Paper`: Layout containers
- `Typography`: Text elements
- `Tabs`, `Tab`: Tab navigation
- `Table`, `TableBody`, `TableCell`, `TableHead`, `TableRow`: Data tables
- `Dialog`, `DialogTitle`, `DialogContent`, `DialogActions`: Modal dialogs
- `TextField`, `Select`, `MenuItem`: Form inputs
- `Button`, `IconButton`: Actions
- `Chip`: Tags/labels
- `Alert`, `Snackbar`: Notifications
- `CircularProgress`: Loading indicator
- `Tooltip`: Hover information

**Theme Integration**:
```javascript
import { useTheme } from '../contexts/ThemeContext';

const TraefikConfig = () => {
  const { currentTheme } = useTheme();

  // Apply theme-specific styling
  <Button
    sx={{
      background: currentTheme === 'unicorn'
        ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
        : 'linear-gradient(135deg, #3b82f6 0%, #1e40af 100%)',
    }}
  >
    Add Route
  </Button>
};
```

### 3.6 Error Handling

**Toast Notification Pattern**:
```javascript
const showToast = (message, severity = 'success') => {
  setToast({ open: true, message, severity });
};

// Usage in async functions
try {
  // ... API call
  showToast('Route created successfully', 'success');
} catch (err) {
  showToast(err.message, 'error');
}

// Toast component
<Snackbar
  open={toast.open}
  autoHideDuration={6000}
  onClose={() => setToast({ ...toast, open: false })}
  anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
>
  <Alert
    onClose={() => setToast({ ...toast, open: false })}
    severity={toast.severity}
  >
    {toast.message}
  </Alert>
</Snackbar>
```

---

## 4. Development Environment

### 4.1 Prerequisites

**System Requirements**:
- Docker & Docker Compose
- Node.js 18+ & npm
- Python 3.10+
- Git

**Services Required**:
- Traefik container running
- PostgreSQL (for Ops-Center)
- Redis (for Ops-Center)
- Keycloak (for authentication)

### 4.2 Local Setup

**Clone Repository**:
```bash
cd /opt/ops-center
```

**Backend Setup**:
```bash
# Python dependencies already installed in Docker image
# For local development:
pip install fastapi pydantic pyyaml bcrypt

# Check Python modules
python3 -c "import traefik_manager; print('OK')"
```

**Frontend Setup**:
```bash
# Install dependencies
npm install

# Dependencies used by TraefikConfig:
# - @mui/material
# - @mui/icons-material
# - react
# - react-router-dom

# Start development server (optional)
npm run dev
# Runs on http://localhost:5173
```

### 4.3 Running Locally

**Start Ops-Center Container**:
```bash
cd /opt/ops-center
docker compose -f docker-compose.direct.yml up -d
```

**Frontend Development**:
```bash
# Option 1: Development server (hot reload)
npm run dev
# Access at: http://localhost:5173/admin/system/traefik

# Option 2: Build and deploy
npm run build
cp -r dist/* public/
docker restart ops-center-direct
# Access at: http://localhost:8084/admin/system/traefik
```

**Backend Development**:
```bash
# Edit backend files
vim backend/traefik_manager.py
vim backend/traefik_api.py

# Restart to load changes
docker restart ops-center-direct

# View logs
docker logs ops-center-direct -f
```

### 4.4 Testing Changes

**Test API Endpoints**:
```bash
# Get JWT token (from browser localStorage or Keycloak)
export TOKEN="eyJhbGciOiJSUzI1NiIsInR5cCI..."

# Test health
curl http://localhost:8084/api/v1/traefik/health

# Test routes list
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8084/api/v1/traefik/routes

# Test route creation
curl -X POST http://localhost:8084/api/v1/traefik/routes \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test-route",
    "rule": "Host(`test.example.com`)",
    "service": "test-svc"
  }'
```

**Test UI**:
1. Open browser: http://localhost:8084/admin/system/traefik
2. Login via Keycloak SSO
3. Test each tab:
   - SSL Certificates: View, Request, Revoke
   - Routes: List, Create, Edit, Delete, Search
   - Middleware: List, Create, Edit, Delete
   - Configuration: View, Edit, Validate, Backup, Restore

### 4.5 Debugging

**Backend Debugging**:
```bash
# Enable debug logging in traefik_manager.py
logging.basicConfig(level=logging.DEBUG)

# Add print statements
print(f"DEBUG: Route data: {route_data}")

# Check logs
docker logs ops-center-direct --tail 100 -f | grep -i traefik
```

**Frontend Debugging**:
```javascript
// Add console.log statements
console.log('Route data:', newRoute);
console.log('API response:', data);

// Check browser console
// F12 → Console tab

// Check network requests
// F12 → Network tab → Filter: XHR
```

**Traefik Debugging**:
```bash
# Check Traefik logs
docker logs traefik --tail 100 -f

# Check configuration files
cat /opt/uc-cloud/traefik/dynamic/routes.yml

# Check ACME data
cat /opt/uc-cloud/traefik/acme/acme.json | jq
```

---

## 5. Code Structure

### 5.1 Backend Files

**traefik_manager.py** (2022 lines):
```
Lines 1-110:    Imports, logging, custom exceptions, enums
Lines 111-229:  Pydantic models (RouteCreate, MiddlewareCreate, CertificateRequest)
Lines 230-303:  AuditLogger class
Lines 304-359:  RateLimiter class
Lines 360-450:  ConfigValidator class
Lines 451-505:  TraefikManager.__init__
Lines 506-812:  Certificate management methods
Lines 813-1206: Route management methods
Lines 1207-1549: Middleware management methods
Lines 1550-1870: Configuration management methods
Lines 1871-1904: Helper methods
Lines 1905-2022: Module-level functions and test code
```

**traefik_api.py** (171 lines):
```
Lines 1-29:     Imports, router setup, traefik_manager init
Lines 30-55:    Pydantic request models (simplified)
Lines 56-86:    Health & status endpoints
Lines 87-116:   Route endpoints (stub implementations)
Lines 117-148:  Certificate endpoints
Lines 149-170:  Configuration endpoints
```

### 5.2 Frontend Files

**TraefikConfig.jsx** (1540 lines):
```
Lines 1-63:     Imports (React, MUI components, icons)
Lines 64-87:    Component setup, state initialization
Lines 88-179:   Certificate state, fetching, handlers
Lines 180-315:  Route state, fetching, handlers
Lines 316-428:  Middleware state, fetching, handlers
Lines 429-585:  Configuration state, fetching, handlers
Lines 586-732:  Certificate tab render function
Lines 733-875:  Routes tab render function
Lines 876-1003: Middleware tab render function
Lines 1004-1161: Configuration tab render function
Lines 1162-1219: Main component render (tabs)
Lines 1220-1540: Dialog components (modals)
```

### 5.3 Configuration Files

**Traefik Directory Structure**:
```
/opt/uc-cloud/traefik/
├── traefik.yml               # Static configuration
├── dynamic/
│   ├── routes.yml           # HTTP routers
│   ├── middleware.yml       # Middleware definitions
│   └── services.yml         # Backend services (optional)
├── acme/
│   └── acme.json            # SSL certificates (600 permissions)
└── backups/
    ├── traefik_backup_20251024_143000/
    │   ├── traefik.yml
    │   ├── dynamic/
    │   │   ├── routes.yml
    │   │   └── middleware.yml
    │   ├── acme.json
    │   └── manifest.json
    └── traefik_backup_20251024_153000/
        └── ...
```

**Example routes.yml**:
```yaml
http:
  routers:
    ops-center:
      rule: Host(`unicorncommander.ai`)
      service: ops-center-svc
      entryPoints:
        - websecure
      middlewares:
        - rate-limit
      priority: 100
      tls:
        certResolver: letsencrypt

  services:
    ops-center-svc:
      loadBalancer:
        servers:
          - url: http://ops-center-direct:8084

  middlewares:
    rate-limit:
      rateLimit:
        average: 100
        period: 1m
        burst: 50
```

---

## 6. Extending Functionality

### 6.1 Adding a New Middleware Type

**Step 1: Update Enum** (`traefik_manager.py`):
```python
class MiddlewareType(str, Enum):
    RATE_LIMIT = "rateLimit"
    # ... existing types ...
    RETRY = "retry"  # New type
```

**Step 2: Add Validation** (`MiddlewareCreate.validate_config_structure`):
```python
@field_validator('config')
@classmethod
def validate_config_structure(cls, v, info):
    # ... existing validation ...

    elif middleware_type == MiddlewareType.RETRY:
        required = ['attempts', 'initialInterval']
        if not all(k in v for k in required):
            raise ValueError(f"Retry middleware requires: {required}")
        if not isinstance(v.get('attempts'), int) or v['attempts'] <= 0:
            raise ValueError("Retry 'attempts' must be positive integer")
```

**Step 3: Update Frontend** (`TraefikConfig.jsx`):
```javascript
const middlewareTypes = [
  // ... existing types ...
  { value: 'retry', label: 'Retry' },
];
```

**Step 4: Add Documentation**:
- Update User Guide with retry middleware examples
- Update API Reference with retry config structure

### 6.2 Adding a New API Endpoint

**Step 1: Add Backend Endpoint** (`traefik_api.py`):
```python
@router.get("/routes/{name}/health")
async def check_route_health(name: str):
    """Check if a route's backend service is healthy"""
    try:
        route = traefik_manager.get_route(name)
        # Implement health check logic
        return {"healthy": True, "route": name}
    except RouteError as e:
        raise HTTPException(status_code=404, detail=str(e))
```

**Step 2: Implement Manager Method** (`traefik_manager.py`):
```python
def get_route(self, name: str) -> Dict[str, Any]:
    """Get a specific route by name"""
    routes = self.list_routes()
    for route in routes:
        if route['name'] == name:
            return route
    raise RouteError(f"Route '{name}' not found")
```

**Step 3: Update Frontend** (`TraefikConfig.jsx`):
```javascript
const checkRouteHealth = async (routeName) => {
  try {
    const response = await fetch(
      `/api/v1/traefik/routes/${routeName}/health`,
      {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        }
      }
    );
    const data = await response.json();
    showToast(
      data.healthy ? 'Route is healthy' : 'Route is unhealthy',
      data.healthy ? 'success' : 'warning'
    );
  } catch (err) {
    showToast(err.message, 'error');
  }
};

// Add button to routes table
<IconButton onClick={() => checkRouteHealth(route.name)}>
  <HealthIcon />
</IconButton>
```

**Step 4: Add Tests** (see Testing section)

### 6.3 Adding Client-Side Filtering

**Add Filter State**:
```javascript
const [filters, setFilters] = useState({
  status: 'all', // all, active, expired
  domain: '',
});
```

**Filter Function**:
```javascript
const filteredCertificates = certificates.filter(cert => {
  // Filter by status
  if (filters.status !== 'all') {
    const status = getCertStatus(cert);
    if (status.label.toLowerCase() !== filters.status) {
      return false;
    }
  }

  // Filter by domain
  if (filters.domain) {
    if (!cert.domain.toLowerCase().includes(filters.domain.toLowerCase())) {
      return false;
    }
  }

  return true;
});
```

**Filter UI**:
```jsx
<Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
  <FormControl size="small" sx={{ minWidth: 150 }}>
    <InputLabel>Status</InputLabel>
    <Select
      value={filters.status}
      onChange={(e) => setFilters({ ...filters, status: e.target.value })}
    >
      <MenuItem value="all">All</MenuItem>
      <MenuItem value="active">Active</MenuItem>
      <MenuItem value="expired">Expired</MenuItem>
    </Select>
  </FormControl>

  <TextField
    size="small"
    placeholder="Filter by domain"
    value={filters.domain}
    onChange={(e) => setFilters({ ...filters, domain: e.target.value })}
  />
</Box>
```

### 6.4 Adding Bulk Operations

**Backend Implementation**:
```python
@router.post("/routes/bulk-delete")
async def bulk_delete_routes(route_names: List[str]):
    """Delete multiple routes at once"""
    results = []
    for name in route_names:
        try:
            result = traefik_manager.delete_route(name, username="bulk")
            results.append({"name": name, "success": True})
        except RouteError as e:
            results.append({"name": name, "success": False, "error": str(e)})

    return {"results": results}
```

**Frontend Implementation**:
```javascript
const [selectedRoutes, setSelectedRoutes] = useState([]);

const handleBulkDelete = async () => {
  try {
    const response = await fetch('/api/v1/traefik/routes/bulk-delete', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('authToken')}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(selectedRoutes)
    });

    const data = await response.json();
    const succeeded = data.results.filter(r => r.success).length;
    showToast(`Deleted ${succeeded} routes successfully`);
    fetchRoutes();
  } catch (err) {
    showToast(err.message, 'error');
  }
};

// Add checkboxes to table
<TableCell>
  <Checkbox
    checked={selectedRoutes.includes(route.name)}
    onChange={(e) => {
      if (e.target.checked) {
        setSelectedRoutes([...selectedRoutes, route.name]);
      } else {
        setSelectedRoutes(selectedRoutes.filter(n => n !== route.name));
      }
    }}
  />
</TableCell>
```

---

## 7. Testing Guidelines

### 7.1 Backend Unit Tests

**File**: `backend/tests/test_traefik_manager.py`

**Example Test**:
```python
import pytest
from traefik_manager import TraefikManager, RouteError, RateLimitExceeded

@pytest.fixture
def manager():
    """Create TraefikManager instance for testing"""
    return TraefikManager(
        traefik_dir="/tmp/test_traefik",
        docker_container="test-traefik"
    )

def test_create_route_validates_name(manager):
    """Test route name validation"""
    with pytest.raises(RouteError) as exc:
        manager.create_route(
            name="Invalid Name with Spaces",
            rule="Host(`example.com`)",
            service="test-svc"
        )
    assert "lowercase alphanumeric" in str(exc.value)

def test_rate_limit_enforced(manager):
    """Test rate limiting"""
    # Make 5 changes (limit)
    for i in range(5):
        manager.create_route(
            name=f"route-{i}",
            rule=f"Host(`test{i}.example.com`)",
            service="test-svc",
            username="testuser"
        )

    # 6th change should be rate limited
    with pytest.raises(RateLimitExceeded):
        manager.create_route(
            name="route-6",
            rule="Host(`test6.example.com`)",
            service="test-svc",
            username="testuser"
        )

def test_backup_and_restore(manager):
    """Test backup/restore functionality"""
    # Create a route
    manager.create_route(
        name="test-route",
        rule="Host(`test.example.com`)",
        service="test-svc"
    )

    # Create backup
    backup_path = manager.backup_config()
    assert backup_path.startswith("/tmp/test_traefik/backups/")

    # Delete route
    manager.delete_route("test-route")

    # Restore backup
    result = manager.restore_config(backup_path)
    assert result['success'] is True

    # Route should exist again
    routes = manager.list_routes()
    assert any(r['name'] == 'test-route' for r in routes)
```

**Run Tests**:
```bash
cd /opt/ops-center/backend
pytest tests/test_traefik_manager.py -v
```

### 7.2 API Integration Tests

**File**: `backend/tests/test_traefik_api.py`

**Example Test**:
```python
from fastapi.testclient import TestClient
from server import app

client = TestClient(app)

def test_health_endpoint():
    """Test health check endpoint"""
    response = client.get("/api/v1/traefik/health")
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'healthy'
    assert data['epic'] == '1.3'

def test_list_routes_requires_auth():
    """Test authentication is required"""
    response = client.get("/api/v1/traefik/routes")
    assert response.status_code == 401

def test_create_route_validation():
    """Test route creation validation"""
    response = client.post(
        "/api/v1/traefik/routes",
        json={
            "name": "Invalid Name",  # Invalid (spaces)
            "rule": "Host(`example.com`)",
            "service": "test-svc"
        },
        headers={"Authorization": "Bearer test-token"}
    )
    assert response.status_code == 400
    assert "lowercase alphanumeric" in response.json()['detail']
```

### 7.3 Frontend Component Tests

**File**: `src/pages/__tests__/TraefikConfig.test.jsx`

**Example Test** (using React Testing Library):
```javascript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import TraefikConfig from '../TraefikConfig';
import { ThemeProvider } from '../../contexts/ThemeContext';

// Mock fetch
global.fetch = jest.fn();

const mockTheme = {
  currentTheme: 'unicorn'
};

describe('TraefikConfig Component', () => {
  beforeEach(() => {
    fetch.mockClear();
  });

  test('renders tabs correctly', () => {
    render(
      <ThemeProvider value={mockTheme}>
        <TraefikConfig />
      </ThemeProvider>
    );

    expect(screen.getByText('SSL Certificates')).toBeInTheDocument();
    expect(screen.getByText('Routes')).toBeInTheDocument();
    expect(screen.getByText('Middleware')).toBeInTheDocument();
    expect(screen.getByText('Configuration')).toBeInTheDocument();
  });

  test('fetches certificates on mount', async () => {
    fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        certificates: [
          { domain: 'example.com', status: 'active' }
        ]
      })
    });

    render(
      <ThemeProvider value={mockTheme}>
        <TraefikConfig />
      </ThemeProvider>
    );

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledWith(
        '/api/v1/traefik/certificates',
        expect.objectContaining({
          headers: expect.objectContaining({
            'Authorization': expect.stringContaining('Bearer')
          })
        })
      );
    });
  });

  test('opens create route dialog', () => {
    render(
      <ThemeProvider value={mockTheme}>
        <TraefikConfig />
      </ThemeProvider>
    );

    // Switch to Routes tab
    fireEvent.click(screen.getByText('Routes'));

    // Click Add Route button
    fireEvent.click(screen.getByText('Add Route'));

    // Dialog should be visible
    expect(screen.getByText('Add Route')).toBeInTheDocument();
  });
});
```

**Run Tests**:
```bash
cd /opt/ops-center
npm test
```

### 7.4 End-to-End Tests

**File**: `tests/e2e/test_traefik_workflow.py` (Selenium)

**Example Test**:
```python
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_complete_route_creation_workflow():
    """Test complete route creation from UI"""
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 10)

    try:
        # Navigate to Traefik Config
        driver.get("http://localhost:8084/admin/system/traefik")

        # Wait for Keycloak login redirect
        # ... (login flow)

        # Click Routes tab
        routes_tab = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[text()='Routes']"))
        )
        routes_tab.click()

        # Click Add Route button
        add_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[text()='Add Route']"))
        )
        add_button.click()

        # Fill in route form
        name_input = wait.until(
            EC.presence_of_element_located((By.NAME, "name"))
        )
        name_input.send_keys("test-route")

        rule_input = driver.find_element(By.NAME, "rule")
        rule_input.send_keys("Host(`test.example.com`)")

        # Select service
        service_select = driver.find_element(By.NAME, "service")
        service_select.click()
        driver.find_element(By.XPATH, "//li[text()='test-svc']").click()

        # Submit form
        create_button = driver.find_element(By.XPATH, "//button[text()='Create']")
        create_button.click()

        # Wait for success toast
        success_toast = wait.until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'created successfully')]"))
        )
        assert success_toast.is_displayed()

        # Verify route appears in table
        route_row = wait.until(
            EC.presence_of_element_located((By.XPATH, "//td[text()='test-route']"))
        )
        assert route_row.is_displayed()

    finally:
        driver.quit()
```

---

## 8. Deployment

### 8.1 Building for Production

**Frontend Build**:
```bash
cd /opt/ops-center

# Install dependencies (if needed)
npm install

# Build production bundle
npm run build

# Output: dist/ directory
ls -lh dist/

# Copy to public directory
cp -r dist/* public/

# Verify files
ls -lh public/assets/
```

**Backend Build**:
```bash
# Backend is Python - no build step required
# Dependencies installed in Docker image

# Verify modules
python3 -c "import traefik_manager; print('OK')"
python3 -c "import traefik_api; print('OK')"
```

### 8.2 Docker Deployment

**Dockerfile** (already configured):
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ /app/

# Copy frontend build
COPY public/ /app/public/

# Expose port
EXPOSE 8084

# Start FastAPI server
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8084"]
```

**docker-compose.direct.yml** (Ops-Center):
```yaml
services:
  ops-center-direct:
    build: .
    container_name: ops-center-direct
    ports:
      - "8084:8084"
    volumes:
      - /opt/uc-cloud/traefik:/traefik
    networks:
      - unicorn-network
      - web
      - uchub-network
    environment:
      - KEYCLOAK_URL=http://uchub-keycloak:8080
      - KEYCLOAK_REALM=uchub
      - POSTGRES_HOST=unicorn-postgresql
```

**Deploy**:
```bash
cd /opt/ops-center

# Build frontend
npm run build
cp -r dist/* public/

# Rebuild Docker image
docker compose -f docker-compose.direct.yml build

# Restart container
docker compose -f docker-compose.direct.yml up -d

# Verify deployment
docker ps | grep ops-center
docker logs ops-center-direct --tail 50
```

### 8.3 Configuration Files

**Environment Variables** (`.env.auth`):
```env
# Keycloak SSO
KEYCLOAK_URL=http://uchub-keycloak:8080
KEYCLOAK_REALM=uchub
KEYCLOAK_CLIENT_ID=ops-center
KEYCLOAK_CLIENT_SECRET=your-keycloak-client-secret

# Traefik paths (mounted via Docker volume)
TRAEFIK_DIR=/traefik
TRAEFIK_DOCKER_CONTAINER=traefik
```

**Traefik Volume Mount**:
```yaml
volumes:
  - /opt/uc-cloud/traefik:/traefik
```

This allows the Ops-Center container to read/write Traefik configuration files.

### 8.4 Monitoring

**Check Logs**:
```bash
# Ops-Center logs
docker logs ops-center-direct -f

# Filter for Traefik operations
docker logs ops-center-direct | grep -i traefik

# Check audit log
docker exec ops-center-direct cat /var/log/traefik_audit.log | tail -20
```

**Check Metrics**:
```bash
# Check API health
curl http://localhost:8084/api/v1/traefik/health

# Check Traefik status
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8084/api/v1/traefik/status
```

### 8.5 Backup Strategy

**Automatic Backups**:
- Backups created automatically before every configuration change
- Last 10 backups retained (older ones deleted)
- Location: `/opt/uc-cloud/traefik/backups/`

**Manual Backups**:
```bash
# Create backup via API
curl -X POST http://localhost:8084/api/v1/traefik/config/backup \
  -H "Authorization: Bearer $TOKEN"

# Or manually copy files
timestamp=$(date +%Y%m%d_%H%M%S)
backup_dir="/backup/traefik_manual_$timestamp"
mkdir -p "$backup_dir"
cp -r /opt/uc-cloud/traefik/* "$backup_dir/"
```

**Archive Important Backups**:
```bash
# Copy to long-term storage
cp -r /traefik/backups/traefik_backup_20251024_153000 \
      /archive/traefik-backups/
```

### 8.6 Rollback Procedure

**If Deployment Fails**:

1. **Restore previous Docker image**:
```bash
docker compose -f docker-compose.direct.yml down
docker compose -f docker-compose.direct.yml up -d --no-build
```

2. **Restore configuration from backup**:
```bash
# Via API
curl -X POST http://localhost:8084/api/v1/traefik/config/restore/traefik_backup_20251024_153000 \
  -H "Authorization: Bearer $TOKEN"

# Or manually
cp -r /traefik/backups/traefik_backup_20251024_153000/* /traefik/
docker restart traefik
```

3. **Verify services**:
```bash
docker ps | grep -E "ops-center|traefik"
curl http://localhost:8084/api/v1/traefik/health
```

---

## Appendix A: File Locations

```
/opt/uc-cloud/
├── services/ops-center/
│   ├── backend/
│   │   ├── traefik_manager.py        # Core business logic
│   │   ├── traefik_api.py            # FastAPI endpoints
│   │   ├── server.py                 # Main FastAPI app
│   │   └── tests/
│   │       ├── test_traefik_manager.py
│   │       └── test_traefik_api.py
│   │
│   ├── src/
│   │   ├── pages/
│   │   │   ├── TraefikConfig.jsx     # Main UI component
│   │   │   └── __tests__/
│   │   │       └── TraefikConfig.test.jsx
│   │   └── contexts/
│   │       └── ThemeContext.jsx
│   │
│   ├── public/                       # Built frontend assets
│   ├── docs/
│   │   ├── TRAEFIK_USER_GUIDE.md
│   │   ├── TRAEFIK_API_REFERENCE.md
│   │   └── TRAEFIK_DEVELOPER_GUIDE.md  # This file
│   │
│   ├── docker-compose.direct.yml
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.js
│   └── .env.auth
│
└── traefik/                          # Traefik configuration
    ├── traefik.yml
    ├── dynamic/
    │   ├── routes.yml
    │   ├── middleware.yml
    │   └── services.yml
    ├── acme/
    │   └── acme.json
    └── backups/
        └── traefik_backup_*/
```

---

## Appendix B: Common Code Patterns

### Pattern 1: CRUD Operation with Backup
```python
def create_entity(self, data, username="system"):
    # Check rate limit
    self.rate_limiter.check_limit(username)

    # Validate input
    validated_data = EntityModel(**data)

    try:
        # Create backup
        backup_file = self.backup_config()

        # Load config
        config = self.load_config()

        # Add entity
        config['entities'][validated_data.name] = validated_data.dict()

        # Validate complete config
        self.validator.validate_traefik_config(config)

        # Save config
        self.save_config(config)

        # Reload Traefik
        self.reload_traefik()

        # Log success
        self.audit_logger.log_change(
            action="create_entity",
            details=validated_data.dict(),
            username=username,
            success=True
        )

        return {
            'success': True,
            'entity': validated_data.dict(),
            'backup': backup_file
        }

    except Exception as e:
        # Log failure
        self.audit_logger.log_change(
            action="create_entity",
            details=data,
            username=username,
            success=False,
            error=str(e)
        )

        # Rollback
        if 'backup_file' in locals():
            self.restore_config(backup_file, username=username)

        raise
```

### Pattern 2: React State Management
```javascript
// State for entity management
const [entities, setEntities] = useState([]);
const [loading, setLoading] = useState(false);
const [dialogOpen, setDialogOpen] = useState(false);
const [editMode, setEditMode] = useState(false);
const [selectedEntity, setSelectedEntity] = useState(null);
const [newEntity, setNewEntity] = useState({ name: '', value: '' });

// Fetch entities
const fetchEntities = async () => {
  try {
    setLoading(true);
    const response = await fetch('/api/v1/entities', {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('authToken')}` }
    });
    if (!response.ok) throw new Error('Failed to fetch entities');
    const data = await response.json();
    setEntities(data.entities || []);
  } catch (err) {
    showToast(err.message, 'error');
  } finally {
    setLoading(false);
  }
};

// Create/update entity
const handleSaveEntity = async () => {
  try {
    const url = editMode ? `/api/v1/entities/${selectedEntity.name}` : '/api/v1/entities';
    const method = editMode ? 'PUT' : 'POST';

    const response = await fetch(url, {
      method,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('authToken')}`
      },
      body: JSON.stringify(newEntity)
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to save entity');
    }

    showToast(`Entity ${editMode ? 'updated' : 'created'} successfully`);
    setDialogOpen(false);
    setEditMode(false);
    setNewEntity({ name: '', value: '' });
    fetchEntities();
  } catch (err) {
    showToast(err.message, 'error');
  }
};
```

---

**Document Version**: 1.0.0
**Last Updated**: October 24, 2025
**Epic**: 1.3 - Traefik Configuration Management
**Support**: support@magicunicorn.tech
