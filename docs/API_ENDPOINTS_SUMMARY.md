# UC-Cloud Ops-Center API Endpoints

**Total Endpoints**: 310

**Generated**: 1761353509.5618868

## Endpoints by Category

### Email Notifications (10 endpoints)

- **GET** `/api/v1/notifications/health`
  - **Function**: `notification_health`
  - **Summary**: Health check for email notification service

- **GET** `/api/v1/notifications/preferences/{user_id}`
  - **Function**: `get_notification_preferences`
  - **Summary**: Get email notification preferences for a user
  - **Path Parameters**: user_id

- **PUT** `/api/v1/notifications/preferences/{user_id}`
  - **Function**: `update_notification_preferences`
  - **Summary**: Update email notification preferences for a user
  - **Path Parameters**: user_id

- **POST** `/api/v1/notifications/send/coupon-redeemed`
  - **Function**: `send_coupon_redeemed`
  - **Summary**: Manually send coupon redemption confirmation (for testing)

- **POST** `/api/v1/notifications/send/low-balance`
  - **Function**: `send_low_balance_alert`
  - **Summary**: Manually send low balance alert email (for testing)

- **POST** `/api/v1/notifications/send/monthly-reset`
  - **Function**: `send_monthly_reset`
  - **Summary**: Manually send monthly credit reset notification (for testing)

- **POST** `/api/v1/notifications/send/payment-failure`
  - **Function**: `send_payment_failure`
  - **Summary**: Manually send payment failure alert (for testing)

- **POST** `/api/v1/notifications/send/tier-upgrade`
  - **Function**: `send_tier_upgrade`
  - **Summary**: Manually send tier upgrade notification (for testing)

- **POST** `/api/v1/notifications/send/welcome`
  - **Function**: `send_welcome_email`
  - **Summary**: Manually send welcome email (for testing)

- **GET** `/api/v1/notifications/unsubscribe/{user_id}`
  - **Function**: `unsubscribe_from_notifications`
  - **Summary**: Unsubscribe user from email notifications (public endpoint)
  - **Path Parameters**: user_id


### Llm (10 endpoints)

- **GET** `/api/v1/llm/byok/keys`
  - **Function**: `list_byok_keys`
  - **Summary**: List user's stored provider keys (masked)

- **POST** `/api/v1/llm/byok/keys`
  - **Function**: `add_byok_key`
  - **Summary**: Add/update user's own API key for a provider

- **DELETE** `/api/v1/llm/byok/keys/{provider}`
  - **Function**: `delete_byok_key`
  - **Summary**: Delete user's API key for a provider
  - **Path Parameters**: provider

- **POST** `/api/v1/llm/chat/completions`
  - **Function**: `chat_completions`
  - **Summary**: OpenAI-compatible chat completions endpoint with credit system

- **GET** `/api/v1/llm/credits`
  - **Function**: `get_credits`
  - **Summary**: Get current credit balance

- **GET** `/api/v1/llm/credits/history`
  - **Function**: `get_credit_history`
  - **Summary**: Get credit transaction history

- **POST** `/api/v1/llm/credits/purchase`
  - **Function**: `purchase_credits`
  - **Summary**: Purchase credits via Stripe

- **GET** `/api/v1/llm/health`
  - **Function**: `health_check`
  - **Summary**: Health check endpoint

- **GET** `/api/v1/llm/models`
  - **Function**: `list_models`
  - **Summary**: List available models based on user tier

- **GET** `/api/v1/llm/usage`
  - **Function**: `get_usage_stats`
  - **Summary**: Get usage statistics


### Llm Configuration (17 endpoints)

- **GET** `/api/v1/llm-config/active`
  - **Function**: `get_all_active_providers`
  - **Summary**: Get all active providers for all purposes

- **POST** `/api/v1/llm-config/active`
  - **Function**: `set_active_provider`
  - **Summary**: Set active provider for a purpose

- **GET** `/api/v1/llm-config/active/{purpose}`
  - **Function**: `get_active_provider`
  - **Summary**: Get active provider for specific purpose
  - **Path Parameters**: purpose

- **GET** `/api/v1/llm-config/api-keys`
  - **Function**: `list_api_keys`
  - **Summary**: List all API keys (MASKED - never returns plaintext keys)

- **POST** `/api/v1/llm-config/api-keys`
  - **Function**: `create_api_key`
  - **Summary**: Create new API key (encrypted storage)

- **DELETE** `/api/v1/llm-config/api-keys/{key_id}`
  - **Function**: `delete_api_key`
  - **Summary**: Delete API key
  - **Path Parameters**: key_id

- **GET** `/api/v1/llm-config/api-keys/{key_id}`
  - **Function**: `get_api_key`
  - **Summary**: Get specific API key by ID (MASKED)
  - **Path Parameters**: key_id

- **PUT** `/api/v1/llm-config/api-keys/{key_id}`
  - **Function**: `update_api_key`
  - **Summary**: Update API key
  - **Path Parameters**: key_id

- **POST** `/api/v1/llm-config/api-keys/{key_id}/test`
  - **Function**: `test_api_key`
  - **Summary**: Test API key validity
  - **Path Parameters**: key_id

- **GET** `/api/v1/llm-config/health`
  - **Function**: `health_check`
  - **Summary**: Health check endpoint

- **GET** `/api/v1/llm-config/servers`
  - **Function**: `list_ai_servers`
  - **Summary**: List all AI servers

- **POST** `/api/v1/llm-config/servers`
  - **Function**: `create_ai_server`
  - **Summary**: Create new AI server configuration

- **DELETE** `/api/v1/llm-config/servers/{server_id}`
  - **Function**: `delete_ai_server`
  - **Summary**: Delete AI server configuration
  - **Path Parameters**: server_id

- **GET** `/api/v1/llm-config/servers/{server_id}`
  - **Function**: `get_ai_server`
  - **Summary**: Get specific AI server by ID
  - **Path Parameters**: server_id

- **PUT** `/api/v1/llm-config/servers/{server_id}`
  - **Function**: `update_ai_server`
  - **Summary**: Update AI server configuration
  - **Path Parameters**: server_id

- **GET** `/api/v1/llm-config/servers/{server_id}/models`
  - **Function**: `get_ai_server_models`
  - **Summary**: Get list of available models from AI server
  - **Path Parameters**: server_id

- **POST** `/api/v1/llm-config/servers/{server_id}/test`
  - **Function**: `test_ai_server`
  - **Summary**: Test connection to AI server
  - **Path Parameters**: server_id


### Llm Management (13 endpoints)

- **GET** `/api/v1/llm/credits`
  - **Function**: `get_credit_status`
  - **Summary**: Get user's credit balance and usage

