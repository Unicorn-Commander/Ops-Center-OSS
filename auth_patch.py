import os
import json
from authlib.integrations.flask_client import OAuth
from authlib.integrations.base_client import OAuthError
from flask import current_app, session, redirect, url_for
from jose import jwt
import requests

class AuthentikOIDCClient:
    def __init__(self, app=None):
        self.app = app
        self.oauth = None
        self.client = None

        if app:
            self.init_app(app)

    def init_app(self, app):
        """Initialize the OIDC client with Flask app"""
        self.app = app

        # Configure OAuth
        self.oauth = OAuth(app)

        # Get configuration from environment
        client_id = os.getenv('OIDC_CLIENT_ID', 'center-deep')
        client_secret = os.getenv('OIDC_CLIENT_SECRET', '')

        # Check if using Keycloak or Authentik
        is_keycloak = os.getenv('KEYCLOAK_ENABLED', 'false').lower() == 'true'
        oauth_provider = os.getenv('OAUTH_PROVIDER', 'authentik').lower()

        if is_keycloak or oauth_provider == 'keycloak':
            # Keycloak configuration
            issuer = os.getenv('OIDC_ISSUER', os.getenv('OAUTH_ISSUER', ''))
            authorize_url = os.getenv('OIDC_AUTHORIZATION_URL', os.getenv('OAUTH_AUTHORIZATION_URL', ''))
            token_url = os.getenv('OIDC_TOKEN_URL', os.getenv('OAUTH_TOKEN_URL', ''))
            userinfo_url = os.getenv('OIDC_USERINFO_URL', os.getenv('OAUTH_USERINFO_URL', ''))
            scope = os.getenv('OAUTH_SCOPE', 'openid profile email')

            # Register Keycloak OIDC client with manual configuration
            self.client = self.oauth.register(
                name='keycloak',
                client_id=client_id,
                client_secret=client_secret,
                authorize_url=authorize_url,
                access_token_url=token_url,
                userinfo_endpoint=userinfo_url,
                client_kwargs={
                    'scope': scope
                }
            )
        else:
            # Authentik configuration (legacy)
            authentik_url = os.getenv('AUTHENTIK_URL', 'http://authentik-server:9000')

            # Override with external URL if explicitly set and internal is not accessible
            if os.getenv('AUTHENTIK_EXTERNAL_URL'):
                try:
                    import socket
                    socket.gethostbyname('authentik-server')
                except:
                    authentik_url = os.getenv('AUTHENTIK_EXTERNAL_URL')

            external_auth_url = os.getenv('AUTHENTIK_EXTERNAL_URL')

            # Register OIDC client
            if external_auth_url:
                self.client = self.oauth.register(
                    name='authentik',
                    client_id=client_id,
                    client_secret=client_secret,
                    authorize_url=f'{external_auth_url}/application/o/authorize/',
                    access_token_url=f'{authentik_url}/application/o/token/',
                    userinfo_endpoint=f'{authentik_url}/application/o/userinfo/',
                    jwks_uri=f'{authentik_url}/application/o/center-deep/jwks/',
                    client_kwargs={
                        'scope': 'openid profile email groups'
                    }
                )
            else:
                # Fallback to auto-discovery
                self.client = self.oauth.register(
                    name='authentik',
                    client_id=client_id,
                    client_secret=client_secret,
                    server_metadata_url=f'{authentik_url}/application/o/center-deep/.well-known/openid-configuration',
                    client_kwargs={
                        'scope': 'openid profile email groups'
                    }
                )

    def create_authorization_url(self, redirect_uri):
        """Generate the authorization URL for SSO login"""
        return self.client.authorize_redirect(redirect_uri)

    def handle_callback(self, request):
        """Handle the OAuth callback and exchange code for token"""
        try:
            token = self.client.authorize_access_token()

            # Get user info from token
            user_info = token.get('userinfo')
            if not user_info:
                # Fetch user info from userinfo endpoint
                resp = self.client.get('userinfo', token=token)
                user_info = resp.json()

            return {
                'success': True,
                'user_info': user_info,
                'token': token
            }
        except OAuthError as e:
            return {
                'success': False,
                'error': str(e)
            }

    def logout(self, token):
        """Logout from OAuth provider"""
        # Try to get end_session_endpoint
        try:
            metadata = self.client.load_server_metadata()
            logout_url = metadata.get('end_session_endpoint')
        except:
            logout_url = None

        if logout_url and token:
            # Redirect to OAuth provider logout
            return redirect(logout_url + '?id_token_hint=' + token.get('id_token'))

        return redirect(url_for('index'))
