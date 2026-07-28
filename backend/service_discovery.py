"""
Service Discovery Module for UC-1 Pro Ops Center

Dynamically discovers and provides service endpoint URLs for all UC-1 Pro services.
Supports multiple deployment scenarios:
- Local development (localhost)
- Docker Compose with internal networking
- Traefik reverse proxy with custom domains
- Remote/distributed deployments

Environment Variables:
    OLLAMA_URL: Ollama service endpoint (default: http://unicorn-ollama:11434)
    OPENWEBUI_URL: Open-WebUI endpoint (default: http://unicorn-open-webui:8080)
    VLLM_URL: vLLM inference endpoint (default: http://unicorn-vllm:8000)
    EMBEDDINGS_URL: Embeddings service endpoint (default: http://unicorn-embeddings:8001)
    RERANKER_URL: Reranker service endpoint (default: http://unicorn-reranker:8002)
    CENTERDEEP_URL: Center-Deep search endpoint (default: http://unicorn-center-deep:8890)
    AUTHENTIK_URL: Authentik SSO endpoint (default: http://authentik-server:9000)
    QDRANT_URL: Qdrant vector database (default: http://unicorn-qdrant:6333)
    POSTGRESQL_URL: PostgreSQL database (default: postgresql://unicorn-postgresql:5432)
    REDIS_URL: Redis cache (default: redis://unicorn-redis:6379)

    EXTERNAL_HOST: External hostname for public access (default: localhost)
    EXTERNAL_PROTOCOL: External protocol http/https (default: http)
"""

import os
import logging
from typing import Dict, Optional
import docker
from docker.errors import DockerException

logger = logging.getLogger(__name__)


