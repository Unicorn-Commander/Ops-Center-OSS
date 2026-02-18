# UC-1 Pro Admin Dashboard Documentation

Welcome to the **UC-1 Pro Admin Dashboard** - your central command center for managing the most advanced AI infrastructure platform available. This comprehensive dashboard gives you complete control over your UC-1 Pro system, from AI model management to system monitoring and everything in between.

![UC-1 Pro Dashboard](assets/images/dashboard-overview.png)

## What is UC-1 Pro?

UC-1 Pro is an enterprise-grade AI infrastructure stack designed specifically for NVIDIA RTX 5090 GPUs. It provides a complete AI platform with:

- **High-Performance LLM Inference** with vLLM engine
- **Advanced Speech Processing** with WhisperX
- **Voice Synthesis** with Kokoro TTS
- **Document Intelligence** with OCR capabilities
- **Vector Search** with Qdrant database
- **Private Search** with SearXNG
- **Comprehensive Monitoring** with real-time metrics

## Admin Dashboard Features

The Admin Dashboard provides a unified interface to manage all aspects of your UC-1 Pro system:

### 🏠 **Overview Dashboard**
Real-time system health monitoring, quick actions, and key performance indicators at a glance.

### 🤖 **AI Model Management**
Complete control over LLM models, including installation, configuration, and performance tuning for both vLLM and Ollama engines.

### ⚙️ **Service Management**
Monitor and control all UC-1 Pro services with detailed status information, logs, and configuration options.

### 📊 **System Monitoring**
Real-time charts and metrics for CPU, memory, GPU utilization, temperatures, and network performance.

### 🌐 **Network & WiFi**
Configure network interfaces, manage WiFi connections, and monitor network performance.

### 💾 **Storage & Backup**
Monitor disk usage, configure automated backups, and manage data retention policies.

### 🧩 **Extensions Marketplace**
Discover and install additional functionality through the extensions ecosystem.

### 📋 **Logs & Diagnostics**
Centralized log aggregation with advanced search and filtering capabilities.

### 🔒 **Security & Access**
User management, authentication, API keys, and session monitoring.

### ⚙️ **Settings**
System-wide configuration options and preferences.

## Quick Start

Getting started with the Admin Dashboard is simple:

1. **Access the Dashboard**: Navigate to `http://your-uc1-pro-ip:8084`
2. **Login**: Use your admin credentials (default: `ucadmin` / `MagicUnicorn!8-)`)
3. **Explore**: Use the sidebar navigation to access different management sections
4. **Get Help**: Press `?` at any time for contextual help

## Key Benefits

- **Centralized Management**: Control everything from one intuitive interface
- **Real-time Monitoring**: Live updates on system performance and health
- **Advanced Analytics**: Detailed insights into system usage and performance
- **Secure Access**: Enterprise-grade authentication and access control
- **Extensible Platform**: Add new functionality through the extensions system
- **Mobile Responsive**: Access your dashboard from any device

## Architecture Overview

The Admin Dashboard is built with modern web technologies:

- **Frontend**: React with Tailwind CSS for responsive design
- **Backend**: FastAPI with Python for high-performance APIs
- **Database**: File-based storage for configuration and user data
- **Authentication**: JWT-based secure authentication
- **Real-time Updates**: WebSocket connections for live data

## Support & Documentation

- **Getting Started Guide**: Step-by-step setup instructions
- **Feature Documentation**: Detailed guides for each dashboard section
- **API Reference**: Complete API documentation for developers
- **Troubleshooting**: Common issues and solutions
- **FAQ**: Frequently asked questions

---

## What's Next?

Ready to dive in? Start with our [Quick Start Guide](getting-started/quick-start.md) or explore the [User Interface Overview](getting-started/ui-overview.md) to familiarize yourself with the dashboard layout.

For specific features, jump directly to:
- [AI Model Management](features/ai-models.md) - Manage your language models
- [System Monitoring](features/system-monitoring.md) - Keep an eye on performance
- [Security & Access](features/security.md) - Manage users and permissions

---

*UC-1 Pro Admin Dashboard - Powered by Magic Unicorn Unconventional Technology & Stuff Inc*