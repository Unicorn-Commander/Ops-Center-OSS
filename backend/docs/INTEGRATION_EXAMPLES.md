# Audit Logging Integration Examples

This document provides examples of how to integrate audit logging into your existing server.py endpoints.

## 1. Adding Audit Logging to server.py

### Step 1: Import Required Modules

Add these imports at the top of `server.py`:

```python
# Add to existing imports in server.py
from audit_logger import audit_logger
from audit_helpers import (
    log_auth_success,
    log_auth_failure,
    log_logout,
    log_permission_denied,
    log_service_operation,
    log_model_operation,
    log_user_management,
    log_data_access,
    get_client_ip,
    get_user_agent,
    get_session_id
)
from models.audit_log import AuditAction, AuditResult
from audit_endpoints import router as audit_router
```

### Step 2: Include Audit Router

Add the audit endpoints router to your FastAPI app:

```python
# Add after other router includes in server.py
app.include_router(audit_router)
```

### Step 3: Initialize Audit Logging on Startup

Add this to your app startup:

```python
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting UC-1 Pro Admin Dashboard API")

    # Initialize audit logging
    try:
        # Ensure audit database is initialized
        from audit_logger import audit_logger
        logger.info("Audit logging initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize audit logging: {e}")

    # Your existing startup code...
```

## 2. Authentication Endpoints

### Login Endpoint

```python
@app.post("/api/auth/login")
async def login(request: Request, credentials: LoginCredentials):
    """User login with audit logging"""
    try:
        # Authenticate user
        user = auth_manager.authenticate(credentials.username, credentials.password)

        if not user:
            # Log failed attempt
            await log_auth_failure(
                request=request,
                username=credentials.username,
                reason="Invalid credentials"
            )
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Create token
        token = auth_manager.create_token(user)

        # Log successful login
        await log_auth_success(
            request=request,
            user_id=user.id,
            username=user.username,
            metadata={
                "method": "password",
                "token_expires": token.expires_in
            }
        )

        return token

    except HTTPException:
        raise
    except Exception as e:
        await log_auth_failure(
            request=request,
            username=credentials.username,
            reason=f"System error: {str(e)}"
        )
        raise HTTPException(status_code=500, detail="Authentication failed")
```

### Logout Endpoint