class ServiceDiscovery:
    """
    Service discovery system for UC-1 Pro infrastructure.

    Provides dynamic service endpoint resolution with fallbacks:
    1. Environment variables (highest priority)
    2. Docker container inspection
    3. Default internal Docker networking names
    4. Localhost fallbacks (lowest priority)
    """

    def __init__(self):
        self.docker_client = None
        self._init_docker_client()

        # External access configuration
        self.external_host = os.getenv('EXTERNAL_HOST', 'localhost')
        self.external_protocol = os.getenv('EXTERNAL_PROTOCOL', 'http')

        # Default internal service names (Docker Compose networking)
        self.default_services = {
            'ollama': 'unicorn-ollama:11434',
            'openwebui': 'unicorn-open-webui:8080',
            'vllm': 'unicorn-vllm:8000',
            'embeddings': 'unicorn-embeddings:8001',
            'reranker': 'unicorn-reranker:8002',
            'centerdeep': 'unicorn-center-deep:8890',
            'authentik': 'authentik-server:9000',
            'qdrant': 'unicorn-qdrant:6333',
            'postgresql': 'unicorn-postgresql:5432',
            'redis': 'unicorn-redis:6379',
            'ops-center': 'unicorn-ops-center:8084'
        }

        # Localhost fallback ports (for development)
        self.localhost_ports = {
            'ollama': 11434,
            'openwebui': 8080,
            'vllm': 8000,
            'embeddings': 8001,
            'reranker': 8002,
            'centerdeep': 8890,
            'authentik': 9000,
            'qdrant': 6333,
            'postgresql': 5432,
            'redis': 6379,
            'ops-center': 8084
        }

    def _init_docker_client(self):
        """Initialize Docker client for container inspection."""
        try:
            self.docker_client = docker.from_env()
            logger.info("Docker client initialized for service discovery")
        except DockerException as e:
            logger.warning(f"Docker client unavailable: {e}. Using environment/defaults only.")
            self.docker_client = None

    def _get_from_env(self, service: str) -> Optional[str]:
        """Get service URL from environment variable."""
        env_map = {
            'ollama': 'OLLAMA_URL',
            'openwebui': 'OPENWEBUI_URL',
            'vllm': 'VLLM_URL',
            'embeddings': 'EMBEDDINGS_URL',
            'reranker': 'RERANKER_URL',
            'centerdeep': 'CENTERDEEP_URL',
            'authentik': 'AUTHENTIK_URL',
            'qdrant': 'QDRANT_URL',
            'postgresql': 'POSTGRESQL_URL',
            'redis': 'REDIS_URL',
            'ops-center': 'OPS_CENTER_URL'
        }

        env_var = env_map.get(service)
        if env_var:
            return os.getenv(env_var)
        return None

    def _get_from_docker(self, service: str) -> Optional[str]:
        """
        Discover service URL from Docker container inspection.

        Looks for running containers matching service name patterns
        and extracts their network addresses and ports.
        """
        if not self.docker_client:
            return None

        container_patterns = {
            'ollama': ['unicorn-ollama', 'ollama'],
            'openwebui': ['unicorn-open-webui', 'open-webui'],
            'vllm': ['unicorn-vllm', 'vllm'],
            'embeddings': ['unicorn-embeddings', 'embeddings'],
            'reranker': ['unicorn-reranker', 'reranker'],
            'centerdeep': ['unicorn-center-deep', 'center-deep'],
            'authentik': ['authentik-server', 'authentik'],
            'qdrant': ['unicorn-qdrant', 'qdrant'],
            'postgresql': ['unicorn-postgresql', 'postgresql', 'postgres'],
            'redis': ['unicorn-redis', 'redis'],
            'ops-center': ['unicorn-ops-center', 'ops-center']
        }

        patterns = container_patterns.get(service, [service])

        try:
            containers = self.docker_client.containers.list()
            for container in containers:
                container_name = container.name.lower()

                # Check if container matches any pattern
                if any(pattern.lower() in container_name for pattern in patterns):
                    # Get first network
                    networks = container.attrs.get('NetworkSettings', {}).get('Networks', {})
                    if networks:
                        network_name = list(networks.keys())[0]
                        ip_address = networks[network_name].get('IPAddress')

                        # Get exposed ports
                        ports = container.attrs.get('NetworkSettings', {}).get('Ports', {})
                        if ports:
                            # Get first exposed port
                            for port_spec, bindings in ports.items():
                                if '/' in port_spec:
                                    port = port_spec.split('/')[0]
                                    return f"http://{container.name}:{port}"

                        # Fallback to default port
                        default_port = self.localhost_ports.get(service, 8000)
                        return f"http://{container.name}:{default_port}"

        except DockerException as e:
            logger.warning(f"Error inspecting Docker containers: {e}")

        return None

    def _get_default(self, service: str) -> str:
        """Get default internal service URL."""
        service_addr = self.default_services.get(service)
        if service_addr:
            # Handle special cases for database URLs
            if service == 'postgresql':
                user = os.getenv('POSTGRES_USER', 'unicorn')
                password = os.getenv('POSTGRES_PASSWORD', 'password')
                db = os.getenv('POSTGRES_DB', 'unicorn_db')
                return f"postgresql://{user}:{password}@{service_addr}/{db}"
            elif service == 'redis':
                return f"redis://{service_addr}/0"
            else:
                return f"http://{service_addr}"

        # Ultimate fallback: localhost
        port = self.localhost_ports.get(service, 8000)
        return f"http://localhost:{port}"

    def get_service_url(self, service: str) -> str:
        """
        Get service URL with fallback chain.

        Resolution order:
        1. Environment variable (explicit configuration)
        2. Docker container inspection (dynamic discovery)
        3. Default Docker Compose names (standard deployment)
        4. Localhost (development fallback)

        Args:
            service: Service name (e.g., 'ollama', 'vllm', 'openwebui')

        Returns:
            Full service URL (e.g., 'http://unicorn-ollama:11434')
        """
        # 1. Check environment
        url = self._get_from_env(service)
        if url:
            logger.debug(f"Service '{service}' resolved from environment: {url}")
            return url

        # 2. Check Docker
        url = self._get_from_docker(service)
        if url:
            logger.debug(f"Service '{service}' discovered via Docker: {url}")
            return url

        # 3. Use default
        url = self._get_default(service)
        logger.debug(f"Service '{service}' using default: {url}")
        return url

    def get_all_services(self) -> Dict[str, str]:
        """
        Get all service endpoints.

        Returns:
            Dictionary mapping service names to their URLs
        """
        services = {}

        for service_name in self.default_services.keys():
            services[service_name] = self.get_service_url(service_name)

        return services

    def get_external_urls(self) -> Dict[str, str]:
        """
        Get external (public) URLs for services.

        Uses EXTERNAL_HOST and EXTERNAL_PROTOCOL for user-facing URLs.
        Only includes services that should be publicly accessible.

        Returns:
            Dictionary of public service URLs
        """
        base_url = f"{self.external_protocol}://{self.external_host}"

        # Public services with their subdomain/path patterns
        public_services = {
            'openwebui': f"{self.external_protocol}://chat.{self.external_host}",
            'centerdeep': f"{self.external_protocol}://search.{self.external_host}",
            'authentik': f"{self.external_protocol}://auth.{self.external_host}",
            'ops-center': f"{base_url}:8084" if self.external_host == 'localhost' else base_url,
            'vllm': f"{base_url}:8000",
            'ollama': f"{base_url}:11434"
        }

        return public_services

    def get_service_info(self) -> Dict[str, Dict[str, str]]:
        """
        Get comprehensive service information.

        Returns:
            Dictionary with both internal and external URLs for each service
        """
        internal = self.get_all_services()
        external = self.get_external_urls()

        info = {}
        for service in self.default_services.keys():
            info[service] = {
                'internal': internal.get(service, ''),
                'external': external.get(service, ''),
                'status': 'available' if internal.get(service) else 'unavailable'
            }

        return info

    def health_check(self, service: str) -> bool:
        """
        Check if a service is reachable.

        Args:
            service: Service name to check

        Returns:
            True if service is reachable, False otherwise
        """
        if not self.docker_client:
            return False

        try:
            containers = self.docker_client.containers.list()
            for container in containers:
                if service in container.name.lower():
                    return container.status == 'running'
        except DockerException as e:
            logger.error(f"Error checking service health: {e}")

        return False


# Global instance
service_discovery = ServiceDiscovery()


def get_service_url(service: str) -> str:
    """Convenience function to get service URL."""
    return service_discovery.get_service_url(service)


def get_all_service_urls() -> Dict[str, str]:
    """Convenience function to get all service URLs."""
    return service_discovery.get_all_services()