- **GET** `/api/v1/llm/models`
  - **Function**: `list_models`
  - **Summary**: List all available LLM models across providers

- **POST** `/api/v1/llm/models`
  - **Function**: `create_model`
  - **Summary**: Add new model to provider

- **GET** `/api/v1/llm/providers`
  - **Function**: `list_providers`
  - **Summary**: List all configured LLM providers

- **POST** `/api/v1/llm/providers`
  - **Function**: `create_provider`
  - **Summary**: Add new LLM provider with encrypted API key

- **DELETE** `/api/v1/llm/providers/{provider_id}`
  - **Function**: `delete_provider`
  - **Summary**: Remove provider (will cascade delete associated models)
  - **Path Parameters**: provider_id

- **PUT** `/api/v1/llm/providers/{provider_id}`
  - **Function**: `update_provider`
  - **Summary**: Update provider configuration
  - **Path Parameters**: provider_id

- **GET** `/api/v1/llm/routing/rules`
  - **Function**: `get_routing_rules`
  - **Summary**: Get current routing configuration

- **PUT** `/api/v1/llm/routing/rules`
  - **Function**: `update_routing_rules`
  - **Summary**: Update routing configuration

- **POST** `/api/v1/llm/test`
  - **Function**: `test_provider_connection`
  - **Summary**: Test provider connection with sample request

- **GET** `/api/v1/llm/usage`
  - **Function**: `get_usage_analytics`
  - **Summary**: Get LLM usage analytics

- **GET** `/api/v1/llm/users/{user_id}/byok`
  - **Function**: `get_user_byok`
  - **Summary**: Get user's BYOK configuration (API keys masked)
  - **Path Parameters**: user_id

- **POST** `/api/v1/llm/users/{user_id}/byok`
  - **Function**: `set_user_byok`
  - **Summary**: Set user's Bring Your Own Key configuration
  - **Path Parameters**: user_id


### Llm Providers (5 endpoints)

- **DELETE** `/api/v1/admin/llm/providers/{provider_id}`
  - **Function**: `delete_provider`
  - **Summary**: Delete LLM provider
  - **Path Parameters**: provider_id

- **GET** `/api/v1/admin/llm/providers/{provider_id}`
  - **Function**: `get_provider`
  - **Summary**: Get provider by ID
  - **Path Parameters**: provider_id

- **PUT** `/api/v1/admin/llm/providers/{provider_id}`
  - **Function**: `update_provider`
  - **Summary**: Update LLM provider
  - **Path Parameters**: provider_id

- **GET** `/api/v1/admin/llm/providers/{provider_id}/health`
  - **Function**: `check_provider_health`
  - **Summary**: Check provider health status
  - **Path Parameters**: provider_id

- **POST** `/api/v1/admin/llm/providers/{provider_id}/test`
  - **Function**: `test_provider_connection`
  - **Summary**: Test provider API connection with API key
  - **Path Parameters**: provider_id


### Local Users (21 endpoints)

- **GET** `/api/v1/admin/system/local-users/groups`
  - **Function**: `list_groups`
  - **Summary**: List all available system groups

- **GET** `/api/v1/admin/system/local-users/health`
  - **Function**: `health_check`
  - **Summary**: Health check endpoint

- **DELETE** `/api/v1/admin/system/local-users/{username}`
  - **Function**: `delete_local_user`
  - **Summary**: Delete a local user
  - **Path Parameters**: username

- **GET** `/api/v1/admin/system/local-users/{username}`
  - **Function**: `get_local_user`
  - **Summary**: Get details for a specific local user
  - **Path Parameters**: username

- **PUT** `/api/v1/admin/system/local-users/{username}`
  - **Function**: `update_local_user`
  - **Summary**: Update an existing local user
  - **Path Parameters**: username

- **POST** `/api/v1/admin/system/local-users/{username}/password`
  - **Function**: `reset_user_password`
  - **Summary**: Reset user password
  - **Path Parameters**: username

- **GET** `/api/v1/admin/system/local-users/{username}/ssh-keys`
  - **Function**: `list_ssh_keys`
  - **Summary**: List SSH public keys for a user
  - **Path Parameters**: username

- **POST** `/api/v1/admin/system/local-users/{username}/ssh-keys`
  - **Function**: `add_ssh_key`
  - **Summary**: Add SSH public key for a user
  - **Path Parameters**: username

- **DELETE** `/api/v1/admin/system/local-users/{username}/ssh-keys/{key_id}`
  - **Function**: `remove_ssh_key`
  - **Summary**: Remove SSH public key for a user
  - **Path Parameters**: username, key_id

- **PUT** `/api/v1/admin/system/local-users/{username}/sudo`
  - **Function**: `set_sudo_access`
  - **Summary**: Manage sudo access for a user
  - **Path Parameters**: username

- **GET** `/api/v1/local-users/`
  - **Function**: `list_local_users`
  - **Summary**: List local Linux users with pagination and filtering.

- **POST** `/api/v1/local-users/`
  - **Function**: `create_local_user`
  - **Summary**: Create a new local Linux user.

- **GET** `/api/v1/local-users/statistics`
  - **Function**: `get_user_statistics`
  - **Summary**: Get statistics about local users.

- **DELETE** `/api/v1/local-users/{username}`
  - **Function**: `delete_local_user`
  - **Summary**: Delete a local Linux user.
  - **Path Parameters**: username

- **GET** `/api/v1/local-users/{username}`
  - **Function**: `get_local_user`
  - **Summary**: Get detailed information about a local user.
  - **Path Parameters**: username

- **POST** `/api/v1/local-users/{username}/password`
  - **Function**: `set_user_password`
  - **Summary**: Set password for a local user.
  - **Path Parameters**: username

- **GET** `/api/v1/local-users/{username}/ssh-keys`
  - **Function**: `get_ssh_keys`
  - **Summary**: List SSH public keys for a user.
  - **Path Parameters**: username

- **POST** `/api/v1/local-users/{username}/ssh-keys`
  - **Function**: `add_user_ssh_key`
  - **Summary**: Add SSH public key to user's authorized_keys.
  - **Path Parameters**: username

- **DELETE** `/api/v1/local-users/{username}/ssh-keys/{key_fingerprint}`
  - **Function**: `remove_user_ssh_key`
  - **Summary**: Remove SSH public key from user's authorized_keys.
  - **Path Parameters**: username, key_fingerprint

- **DELETE** `/api/v1/local-users/{username}/sudo`
  - **Function**: `revoke_sudo`
  - **Summary**: Revoke sudo permissions from a user.
  - **Path Parameters**: username

- **POST** `/api/v1/local-users/{username}/sudo`
  - **Function**: `grant_sudo`
  - **Summary**: Grant sudo permissions to a user.
  - **Path Parameters**: username