```python
@app.post("/api/auth/logout")
async def logout(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """User logout with audit logging"""
    try:
        # Verify token and get user
        user = auth_manager.verify_token(credentials.credentials)

        # Invalidate token
        auth_manager.revoke_token(credentials.credentials)

        # Log logout
        await log_logout(
            request=request,
            user_id=user.id,
            username=user.username
        )

        return {"message": "Logged out successfully"}

    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### Password Change Endpoint

```python
@app.post("/api/auth/password/change")
async def change_password(
    request: Request,
    password_data: PasswordChange,
    current_user = Depends(get_current_user)
):
    """Change password with audit logging"""
    try:
        # Verify current password
        if not auth_manager.verify_password(current_user.id, password_data.current_password):
            await audit_logger.log(
                action=AuditAction.AUTH_PASSWORD_CHANGE.value,
                result=AuditResult.FAILURE.value,
                user_id=current_user.id,
                username=current_user.username,
                ip_address=get_client_ip(request),
                error_message="Current password incorrect"
            )
            raise HTTPException(status_code=400, detail="Current password incorrect")

        # Change password
        auth_manager.change_password(current_user.id, password_data.new_password)

        # Log success
        await audit_logger.log(
            action=AuditAction.AUTH_PASSWORD_CHANGE.value,
            result=AuditResult.SUCCESS.value,
            user_id=current_user.id,
            username=current_user.username,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request)
        )

        return {"message": "Password changed successfully"}

    except HTTPException:
        raise
    except Exception as e:
        await audit_logger.log(
            action=AuditAction.AUTH_PASSWORD_CHANGE.value,
            result=AuditResult.ERROR.value,
            user_id=current_user.id,
            username=current_user.username,
            ip_address=get_client_ip(request),
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail="Failed to change password")
```

## 3. Service Management Endpoints

### Start Service

```python
@app.post("/api/services/{service_name}/start")
async def start_service(
    request: Request,
    service_name: str,
    current_user = Depends(require_admin)
):
    """Start a service with audit logging"""
    try:
        # Start the service
        docker_manager.start_service(service_name)

        # Log success
        await log_service_operation(
            request=request,
            user_id=current_user.id,
            username=current_user.username,
            operation="start",
            service_name=service_name,
            success=True
        )

        return {"status": "started", "service": service_name}

    except Exception as e:
        # Log failure
        await log_service_operation(
            request=request,
            user_id=current_user.id,
            username=current_user.username,
            operation="start",
            service_name=service_name,
            success=False,
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Failed to start service: {str(e)}")
```

### Stop Service

```python
@app.post("/api/services/{service_name}/stop")
async def stop_service(
    request: Request,
    service_name: str,
    current_user = Depends(require_admin)
):
    """Stop a service with audit logging"""
    try:
        # Stop the service
        docker_manager.stop_service(service_name)

        # Log success
        await log_service_operation(
            request=request,
            user_id=current_user.id,
            username=current_user.username,
            operation="stop",
            service_name=service_name,
            success=True
        )

        return {"status": "stopped", "service": service_name}

    except Exception as e:
        # Log failure
        await log_service_operation(
            request=request,
            user_id=current_user.id,
            username=current_user.username,
            operation="stop",
            service_name=service_name,
            success=False,
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Failed to stop service: {str(e)}")
```

## 4. Model Management Endpoints

### Download Model

```python
@app.post("/api/models/download")
async def download_model(
    request: Request,
    model_request: ModelDownloadRequest,
    current_user = Depends(require_admin)
):
    """Download a model with audit logging"""
    try:
        # Start download
        task_id = ai_model_manager.download_model(model_request.model_name)

        # Log success
        await log_model_operation(
            request=request,
            user_id=current_user.id,
            username=current_user.username,
            operation="download",
            model_name=model_request.model_name,
            success=True,
            metadata={
                "task_id": task_id,
                "model_type": model_request.model_type
            }
        )

        return {"task_id": task_id, "status": "downloading"}

    except Exception as e:
        # Log failure
        await log_model_operation(
            request=request,
            user_id=current_user.id,
            username=current_user.username,
            operation="download",
            model_name=model_request.model_name,
            success=False,
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Failed to download model: {str(e)}")
```

### Delete Model

```python
@app.delete("/api/models/{model_name}")
async def delete_model(
    request: Request,
    model_name: str,
    current_user = Depends(require_admin)
):
    """Delete a model with audit logging"""
    try:
        # Delete the model
        ai_model_manager.delete_model(model_name)

        # Log success
        await log_model_operation(
            request=request,
            user_id=current_user.id,
            username=current_user.username,
            operation="delete",
            model_name=model_name,
            success=True
        )

        return {"status": "deleted", "model": model_name}

    except Exception as e:
        # Log failure
        await log_model_operation(
            request=request,
            user_id=current_user.id,
            username=current_user.username,
            operation="delete",
            model_name=model_name,
            success=False,
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Failed to delete model: {str(e)}")
```

## 5. User Management Endpoints

### Create User

```python
@app.post("/api/users")
async def create_user(
    request: Request,
    user_data: UserCreate,
    current_user = Depends(require_admin)
):
    """Create a user with audit logging"""
    try:
        # Create the user
        new_user = auth_manager.create_user(user_data)

        # Log success
        await log_user_management(
            request=request,
            admin_user_id=current_user.id,
            admin_username=current_user.username,
            operation="create",
            target_user_id=new_user.id,
            target_username=new_user.username,
            success=True,
            metadata={
                "role": new_user.role,
                "email": new_user.email
            }
        )

        return new_user

    except Exception as e:
        # Log failure
        await log_user_management(
            request=request,
            admin_user_id=current_user.id,
            admin_username=current_user.username,
            operation="create",
            target_user_id="unknown",
            target_username=user_data.username,
            success=False,
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")
```

### Update User Role

```python
@app.patch("/api/users/{user_id}/role")
async def update_user_role(
    request: Request,
    user_id: str,
    role_data: dict,
    current_user = Depends(require_admin)
):
    """Update user role with audit logging"""
    try:
        # Get target user
        target_user = auth_manager.get_user(user_id)
        old_role = target_user.role

        # Update role
        auth_manager.update_user_role(user_id, role_data["role"])

        # Log success
        await log_user_management(
            request=request,
            admin_user_id=current_user.id,
            admin_username=current_user.username,
            operation="role_change",
            target_user_id=user_id,
            target_username=target_user.username,
            success=True,
            metadata={
                "old_role": old_role,
                "new_role": role_data["role"]
            }
        )

        return {"message": "Role updated successfully"}

    except Exception as e:
        # Log failure
        await log_user_management(
            request=request,
            admin_user_id=current_user.id,
            admin_username=current_user.username,
            operation="role_change",
            target_user_id=user_id,
            target_username="unknown",
            success=False,
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Failed to update role: {str(e)}")
```

## 6. Permission Denied Logging

### Admin-Only Endpoint with Audit

```python
async def require_admin(request: Request, current_user = Depends(get_current_user)):
    """Require admin role with audit logging for denials"""
    if current_user.role != "admin":
        # Log permission denied
        await log_permission_denied(
            request=request,
            user_id=current_user.id,
            username=current_user.username,
            resource_type="admin_endpoint",
            required_permission="admin"
        )
        raise HTTPException(status_code=403, detail="Admin access required")

    return current_user
```

## 7. Data Access Logging

### View Configuration

```python
@app.get("/api/config")
async def get_config(
    request: Request,
    current_user = Depends(get_current_user)
):
    """Get configuration with audit logging"""
    try:
        # Get config
        config = get_system_config()

        # Log data access
        await log_data_access(
            request=request,
            user_id=current_user.id,
            username=current_user.username,
            data_type="system_config",
            operation="config_view"
        )

        return config

    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to get config")
```

### Export Configuration

```python
@app.get("/api/config/export")
async def export_config(
    request: Request,
    current_user = Depends(require_admin)
):
    """Export configuration with audit logging"""
    try:
        # Export config
        config_data = export_system_config()

        # Log data export
        await log_data_access(
            request=request,
            user_id=current_user.id,
            username=current_user.username,
            data_type="system_config",
            operation="config_export",
            metadata={"format": "json"}
        )

        return StreamingResponse(
            iter([config_data]),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=config.json"}
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to export config")
```

## 8. System Operations

### System Update

```python
@app.post("/api/system/update")
async def update_system(
    request: Request,
    current_user = Depends(require_admin)
):
    """Update system with audit logging"""
    try:
        # Perform update
        result = github_update_manager.update()

        # Log success
        await audit_logger.log(
            action=AuditAction.SYSTEM_UPDATE.value,
            result=AuditResult.SUCCESS.value,
            user_id=current_user.id,
            username=current_user.username,
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            metadata={
                "version": result.get("version"),
                "commit": result.get("commit")
            }
        )

        return result

    except Exception as e:
        # Log failure
        await audit_logger.log(
            action=AuditAction.SYSTEM_UPDATE.value,
            result=AuditResult.ERROR.value,
            user_id=current_user.id,
            username=current_user.username,
            ip_address=get_client_ip(request),
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")
```

## 9. Middleware for Automatic Logging

### Request Logging Middleware

```python
@app.middleware("http")
async def audit_middleware(request: Request, call_next):
    """Log all API requests"""
    start_time = time.time()

    # Get user if authenticated
    user_id = None
    username = None
    if hasattr(request.state, "user"):
        user = request.state.user
        user_id = getattr(user, "id", None)
        username = getattr(user, "username", None)

    # Process request
    response = await call_next(request)

    # Log request if it's an API call
    if request.url.path.startswith("/api/"):
        duration = time.time() - start_time

        # Don't log audit endpoint calls to avoid recursion
        if not request.url.path.startswith("/api/v1/audit/"):
            # Log based on response status
            result = AuditResult.SUCCESS.value if response.status_code < 400 else AuditResult.FAILURE.value

            # Use appropriate action based on method
            action = f"api.{request.method.lower()}.{request.url.path.replace('/api/', '').replace('/', '.')}"

            await audit_logger.log(
                action=action,
                result=result,
                user_id=user_id,
                username=username,
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                metadata={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": int(duration * 1000)
                }
            )

    return response
```

## 10. Complete Integration Example

Here's a complete example showing how to add audit logging to server.py:

```python
# At the top of server.py, add imports
from audit_logger import audit_logger
from audit_helpers import *
from models.audit_log import AuditAction, AuditResult
from audit_endpoints import router as audit_router

# Include audit router
app.include_router(audit_router)

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Starting UC-1 Pro Admin Dashboard API")

    # Initialize audit logging
    try:
        logger.info("Audit logging initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize audit logging: {e}")

# Example endpoint with audit logging
@app.post("/api/services/{service_name}/start")
async def start_service(
    request: Request,
    service_name: str,
    current_user = Depends(require_admin)
):
    try:
        docker_manager.start_service(service_name)

        await log_service_operation(
            request=request,
            user_id=current_user.id,
            username=current_user.username,
            operation="start",
            service_name=service_name,
            success=True
        )

        return {"status": "started"}
    except Exception as e:
        await log_service_operation(
            request=request,
            user_id=current_user.id,
            username=current_user.username,
            operation="start",
            service_name=service_name,
            success=False,
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=str(e))
```

## Testing Audit Logging

```bash
# Test login (will create audit log)
curl -X POST http://localhost:8084/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"password"}'

# View audit logs
curl http://localhost:8084/api/v1/audit/logs?limit=10

# View statistics
curl http://localhost:8084/api/v1/audit/stats

# View recent logs
curl http://localhost:8084/api/v1/audit/recent?limit=50
```

## Best Practices

1. **Log All Security Events**: Authentication, authorization, data access
2. **Use Helper Functions**: Consistent logging across endpoints
3. **Include Context**: IP address, user agent, metadata
4. **Don't Log Secrets**: Never log passwords, tokens, or sensitive data
5. **Async Logging**: Use async functions to avoid blocking
6. **Error Handling**: Log both successes and failures
7. **Meaningful Actions**: Use descriptive action names
8. **Resource Tracking**: Always include resource type and ID when applicable