### Platform Settings (5 endpoints)

- **GET** `/api/v1/platform/settings`
  - **Function**: `get_platform_settings`
  - **Summary**: Get all platform settings with masked secrets

- **PUT** `/api/v1/platform/settings`
  - **Function**: `update_platform_settings`
  - **Summary**: Update platform settings

- **POST** `/api/v1/platform/settings/restart`
  - **Function**: `restart_container`
  - **Summary**: Restart ops-center container to apply new settings

- **POST** `/api/v1/platform/settings/test`
  - **Function**: `test_connection`
  - **Summary**: Test connection with provided credentials

- **GET** `/api/v1/platform/settings/{key}`
  - **Function**: `get_setting`
  - **Summary**: Get specific platform setting
  - **Path Parameters**: key


### Storage & Backup (25 endpoints)

- **GET** `/api/v1/backups`
  - **Function**: `list_backups`
  - **Summary**: List all backups with status

- **GET** `/api/v1/backups/config`
  - **Function**: `get_backup_config`
  - **Summary**: Get backup configuration

- **PUT** `/api/v1/backups/config`
  - **Function**: `update_backup_config`
  - **Summary**: Update backup configuration

- **POST** `/api/v1/backups/create`
  - **Function**: `create_backup`
  - **Summary**: Create a new backup

- **POST** `/api/v1/backups/rclone/check`
  - **Function**: `check_rclone_connection`
  - **Summary**: Test connection to remote

- **POST** `/api/v1/backups/rclone/configure`
  - **Function**: `configure_rclone_remote`
  - **Summary**: Configure a new rclone remote

- **POST** `/api/v1/backups/rclone/copy`
  - **Function**: `rclone_copy`
  - **Summary**: Copy files via rclone (doesn't delete from destination)

- **POST** `/api/v1/backups/rclone/delete`
  - **Function**: `rclone_delete`
  - **Summary**: Delete files at remote path

- **GET** `/api/v1/backups/rclone/list`
  - **Function**: `rclone_list`
  - **Summary**: List files at remote path

- **POST** `/api/v1/backups/rclone/mount`
  - **Function**: `mount_rclone_remote`
  - **Summary**: Mount remote as local filesystem

- **POST** `/api/v1/backups/rclone/move`
  - **Function**: `rclone_move`
  - **Summary**: Move files via rclone (deletes from source after copying)

- **GET** `/api/v1/backups/rclone/providers`
  - **Function**: `list_rclone_providers`
  - **Summary**: List all supported cloud providers

- **GET** `/api/v1/backups/rclone/remotes`
  - **Function**: `list_rclone_remotes`
  - **Summary**: List all configured rclone remotes

- **GET** `/api/v1/backups/rclone/size`
  - **Function**: `rclone_size`
  - **Summary**: Get total size of remote path

- **POST** `/api/v1/backups/rclone/sync`
  - **Function**: `rclone_sync`
  - **Summary**: Sync directories via rclone (makes destination identical to source)

- **POST** `/api/v1/backups/verify/{backup_id}`
  - **Function**: `verify_backup`
  - **Summary**: Verify backup integrity
  - **Path Parameters**: backup_id

- **DELETE** `/api/v1/backups/{backup_id}`
  - **Function**: `delete_backup`
  - **Summary**: Delete a backup
  - **Path Parameters**: backup_id

- **GET** `/api/v1/backups/{backup_id}/download`
  - **Function**: `download_backup`
  - **Summary**: Download a backup file
  - **Path Parameters**: backup_id

- **POST** `/api/v1/backups/{backup_id}/restore`
  - **Function**: `restore_backup`
  - **Summary**: Restore from a backup
  - **Path Parameters**: backup_id

- **POST** `/api/v1/storage/cleanup`
  - **Function**: `cleanup_storage`
  - **Summary**: Clean up unused volumes, images, logs, and cache

- **GET** `/api/v1/storage/health`
  - **Function**: `check_storage_health`
  - **Summary**: Check storage health and get recommendations

- **GET** `/api/v1/storage/info`
  - **Function**: `get_storage_info`
  - **Summary**: Get comprehensive storage information

- **POST** `/api/v1/storage/optimize`
  - **Function**: `optimize_storage`
  - **Summary**: Optimize storage (compress logs, verify integrity)

- **GET** `/api/v1/storage/volumes`
  - **Function**: `list_volumes`
  - **Summary**: List all Docker volumes with details

- **GET** `/api/v1/storage/volumes/{volume_name}`
  - **Function**: `get_volume_details`
  - **Summary**: Get detailed information about a specific volume
  - **Path Parameters**: volume_name


### System Settings (7 endpoints)

- **GET** `/api/v1/system/settings/audit/log`
  - **Function**: `get_audit_log`
  - **Summary**: Get audit log for system settings changes

- **POST** `/api/v1/system/settings/bulk`
  - **Function**: `bulk_update_settings`
  - **Summary**: Bulk update multiple settings

- **GET** `/api/v1/system/settings/categories`
  - **Function**: `list_categories`
  - **Summary**: List all available setting categories

- **GET** `/api/v1/system/settings/health`
  - **Function**: `health_check`
  - **Summary**: Health check endpoint

- **DELETE** `/api/v1/system/settings/{key}`
  - **Function**: `delete_setting`
  - **Summary**: Delete a system setting
  - **Path Parameters**: key

- **GET** `/api/v1/system/settings/{key}`
  - **Function**: `get_setting`
  - **Summary**: Get specific setting by key
  - **Path Parameters**: key

- **PUT** `/api/v1/system/settings/{key}`
  - **Function**: `update_setting`
  - **Summary**: Update existing setting
  - **Path Parameters**: key


### Traefik Metrics (6 endpoints)

- **GET** `/api/v1/traefik/metrics/errors`
  - **Function**: `get_error_summary`
  - **Summary**: Get error summary across all routes.

- **GET** `/api/v1/traefik/metrics/overview`
  - **Function**: `get_traefik_stats`
  - **Summary**: Get overall Traefik statistics.

- **GET** `/api/v1/traefik/metrics/performance`
  - **Function**: `get_performance_summary`
  - **Summary**: Get performance summary across all routes.

- **GET** `/api/v1/traefik/metrics/raw`
  - **Function**: `get_raw_metrics`
  - **Summary**: Get raw Prometheus metrics from Traefik.

- **GET** `/api/v1/traefik/metrics/routes`
  - **Function**: `get_route_metrics`
  - **Summary**: Get metrics for all routes.

- **GET** `/api/v1/traefik/metrics/routes/{route_name}`
  - **Function**: `get_route_metric`
  - **Summary**: Get metrics for a specific route.
  - **Path Parameters**: route_name


### Traefik Middlewares (4 endpoints)

- **GET** `/api/v1/traefik/middlewares/templates`
  - **Function**: `list_middleware_templates`
  - **Summary**: List available middleware templates.

- **DELETE** `/api/v1/traefik/middlewares/{middleware_id}`
  - **Function**: `delete_middleware`
  - **Summary**: Delete a middleware.
  - **Path Parameters**: middleware_id

- **GET** `/api/v1/traefik/middlewares/{middleware_id}`
  - **Function**: `get_middleware`
  - **Summary**: Get specific middleware details.
  - **Path Parameters**: middleware_id

- **PUT** `/api/v1/traefik/middlewares/{middleware_id}`
  - **Function**: `update_middleware`
  - **Summary**: Update an existing middleware.
  - **Path Parameters**: middleware_id


### Traefik Routes (4 endpoints)

- **DELETE** `/api/v1/traefik/routes/{route_id}`
  - **Function**: `delete_route`
  - **Summary**: Delete a Traefik route.
  - **Path Parameters**: route_id

- **GET** `/api/v1/traefik/routes/{route_id}`
  - **Function**: `get_route`
  - **Summary**: Get specific route details.
  - **Path Parameters**: route_id

- **PUT** `/api/v1/traefik/routes/{route_id}`
  - **Function**: `update_route`
  - **Summary**: Update an existing Traefik route.
  - **Path Parameters**: route_id

- **POST** `/api/v1/traefik/routes/{route_id}/test`
  - **Function**: `test_route`
  - **Summary**: Test a Traefik route configuration.
  - **Path Parameters**: route_id


### Traefik Services (4 endpoints)

- **GET** `/api/v1/traefik/services/discover/containers`
  - **Function**: `discover_containers`
  - **Summary**: Discover running Docker containers for service creation.

- **DELETE** `/api/v1/traefik/services/{service_id}`
  - **Function**: `delete_service`
  - **Summary**: Delete a backend service.
  - **Path Parameters**: service_id

- **GET** `/api/v1/traefik/services/{service_id}`
  - **Function**: `get_service`
  - **Summary**: Get specific service details.
  - **Path Parameters**: service_id

- **PUT** `/api/v1/traefik/services/{service_id}`
  - **Function**: `update_service`
  - **Summary**: Update an existing backend service.
  - **Path Parameters**: service_id


### Admin (7 endpoints)

- **GET** `/api/v1/admin/subscriptions/analytics/overview`
  - **Function**: `get_subscription_analytics`
  - **Summary**: Get subscription analytics and revenue metrics

- **GET** `/api/v1/admin/subscriptions/analytics/revenue-by-tier`
  - **Function**: `get_revenue_by_tier`
  - **Summary**: Get revenue breakdown by subscription tier

- **GET** `/api/v1/admin/subscriptions/analytics/usage-stats`
  - **Function**: `get_usage_statistics`
  - **Summary**: Get detailed usage statistics

- **GET** `/api/v1/admin/subscriptions/list`
  - **Function**: `list_all_subscriptions`
  - **Summary**: List all user subscriptions with usage stats

- **GET** `/api/v1/admin/subscriptions/{email}`
  - **Function**: `get_user_subscription`
  - **Summary**: Get detailed subscription info for a specific user
  - **Path Parameters**: email

- **PATCH** `/api/v1/admin/subscriptions/{email}`
  - **Function**: `update_user_subscription`
  - **Summary**: Manually update a user's subscription (for support cases)
  - **Path Parameters**: email

- **POST** `/api/v1/admin/subscriptions/{email}/reset-usage`
  - **Function**: `reset_user_usage`
  - **Summary**: Reset a user's API usage counters
  - **Path Parameters**: email


### Billing (8 endpoints)

- **GET** `/api/v1/billing/payment-methods`
  - **Function**: `get_payment_methods`
  - **Summary**: Get user's saved payment methods

- **POST** `/api/v1/billing/portal/create`
  - **Function**: `create_portal_session`
  - **Summary**: Create a Stripe Customer Portal session for subscription management

- **GET** `/api/v1/billing/subscription-status`
  - **Function**: `get_subscription_status`
  - **Summary**: Get user's current subscription status

- **POST** `/api/v1/billing/subscription/cancel`
  - **Function**: `cancel_subscription`
  - **Summary**: Cancel a subscription

- **POST** `/api/v1/billing/subscription/upgrade`
  - **Function**: `upgrade_subscription`
  - **Summary**: Upgrade or downgrade subscription tier

- **POST** `/api/v1/billing/subscriptions/checkout`
  - **Function**: `create_checkout_session`
  - **Summary**: Create a Stripe Checkout session for subscription purchase

- **POST** `/api/v1/billing/webhooks/stripe`
  - **Function**: `stripe_webhook`
  - **Summary**: Handle Stripe webhook events

- **POST** `/api/v1/billing/webhooks/stripe/checkout`
  - **Function**: `stripe_checkout_webhook`
  - **Summary**: Handle Stripe checkout.session.completed webhook


### Billing-Lago (5 endpoints)

- **GET** `/api/v1/billing/cycle`
  - **Function**: `get_billing_cycle`
  - **Summary**: Get current billing cycle information.

- **POST** `/api/v1/billing/download-invoice/{invoice_id}`
  - **Function**: `download_invoice`
  - **Summary**: Generate download URL for invoice PDF.
  - **Path Parameters**: invoice_id

- **GET** `/api/v1/billing/invoices`
  - **Function**: `get_invoices_list`
  - **Summary**: Get invoice history from Lago.

- **GET** `/api/v1/billing/payment-methods`
  - **Function**: `get_payment_methods`
  - **Summary**: Get stored payment methods (Stripe).

- **GET** `/api/v1/billing/summary`
  - **Function**: `get_billing_summary`
  - **Summary**: Get billing summary with total spend, upcoming charges, etc.


### Byok (5 endpoints)

- **GET** `/api/v1/byok/keys`
  - **Function**: `list_keys`
  - **Summary**: List user's configured API keys (masked)

- **POST** `/api/v1/byok/keys/test/{provider}`
  - **Function**: `test_key`
  - **Summary**: Test if an API key is valid
  - **Path Parameters**: provider

- **DELETE** `/api/v1/byok/keys/{provider}`
  - **Function**: `delete_key`
  - **Summary**: Remove an API key
  - **Path Parameters**: provider

- **GET** `/api/v1/byok/providers`
  - **Function**: `list_providers`
  - **Summary**: Get list of supported providers

- **GET** `/api/v1/byok/stats`
  - **Function**: `get_byok_stats`
  - **Summary**: Get statistics about user's BYOK configuration


### Cloudflare (16 endpoints)

- **GET** `/api/v1/cloudflare/health`
  - **Function**: `cloudflare_health_check`
  - **Summary**: Health check endpoint for Cloudflare API

- **GET** `/api/v1/cloudflare/propagation/{zone_id}`
  - **Function**: `check_propagation`
  - **Summary**: Check DNS propagation status for a zone
  - **Path Parameters**: zone_id

- **GET** `/api/v1/cloudflare/zones`
  - **Function**: `list_zones`
  - **Summary**: Get all Cloudflare zones with optional filtering

- **POST** `/api/v1/cloudflare/zones`
  - **Function**: `create_zone`
  - **Summary**: Create a new Cloudflare zone

- **DELETE** `/api/v1/cloudflare/zones/{zone_id}`
  - **Function**: `delete_zone`
  - **Summary**: Delete a Cloudflare zone
  - **Path Parameters**: zone_id

- **GET** `/api/v1/cloudflare/zones/{zone_id}`
  - **Function**: `get_zone`
  - **Summary**: Get detailed information about a specific zone
  - **Path Parameters**: zone_id

- **POST** `/api/v1/cloudflare/zones/{zone_id}/activate`
  - **Function**: `activate_zone`
  - **Summary**: Check and activate a pending zone
  - **Path Parameters**: zone_id

- **GET** `/api/v1/cloudflare/zones/{zone_id}/analytics`
  - **Function**: `get_zone_analytics`
  - **Summary**: Get analytics data for a zone
  - **Path Parameters**: zone_id

- **GET** `/api/v1/cloudflare/zones/{zone_id}/dns`
  - **Function**: `list_dns_records`
  - **Summary**: List DNS records for a zone
  - **Path Parameters**: zone_id

- **POST** `/api/v1/cloudflare/zones/{zone_id}/dns`
  - **Function**: `create_dns_record`
  - **Summary**: Create a new DNS record
  - **Path Parameters**: zone_id

- **DELETE** `/api/v1/cloudflare/zones/{zone_id}/dns/{record_id}`
  - **Function**: `delete_dns_record`
  - **Summary**: Delete a DNS record
  - **Path Parameters**: zone_id, record_id

- **PUT** `/api/v1/cloudflare/zones/{zone_id}/dns/{record_id}`
  - **Function**: `update_dns_record`
  - **Summary**: Update an existing DNS record
  - **Path Parameters**: zone_id, record_id

- **GET** `/api/v1/cloudflare/zones/{zone_id}/nameservers`
  - **Function**: `get_nameservers`
  - **Summary**: Get assigned Cloudflare nameservers for a zone
  - **Path Parameters**: zone_id

- **PUT** `/api/v1/cloudflare/zones/{zone_id}/nameservers`
  - **Function**: `update_nameservers`
  - **Summary**: Update nameservers for a zone (advanced operation)
  - **Path Parameters**: zone_id

- **GET** `/api/v1/cloudflare/zones/{zone_id}/ssl`
  - **Function**: `get_ssl_status`
  - **Summary**: Get SSL/TLS status for a zone
  - **Path Parameters**: zone_id

- **GET** `/api/v1/cloudflare/zones/{zone_id}/status`
  - **Function**: `get_zone_status`
  - **Summary**: Get current status of a zone (pending, active, deactivated)
  - **Path Parameters**: zone_id


### Credentials (6 endpoints)

- **GET** `/api/v1/credentials/health`
  - **Function**: `health_check`
  - **Summary**: Health check endpoint for credential management API

- **GET** `/api/v1/credentials/services`
  - **Function**: `list_supported_services`
  - **Summary**: List all supported services and their credential types

- **POST** `/api/v1/credentials/{service}/test`
  - **Function**: `test_credential`
  - **Summary**: Test credential by calling service API
  - **Path Parameters**: service

- **DELETE** `/api/v1/credentials/{service}/{credential_type}`
  - **Function**: `delete_credential`
  - **Summary**: Delete credential (soft delete)
  - **Path Parameters**: service, credential_type

- **GET** `/api/v1/credentials/{service}/{credential_type}`
  - **Function**: `get_credential`
  - **Summary**: Get single credential info (MASKED value only)
  - **Path Parameters**: service, credential_type

- **PUT** `/api/v1/credentials/{service}/{credential_type}`
  - **Function**: `update_credential`
  - **Summary**: Update existing credential
  - **Path Parameters**: service, credential_type


### Credits (21 endpoints)

- **POST** `/api/v1/credits/allocate`
  - **Function**: `allocate_credits`
  - **Summary**: Allocate credits to a user (admin only).

- **GET** `/api/v1/credits/balance`
  - **Function**: `get_credit_balance`
  - **Summary**: Get user's current credit balance.

- **GET** `/api/v1/credits/coupons`
  - **Function**: `list_coupons`
  - **Summary**: List all coupons (admin only).

- **POST** `/api/v1/credits/coupons/create`
  - **Function**: `create_coupon`
  - **Summary**: Create coupon code (admin only).

- **POST** `/api/v1/credits/coupons/redeem`
  - **Function**: `redeem_coupon`
  - **Summary**: Redeem coupon code.

- **GET** `/api/v1/credits/coupons/validate/{code}`
  - **Function**: `validate_coupon`
  - **Summary**: Validate coupon code.
  - **Path Parameters**: code

- **DELETE** `/api/v1/credits/coupons/{code}`
  - **Function**: `delete_coupon`
  - **Summary**: Deactivate coupon (admin only).
  - **Path Parameters**: code

- **POST** `/api/v1/credits/deduct`
  - **Function**: `deduct_credits`
  - **Summary**: Deduct credits from user (internal/admin only).

- **DELETE** `/api/v1/credits/openrouter/account`
  - **Function**: `delete_openrouter_account`
  - **Summary**: Delete OpenRouter BYOK account.

- **GET** `/api/v1/credits/openrouter/account`
  - **Function**: `get_openrouter_account`
  - **Summary**: Get OpenRouter account details.

- **POST** `/api/v1/credits/openrouter/create-account`
  - **Function**: `create_openrouter_account`
  - **Summary**: Create OpenRouter BYOK account for user.

- **POST** `/api/v1/credits/openrouter/sync-balance`
  - **Function**: `sync_openrouter_balance`
  - **Summary**: Sync free credits from OpenRouter API.

- **POST** `/api/v1/credits/refund`
  - **Function**: `refund_credits`
  - **Summary**: Refund credits to user (admin only).

- **GET** `/api/v1/credits/tiers/compare`
  - **Function**: `compare_tiers`
  - **Summary**: Compare subscription tiers.

- **POST** `/api/v1/credits/tiers/switch`
  - **Function**: `switch_tier`
  - **Summary**: Switch subscription tier (triggers monthly credit reset).

- **GET** `/api/v1/credits/transactions`
  - **Function**: `get_transactions`
  - **Summary**: Get credit transaction history.

- **GET** `/api/v1/credits/usage/by-model`
  - **Function**: `get_usage_by_model`
  - **Summary**: Get usage breakdown by model.

- **GET** `/api/v1/credits/usage/by-service`
  - **Function**: `get_usage_by_service`
  - **Summary**: Get usage breakdown by service.

- **GET** `/api/v1/credits/usage/free-tier`
  - **Function**: `get_free_tier_usage`
  - **Summary**: Get free tier usage statistics.

- **GET** `/api/v1/credits/usage/summary`
  - **Function**: `get_usage_summary`
  - **Summary**: Get usage summary for user.

- **POST** `/api/v1/credits/usage/track`
  - **Function**: `track_usage`
  - **Summary**: Track API usage event.


### Execution-Servers (4 endpoints)

- **GET** `/api/v1/execution-servers/default`
  - **Function**: `get_default_server`
  - **Summary**: Get user's default execution server

- **DELETE** `/api/v1/execution-servers/{server_id}`
  - **Function**: `delete_server`
  - **Summary**: Delete execution server
  - **Path Parameters**: server_id

- **PUT** `/api/v1/execution-servers/{server_id}`
  - **Function**: `update_server`
  - **Summary**: Update execution server
  - **Path Parameters**: server_id

- **POST** `/api/v1/execution-servers/{server_id}/test`
  - **Function**: `test_server`
  - **Summary**: Test execution server connection
  - **Path Parameters**: server_id


### Keycloak-Status (6 endpoints)

- **GET** `/api/v1/system/keycloak/api-credentials`
  - **Function**: `get_api_credentials`
  - **Summary**: Get service account credentials for Ops-Center API

- **GET** `/api/v1/system/keycloak/clients`
  - **Function**: `get_clients`
  - **Summary**: List OAuth clients configured in Keycloak

- **GET** `/api/v1/system/keycloak/session-config`
  - **Function**: `get_session_config`
  - **Summary**: Get session configuration from Keycloak realm settings

- **GET** `/api/v1/system/keycloak/ssl-status`
  - **Function**: `get_ssl_status`
  - **Summary**: Get SSL/TLS certificate status for Keycloak

- **GET** `/api/v1/system/keycloak/status`
  - **Function**: `get_keycloak_status`
  - **Summary**: Get Keycloak service status and configuration

- **POST** `/api/v1/system/keycloak/test-connection`
  - **Function**: `test_keycloak_connection`
  - **Summary**: Test connection to Keycloak and verify admin credentials


### Migration (20 endpoints)

- **GET** `/api/v1/migration/health`
  - **Function**: `migration_health_check`
  - **Summary**: Health check endpoint for migration API

- **POST** `/api/v1/migration/migration/execute`
  - **Function**: `execute_migration`
  - **Summary**: Execute a migration job

- **POST** `/api/v1/migration/migration/preview`
  - **Function**: `preview_migration`
  - **Summary**: Preview migration plan before execution

- **GET** `/api/v1/migration/migration/preview/{migration_id}`
  - **Function**: `get_migration_preview`
  - **Summary**: Get details of a migration preview
  - **Path Parameters**: migration_id

- **POST** `/api/v1/migration/migration/validate`
  - **Function**: `validate_migration`
  - **Summary**: Validate DNS records before migration

- **GET** `/api/v1/migration/migration/{migration_id}/health`
  - **Function**: `get_migration_health`
  - **Summary**: Get overall health check for a migration
  - **Path Parameters**: migration_id

- **POST** `/api/v1/migration/migration/{migration_id}/pause`
  - **Function**: `pause_migration`
  - **Summary**: Pause a running migration job
  - **Path Parameters**: migration_id

- **POST** `/api/v1/migration/migration/{migration_id}/resume`
  - **Function**: `resume_migration`
  - **Summary**: Resume a paused migration job
  - **Path Parameters**: migration_id

- **POST** `/api/v1/migration/migration/{migration_id}/rollback`
  - **Function**: `rollback_migration`
  - **Summary**: Rollback a migration (revert nameservers to original values)
  - **Path Parameters**: migration_id

- **GET** `/api/v1/migration/migration/{migration_id}/status`
  - **Function**: `get_migration_status`
  - **Summary**: Get current status of a migration job
  - **Path Parameters**: migration_id

- **POST** `/api/v1/migration/migration/{migration_id}/verify/dns`
  - **Function**: `verify_dns_propagation`
  - **Summary**: Check DNS propagation status across multiple resolvers
  - **Path Parameters**: migration_id

- **POST** `/api/v1/migration/migration/{migration_id}/verify/email`
  - **Function**: `verify_email_functionality`
  - **Summary**: Test email delivery for migrated domains
  - **Path Parameters**: migration_id

- **POST** `/api/v1/migration/migration/{migration_id}/verify/ssl`
  - **Function**: `verify_ssl_certificates`
  - **Summary**: Verify SSL certificates for migrated domains
  - **Path Parameters**: migration_id

- **POST** `/api/v1/migration/migration/{migration_id}/verify/website`
  - **Function**: `verify_website_accessibility`
  - **Summary**: Check website accessibility for migrated domains
  - **Path Parameters**: migration_id

- **GET** `/api/v1/migration/namecheap/domains`
  - **Function**: `list_namecheap_domains`
  - **Summary**: Get all domains from NameCheap account

- **POST** `/api/v1/migration/namecheap/domains/bulk-check`
  - **Function**: `bulk_check_domains`
  - **Summary**: Check availability and status of multiple domains

- **POST** `/api/v1/migration/namecheap/domains/bulk-export`
  - **Function**: `bulk_export_dns`
  - **Summary**: Export DNS records for multiple domains

- **GET** `/api/v1/migration/namecheap/domains/{domain}`
  - **Function**: `get_namecheap_domain`
  - **Summary**: Get detailed information about a specific domain from NameCheap
  - **Path Parameters**: domain

- **GET** `/api/v1/migration/namecheap/domains/{domain}/dns`
  - **Function**: `export_dns_records`
  - **Summary**: Export DNS records from NameCheap for a domain
  - **Path Parameters**: domain

- **GET** `/api/v1/migration/namecheap/domains/{domain}/email`
  - **Function**: `detect_email_service`
  - **Summary**: Detect email service provider for a domain
  - **Path Parameters**: domain


### Network (12 endpoints)

- **POST** `/api/v1/network/firewall/disable`
  - **Function**: `disable_firewall`
  - **Summary**: Disable UFW firewall

- **POST** `/api/v1/network/firewall/enable`
  - **Function**: `enable_firewall`
  - **Summary**: Enable UFW firewall

- **GET** `/api/v1/network/firewall/health`
  - **Function**: `firewall_health_check`
  - **Summary**: Health check endpoint for firewall API

- **GET** `/api/v1/network/firewall/logs`
  - **Function**: `get_firewall_logs`
  - **Summary**: Get recent firewall logs (blocked/allowed traffic)

- **POST** `/api/v1/network/firewall/reset`
  - **Function**: `reset_firewall`
  - **Summary**: Reset firewall to default configuration

- **GET** `/api/v1/network/firewall/rules`
  - **Function**: `list_firewall_rules`
  - **Summary**: Get all firewall rules with optional filtering

- **POST** `/api/v1/network/firewall/rules`
  - **Function**: `add_firewall_rule`
  - **Summary**: Add new firewall rule

- **POST** `/api/v1/network/firewall/rules/bulk-delete`
  - **Function**: `bulk_delete_firewall_rules`
  - **Summary**: Delete multiple firewall rules at once

- **DELETE** `/api/v1/network/firewall/rules/{rule_num}`
  - **Function**: `delete_firewall_rule`
  - **Summary**: Delete firewall rule by number
  - **Path Parameters**: rule_num

- **GET** `/api/v1/network/firewall/status`
  - **Function**: `get_firewall_status`
  - **Summary**: Get current firewall status and configuration

- **GET** `/api/v1/network/firewall/templates`
  - **Function**: `list_firewall_templates`
  - **Summary**: List all available firewall rule templates

- **POST** `/api/v1/network/firewall/templates/{template_name}`
  - **Function**: `apply_firewall_template`
  - **Summary**: Apply predefined firewall rule template
  - **Path Parameters**: template_name


### Organizations (9 endpoints)

- **GET** `/api/v1/org/roles`
  - **Function**: `list_available_roles`
  - **Summary**: Get list of available organization roles

- **GET** `/api/v1/org/{org_id}/billing`
  - **Function**: `get_organization_billing`
  - **Summary**: Get organization billing information
  - **Path Parameters**: org_id

- **GET** `/api/v1/org/{org_id}/members`
  - **Function**: `list_organization_members`
  - **Summary**: Get list of all members in an organization
  - **Path Parameters**: org_id

- **POST** `/api/v1/org/{org_id}/members`
  - **Function**: `add_organization_member`
  - **Summary**: Add a new member to the organization
  - **Path Parameters**: org_id

- **DELETE** `/api/v1/org/{org_id}/members/{user_id}`
  - **Function**: `remove_organization_member`
  - **Summary**: Remove a member from the organization
  - **Path Parameters**: org_id, user_id

- **PUT** `/api/v1/org/{org_id}/members/{user_id}/role`
  - **Function**: `update_member_role`
  - **Summary**: Update a member's role in the organization
  - **Path Parameters**: org_id, user_id

- **GET** `/api/v1/org/{org_id}/settings`
  - **Function**: `get_organization_settings`
  - **Summary**: Get organization settings
  - **Path Parameters**: org_id

- **PUT** `/api/v1/org/{org_id}/settings`
  - **Function**: `update_organization_settings`
  - **Summary**: Update organization settings
  - **Path Parameters**: org_id

- **GET** `/api/v1/org/{org_id}/stats`
  - **Function**: `get_organization_stats`
  - **Summary**: Get organization statistics and metrics
  - **Path Parameters**: org_id


### Subscriptions (17 endpoints)

- **GET** `/api/v1/subscriptions/admin/user-access/{user_id}`
  - **Function**: `get_user_access_admin`
  - **Summary**: Get service access for specific user (admin only)
  - **Path Parameters**: user_id

- **POST** `/api/v1/subscriptions/cancel`
  - **Function**: `cancel_subscription`
  - **Summary**: Cancel current subscription.

- **POST** `/api/v1/subscriptions/change`
  - **Function**: `change_subscription`
  - **Summary**: Change subscription to a different tier (usually downgrade).

- **POST** `/api/v1/subscriptions/check-access/{service}`
  - **Function**: `check_service_access`
  - **Summary**: Check if user has access to specific service
  - **Path Parameters**: service

- **POST** `/api/v1/subscriptions/confirm-upgrade`
  - **Function**: `confirm_upgrade`
  - **Summary**: Confirm upgrade after successful Stripe payment.

- **GET** `/api/v1/subscriptions/current`
  - **Function**: `get_current_subscription`
  - **Summary**: Get current subscription details from Lago.

- **POST** `/api/v1/subscriptions/downgrade`
  - **Function**: `initiate_downgrade`
  - **Summary**: Schedule subscription downgrade at end of current billing period.

- **GET** `/api/v1/subscriptions/my-access`
  - **Function**: `get_my_access`
  - **Summary**: Get services accessible to current user

- **GET** `/api/v1/subscriptions/plans`
  - **Function**: `get_plans`
  - **Summary**: Get all active subscription plans

- **POST** `/api/v1/subscriptions/plans`
  - **Function**: `create_plan`
  - **Summary**: Create new subscription plan (admin only)

- **DELETE** `/api/v1/subscriptions/plans/{plan_id}`
  - **Function**: `delete_plan`
  - **Summary**: Delete (deactivate) subscription plan (admin only)
  - **Path Parameters**: plan_id

- **GET** `/api/v1/subscriptions/plans/{plan_id}`
  - **Function**: `get_plan`
  - **Summary**: Get specific plan details
  - **Path Parameters**: plan_id

- **PUT** `/api/v1/subscriptions/plans/{plan_id}`
  - **Function**: `update_plan`
  - **Summary**: Update subscription plan (admin only)
  - **Path Parameters**: plan_id

- **GET** `/api/v1/subscriptions/preview-change`
  - **Function**: `preview_subscription_change`
  - **Summary**: Preview subscription change with proration calculation.

- **GET** `/api/v1/subscriptions/services`
  - **Function**: `get_all_services`
  - **Summary**: Get all available services (for admin reference)

- **POST** `/api/v1/subscriptions/upgrade`
  - **Function**: `upgrade_subscription`
  - **Summary**: Upgrade subscription to a higher tier.

- **POST** `/api/v1/subscriptions/upgrade`
  - **Function**: `initiate_upgrade`
  - **Summary**: Initiate subscription upgrade flow with Stripe Checkout.


### System-Metrics (9 endpoints)

- **GET** `/api/v1/system/alerts`
  - **Function**: `get_system_alerts`
  - **Summary**: Get active system alerts and warnings.

- **GET** `/api/v1/system/alerts/history`
  - **Function**: `get_alert_history`
  - **Summary**: Get alert history.

- **GET** `/api/v1/system/alerts/summary`
  - **Function**: `get_alert_summary`
  - **Summary**: Get summary of current alerts by severity.

- **POST** `/api/v1/system/alerts/{alert_id}/dismiss`
  - **Function**: `dismiss_alert`
  - **Summary**: Dismiss a system alert.
  - **Path Parameters**: alert_id

- **GET** `/api/v1/system/health-score`
  - **Function**: `get_health_score`
  - **Summary**: Calculate overall system health score (0-100).

- **GET** `/api/v1/system/metrics`
  - **Function**: `get_system_metrics`
  - **Summary**: Get comprehensive system metrics with historical data.

- **GET** `/api/v1/system/processes`
  - **Function**: `get_top_processes`
  - **Summary**: Get top processes by CPU and memory usage.

- **GET** `/api/v1/system/services/status`
  - **Function**: `get_services_status`
  - **Summary**: Get status of all Docker services.

- **GET** `/api/v1/system/temperature`
  - **Function**: `get_system_temperature`
  - **Summary**: Get system temperature sensors.


### Tier-Check (6 endpoints)

- **GET** `/api/v1/check-tier`
  - **Function**: `check_tier_access`
  - **Summary**: Check if user has access to a service based on their subscription tier.

- **GET** `/api/v1/rate-limit/check`
  - **Function**: `check_rate_limit`
  - **Summary**: Check current rate limit status for user.

- **GET** `/api/v1/services/access-matrix`
  - **Function**: `get_access_matrix`
  - **Summary**: Get complete service access matrix for a given tier.

- **GET** `/api/v1/tiers/info`
  - **Function**: `get_tiers_info`
  - **Summary**: Get information about all subscription tiers.

- **POST** `/api/v1/usage/track`
  - **Function**: `track_usage`
  - **Summary**: Track service usage for billing and rate limiting.

- **GET** `/api/v1/user/tier`
  - **Function**: `get_user_tier_info`
  - **Summary**: Get user's subscription tier information.


### Traefik (22 endpoints)

- **GET** `/api/v1/traefik/acme/status`
  - **Function**: `get_acme_status`
  - **Summary**: Get ACME (Let's Encrypt) status

- **GET** `/api/v1/traefik/certificates`
  - **Function**: `list_certificates`
  - **Summary**: List all SSL certificates

- **GET** `/api/v1/traefik/certificates/{domain}`
  - **Function**: `get_certificate`
  - **Summary**: Get SSL certificate information for a domain
  - **Path Parameters**: domain

- **POST** `/api/v1/traefik/config/reload`
  - **Function**: `reload_config`
  - **Summary**: Reload Traefik configuration

- **GET** `/api/v1/traefik/config/summary`
  - **Function**: `get_config_summary`
  - **Summary**: Get Traefik configuration summary

- **POST** `/api/v1/traefik/config/validate`
  - **Function**: `validate_config`
  - **Summary**: Validate Traefik configuration

- **GET** `/api/v1/traefik/health`
  - **Function**: `health_check`
  - **Summary**: Health check endpoint for Traefik management API

- **GET** `/api/v1/traefik/middlewares`
  - **Function**: `list_middlewares`
  - **Summary**: List all Traefik middlewares

- **POST** `/api/v1/traefik/middlewares`
  - **Function**: `create_middleware`
  - **Summary**: Create a new Traefik middleware

- **DELETE** `/api/v1/traefik/middlewares/{middleware_name}`
  - **Function**: `delete_middleware`
  - **Summary**: Delete a Traefik middleware
  - **Path Parameters**: middleware_name

- **GET** `/api/v1/traefik/middlewares/{middleware_name}`
  - **Function**: `get_middleware`
  - **Summary**: Get details of a specific middleware
  - **Path Parameters**: middleware_name

- **PUT** `/api/v1/traefik/middlewares/{middleware_name}`
  - **Function**: `update_middleware`
  - **Summary**: Update an existing middleware
  - **Path Parameters**: middleware_name

- **GET** `/api/v1/traefik/routes`
  - **Function**: `list_routes`
  - **Summary**: List all Traefik routes

- **POST** `/api/v1/traefik/routes`
  - **Function**: `create_route`
  - **Summary**: Create a new Traefik route

- **DELETE** `/api/v1/traefik/routes/{route_name}`
  - **Function**: `delete_route`
  - **Summary**: Delete a Traefik route
  - **Path Parameters**: route_name

- **GET** `/api/v1/traefik/routes/{route_name}`
  - **Function**: `get_route`
  - **Summary**: Get details of a specific route
  - **Path Parameters**: route_name

- **PUT** `/api/v1/traefik/routes/{route_name}`
  - **Function**: `update_route`
  - **Summary**: Update an existing route
  - **Path Parameters**: route_name

- **GET** `/api/v1/traefik/services`
  - **Function**: `list_services`
  - **Summary**: List all Traefik services

- **POST** `/api/v1/traefik/services`
  - **Function**: `create_service`
  - **Summary**: Create a new Traefik service

- **DELETE** `/api/v1/traefik/services/{service_name}`
  - **Function**: `delete_service`
  - **Summary**: Delete a Traefik service
  - **Path Parameters**: service_name

- **GET** `/api/v1/traefik/services/{service_name}`
  - **Function**: `get_service`
  - **Summary**: Get details of a specific service
  - **Path Parameters**: service_name

- **GET** `/api/v1/traefik/status`
  - **Function**: `get_traefik_status`
  - **Summary**: Get overall Traefik status


### Usage (6 endpoints)

- **GET** `/api/v1/usage/current`
  - **Function**: `get_current_usage_endpoint`
  - **Summary**: Get current usage statistics for the authenticated user.

- **GET** `/api/v1/usage/export`
  - **Function**: `export_usage_data`
  - **Summary**: Export usage data as CSV file.

- **GET** `/api/v1/usage/features`
  - **Function**: `get_tier_features`
  - **Summary**: Get feature access information for current tier.

- **GET** `/api/v1/usage/history`
  - **Function**: `get_usage_history`
  - **Summary**: Get historical usage data.

- **GET** `/api/v1/usage/limits`
  - **Function**: `get_tier_limits`
  - **Summary**: Get tier limits and pricing information.

- **POST** `/api/v1/usage/reset-demo`
  - **Function**: `reset_usage_demo`
  - **Summary**: DEMO/TESTING ONLY: Reset usage counter for current user.


## Statistics

### Endpoints by HTTP Method

- **DELETE**: 28
- **GET**: 158
- **PATCH**: 1
- **POST**: 100
- **PUT**: 23
